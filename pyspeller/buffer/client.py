"""Client side of the buffer: the API every other component uses."""
import socket
import struct
import time

import numpy as np

from . import protocol as P
from .protocol import Event, Header, ProtocolError


class BufferClient:
    """Connection to a buffer server, plus the event helpers clients need."""

    def __init__(self, host='localhost', port=1972, timeout=None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock = None
        self.header = None
        self._event_cursor = 0   # next event index this client has not seen
        self._pending = []       # read from the buffer but not yet handed out

    # -- connection --------------------------------------------------------
    def connect(self, retries=0, retry_delay=0.5):
        last = None
        for attempt in range(retries + 1):
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(self.timeout)
                self.sock.connect((self.host, self.port))
                self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                return self
            except OSError as err:
                last = err
                self.sock = None
                if attempt < retries:
                    time.sleep(retry_delay)
        raise ConnectionError('could not connect to buffer at %s:%d (%s)'
                              % (self.host, self.port, last))

    def disconnect(self):
        if self.sock is not None:
            try:
                self.sock.close()
            finally:
                self.sock = None

    def __enter__(self):
        return self.connect() if self.sock is None else self

    def __exit__(self, *exc):
        self.disconnect()

    # -- raw request/response ---------------------------------------------
    def _request(self, command, payload=b''):
        if self.sock is None:
            raise ConnectionError('not connected to a buffer')
        self.sock.sendall(P.pack_message(command, payload))
        raw = P.recv_exactly(self.sock, P.HEADER_SIZE)
        _, response, size, _ = P.unpack_message_header(raw, endian='<')
        body = P.recv_exactly(self.sock, size) if size else b''
        return response, body

    # -- header ------------------------------------------------------------
    def put_header(self, nchannels, fsample, data_type=P.DATATYPE_FLOAT32,
                   labels=None):
        hdr = Header(nchannels, fsample, data_type, labels)
        status, _ = self._request(P.PUT_HDR, hdr.serialize())
        if status != P.PUT_OK:
            raise ProtocolError('the buffer rejected the header')
        self.header = hdr
        return hdr

    def get_header(self):
        status, body = self._request(P.GET_HDR)
        if status != P.GET_OK:
            return None
        self.header = Header.deserialize(body)
        return self.header

    def wait_for_header(self, timeout=10.0, poll=0.2):
        """Block until an acquisition client has described the dataset."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            hdr = self.get_header()
            if hdr is not None and hdr.nchannels > 0:
                self._event_cursor = hdr.nevents
                return hdr
            time.sleep(poll)
        raise TimeoutError('no header appeared in the buffer within %gs' % timeout)

    # -- data --------------------------------------------------------------
    def put_data(self, samples):
        """Append samples, given as [nsamples x nchannels]."""
        status, _ = self._request(P.PUT_DAT, P.serialize_data(samples))
        if status != P.PUT_OK:
            raise ProtocolError('the buffer rejected the samples')

    def get_data(self, start=None, end=None):
        """Samples [start..end] inclusive as [nsamples x nchannels]."""
        payload = b'' if start is None else struct.pack('<II', int(start), int(end))
        status, body = self._request(P.GET_DAT, payload)
        if status != P.GET_OK:
            raise ProtocolError('the buffer could not return samples %s-%s'
                                % (start, end))
        return P.deserialize_data(body)

    # -- events ------------------------------------------------------------
    def put_events(self, events):
        if isinstance(events, Event):
            events = [events]
        body = b''.join(e.serialize() for e in events)
        status, _ = self._request(P.PUT_EVT, body)
        if status != P.PUT_OK:
            raise ProtocolError('the buffer rejected the events')

    def send_event(self, type, value='', sample=-1, duration=0, offset=0):
        """Send one event; sample=-1 means 'stamp it with the current sample'."""
        evt = Event(type, value, sample, offset, duration)
        self.put_events([evt])
        return evt

    def get_events(self, start=None, end=None):
        payload = b'' if start is None else struct.pack('<II', int(start), int(end))
        status, body = self._request(P.GET_EVT, payload)
        if status != P.GET_OK:
            raise ProtocolError('the buffer could not return events %s-%s'
                                % (start, end))
        return P.Event.deserialize_many(body)

    def poll(self):
        """(nsamples, nevents) currently in the buffer."""
        return self.wait(0xFFFFFFFF, 0xFFFFFFFF, 0)

    def wait(self, nsamples, nevents, timeout_ms):
        """Block until nsamples/nevents are exceeded; returns the new counts."""
        payload = struct.pack('<III', int(nsamples) & 0xFFFFFFFF,
                              int(nevents) & 0xFFFFFFFF, int(timeout_ms))
        status, body = self._request(P.WAIT_DAT, payload)
        if status != P.WAIT_OK or len(body) < 8:
            raise ProtocolError('wait request failed')
        return struct.unpack('<II', body[:8])

    # -- event stream ------------------------------------------------------
    def reset_event_cursor(self, index=None):
        """Forget past events; new events are those after `index` (default: now)."""
        if index is None:
            index = self.poll()[1]
        self._event_cursor = int(index)
        self._pending = []
        return self._event_cursor

    @property
    def event_cursor(self):
        return self._event_cursor

    def new_events(self, timeout_ms=0):
        """Events written since the last call, advancing the cursor."""
        if self._pending:
            # events a previous wait_for_event() read but did not hand out
            pending, self._pending = self._pending, []
            return pending
        _, nevents = self.wait(0xFFFFFFFF, self._event_cursor, timeout_ms)
        if nevents <= self._event_cursor:
            return []
        try:
            events = self.get_events(self._event_cursor, nevents - 1)
        except ProtocolError:      # cursor fell out of the (bounded) event ring
            events = self.get_events()
        self._event_cursor = nevents
        return events

    def wait_for_event(self, types, timeout=None, values=None):
        """Next event whose type (and optionally value) matches, or None."""
        types = [types] if isinstance(types, str) else list(types)
        values = [values] if isinstance(values, str) else values
        deadline = None if timeout is None else time.time() + timeout
        while True:
            remaining = 1000 if deadline is None else max(
                0, int((deadline - time.time()) * 1000))
            events = self.new_events(timeout_ms=remaining)
            for index, evt in enumerate(events):
                if evt.type in types and (values is None or evt.value in values):
                    # keep the rest of the batch: the caller asked for one event,
                    # not for the others to be thrown away
                    self._pending = events[index + 1:] + self._pending
                    return evt
            if deadline is not None and time.time() >= deadline:
                return None

    # -- convenience -------------------------------------------------------
    @property
    def fsample(self):
        if self.header is None:
            self.get_header()
        return self.header.fsample

    def samples_for(self, milliseconds):
        return int(round(milliseconds * self.fsample / 1000.0))

    def data_since(self, start_sample):
        """All samples from `start_sample` onwards (empty array if none yet)."""
        nsamples = self.poll()[0]
        if nsamples <= start_sample:
            return np.zeros((0, self.header.nchannels))
        return self.get_data(start_sample, nsamples - 1)
