"""A pure-python FieldTrip buffer server.

The buffer is the hub of the framework: acquisition clients put samples and
events into it, application clients get them out.  Samples live in a ring
buffer, events in a bounded deque, and both are indexed by a monotonically
increasing counter so clients can ask for "everything after index N".
"""
import socket
import threading

import numpy as np

from . import protocol as P
from .protocol import Event, Header, ProtocolError


class _Store:
    """Header + sample ring + event ring, guarded by one condition variable."""

    def __init__(self, max_samples=100000, max_events=10000):
        self.max_samples = int(max_samples)
        self.max_events = int(max_events)
        self.cond = threading.Condition()
        self.reset()

    def reset(self):
        self.header = None
        self.data = None          # [max_samples x nchannels] ring
        self.nsamples = 0         # total samples ever written
        self.events = []          # bounded list of (index, Event)
        self.nevents = 0          # total events ever written

    # -- writers -----------------------------------------------------------
    def put_header(self, header):
        with self.cond:
            self.header = header
            self.data = np.zeros((self.max_samples, header.nchannels),
                                 dtype=header.dtype)
            self.nsamples = 0
            self.events = []
            self.nevents = 0
            self.cond.notify_all()

    def put_data(self, samples):
        with self.cond:
            if self.header is None:
                raise ProtocolError('no header in the buffer')
            if samples.shape[1] != self.header.nchannels:
                raise ProtocolError('data has %d channels, header says %d'
                                    % (samples.shape[1], self.header.nchannels))
            samples = samples.astype(self.header.dtype, copy=False)
            if samples.shape[0] > self.max_samples:      # keep only the tail
                samples = samples[-self.max_samples:]
            start = self.nsamples % self.max_samples
            first = min(samples.shape[0], self.max_samples - start)
            self.data[start:start + first] = samples[:first]
            if first < samples.shape[0]:                 # wrapped around
                self.data[:samples.shape[0] - first] = samples[first:]
            self.nsamples += samples.shape[0]
            self.cond.notify_all()

    def put_events(self, events):
        with self.cond:
            for evt in events:
                if evt.sample < 0:       # stamp with "now", like the C server
                    evt.sample = self.nsamples
                self.events.append((self.nevents, evt))
                self.nevents += 1
            if len(self.events) > self.max_events:
                self.events = self.events[-self.max_events:]
            self.cond.notify_all()

    # -- readers -----------------------------------------------------------
    def get_header(self):
        with self.cond:
            if self.header is None:
                return None
            hdr = Header(self.header.nchannels, self.header.fsample,
                         self.header.data_type, self.header.labels,
                         self.nsamples, self.nevents)
            return hdr

    def get_data(self, start=None, end=None):
        with self.cond:
            if self.header is None:
                raise ProtocolError('no header in the buffer')
            oldest = max(0, self.nsamples - self.max_samples)
            if start is None:
                start, end = oldest, self.nsamples - 1
            if end < start:
                raise ProtocolError('end sample before start sample')
            if start < oldest or end >= self.nsamples:
                raise ProtocolError('requested samples %d-%d, buffer holds %d-%d'
                                    % (start, end, oldest, self.nsamples - 1))
            idx = np.arange(start, end + 1) % self.max_samples
            return self.data[idx].copy()

    def get_events(self, start=None, end=None):
        with self.cond:
            if start is None:
                return [e for _, e in self.events]
            if end < start:
                return []
            oldest = self.events[0][0] if self.events else self.nevents
            if start < oldest or end >= self.nevents:
                raise ProtocolError('requested events %d-%d, buffer holds %d-%d'
                                    % (start, end, oldest, self.nevents - 1))
            return [e for i, e in self.events if start <= i <= end]

    def wait(self, nsamples, nevents, timeout_ms):
        """Block until the counters exceed the given thresholds, or timeout."""
        deadline_reached = False
        with self.cond:
            def ready():
                return self.nsamples > nsamples or self.nevents > nevents
            if not ready():
                deadline_reached = not self.cond.wait_for(
                    ready, timeout=max(0.0, timeout_ms / 1000.0))
            return self.nsamples, self.nevents, deadline_reached

    def flush(self, what):
        with self.cond:
            if what == 'header':
                self.reset()
            elif what == 'data':
                self.nsamples = 0
            elif what == 'events':
                self.events, self.nevents = [], 0
            self.cond.notify_all()


class BufferServer:
    """Threaded TCP server speaking the FieldTrip buffer protocol."""

    def __init__(self, host='localhost', port=1972, max_samples=100000,
                 max_events=10000):
        self.store = _Store(max_samples, max_events)
        self.host = host
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((host, port))
        self._sock.listen(16)
        self._sock.settimeout(0.2)      # so stop() does not wait on accept()
        self.port = self._sock.getsockname()[1]   # resolves port=0
        self._running = False
        self._threads = []
        self._accept_thread = None

    # -- lifecycle ---------------------------------------------------------
    def start(self):
        """Start accepting clients in a background thread."""
        self._running = True
        self._accept_thread = threading.Thread(target=self._accept_loop,
                                               name='buffer-accept', daemon=True)
        self._accept_thread.start()
        return self

    def stop(self):
        self._running = False
        try:
            self._sock.close()
        except OSError:
            pass
        if self._accept_thread is not None:
            self._accept_thread.join(timeout=2.0)

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()

    def _accept_loop(self):
        while self._running:
            try:
                conn, _ = self._sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            conn.settimeout(None)
            thread = threading.Thread(target=self._serve_client, args=(conn,),
                                      name='buffer-client', daemon=True)
            thread.start()
            self._threads.append(thread)

    # -- per client --------------------------------------------------------
    def _serve_client(self, conn):
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        try:
            while self._running:
                try:
                    raw = P.recv_exactly(conn, P.HEADER_SIZE)
                except ProtocolError:
                    break
                _, command, size, endian = P.unpack_message_header(raw)
                payload = P.recv_exactly(conn, size) if size else b''
                response = self._handle(command, payload, endian)
                conn.sendall(response)
        except (OSError, ProtocolError):
            pass
        finally:
            try:
                conn.close()
            except OSError:
                pass

    def _handle(self, command, payload, endian):
        try:
            return self._dispatch(command, payload, endian)
        except ProtocolError:
            return P.pack_message(_error_for(command), b'', endian)

    def _dispatch(self, command, payload, endian):
        store = self.store
        if command == P.PUT_HDR:
            store.put_header(Header.deserialize(payload, endian))
            return P.pack_message(P.PUT_OK, b'', endian)

        if command == P.PUT_DAT:
            store.put_data(P.deserialize_data(payload, endian))
            return P.pack_message(P.PUT_OK, b'', endian)

        if command == P.PUT_EVT:
            store.put_events(Event.deserialize_many(payload, endian))
            return P.pack_message(P.PUT_OK, b'', endian)

        if command == P.GET_HDR:
            hdr = store.get_header()
            if hdr is None:
                return P.pack_message(P.GET_ERR, b'', endian)
            return P.pack_message(P.GET_OK, hdr.serialize(endian), endian)

        if command == P.GET_DAT:
            start, end = _index_range(payload, endian)
            data = store.get_data(start, end)
            return P.pack_message(P.GET_OK, P.serialize_data(data, endian), endian)

        if command == P.GET_EVT:
            start, end = _index_range(payload, endian)
            events = store.get_events(start, end)
            body = b''.join(e.serialize(endian) for e in events)
            return P.pack_message(P.GET_OK, body, endian)

        if command == P.WAIT_DAT:
            if len(payload) < 12:
                raise ProtocolError('short wait request')
            import struct
            nsamples, nevents, timeout = struct.unpack(endian + 'III', payload[:12])
            got_samples, got_events, _ = store.wait(nsamples, nevents, timeout)
            return P.pack_message(
                P.WAIT_OK, struct.pack(endian + 'II', got_samples, got_events), endian)

        if command in (P.FLUSH_HDR, P.FLUSH_DAT, P.FLUSH_EVT):
            store.flush({P.FLUSH_HDR: 'header', P.FLUSH_DAT: 'data',
                         P.FLUSH_EVT: 'events'}[command])
            return P.pack_message(P.FLUSH_OK, b'', endian)

        raise ProtocolError('unknown command 0x%x' % command)


def _index_range(payload, endian):
    """(start, end) of a get request, or (None, None) for 'everything'."""
    if len(payload) < 8:
        return None, None
    import struct
    start, end = struct.unpack(endian + 'II', payload[:8])
    return start, end


def _error_for(command):
    if command in (P.PUT_HDR, P.PUT_DAT, P.PUT_EVT):
        return P.PUT_ERR
    if command == P.WAIT_DAT:
        return P.WAIT_ERR
    if command in (P.FLUSH_HDR, P.FLUSH_DAT, P.FLUSH_EVT):
        return P.FLUSH_ERR
    return P.GET_ERR


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description='pure-python fieldtrip buffer server')
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', type=int, default=1972)
    parser.add_argument('--max-samples', type=int, default=100000)
    args = parser.parse_args(argv)
    server = BufferServer(args.host, args.port, max_samples=args.max_samples).start()
    print('buffer server listening on %s:%d' % (server.host, server.port), flush=True)
    try:
        while True:
            server._accept_thread.join(1.0)
    except KeyboardInterrupt:
        print('\nshutting down')
    finally:
        server.stop()


if __name__ == '__main__':
    main()
