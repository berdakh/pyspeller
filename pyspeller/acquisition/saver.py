"""Save everything that passes through the buffer to disk.

The files are written in the FieldTrip offline-buffer layout that the rest of
buffer_bci already reads and replays:

    <session>/header       binary header (channels, rate, sample type, labels)
    <session>/header.txt   the same in ascii, one key=value per line
    <session>/samples      raw samples, channels fastest, in the header's type
    <session>/events       events in the buffer's own wire format

so a recording made here can be loaded with matlab/offline/read_buffer_offline_*
or replayed into a buffer with matlab/dataAcq/buffer_fileproxy.m, and read back
in python with load_session() below.

If samples are overwritten in the buffer's ring before the saver gets to them
(a stall, a slow disk), the gap is filled with zeros and recorded in `gaps`, so
that the sample indices stored in the events keep pointing at the right place.
"""
import json
import os
import sys
import time

import numpy as np

from ..buffer.client import BufferClient
from ..buffer.protocol import NUMPY_TYPE, Event, Header, ProtocolError


def session_directory(root='~/output', experiment='pyspeller', subject='test',
                      name='raw_buffer', now=None):
    """The buffer_bci save path: <root>/<experiment>/<subject>/<date>/<time>/."""
    stamp = time.strftime('%y%m%d/%H%M', time.localtime(now or time.time()))
    return os.path.join(os.path.expanduser(root), experiment, subject, stamp, name)


class BufferSaver:
    """A buffer client that copies samples and events onto disk as they arrive."""

    def __init__(self, host='localhost', port=1972, directory=None, root='~/output',
                 experiment='pyspeller', subject='test', verbose=True):
        self.host = host
        self.port = port
        self.directory = directory or session_directory(root, experiment, subject)
        self.verbose = verbose
        self.client = None
        self.header = None
        self.nsamples = 0            # samples written to disk
        self.nevents = 0             # events written to disk
        self.gaps = []               # [(sample, n_missing)] filled with zeros
        self._samples_file = None
        self._events_file = None
        self._thread = None
        self._running = False

    # -- setup -------------------------------------------------------------
    def connect(self, timeout=60.0):
        self.client = BufferClient(self.host, self.port).connect(retries=20)
        self.header = self.client.wait_for_header(timeout=timeout)
        os.makedirs(self.directory, exist_ok=True)
        self._samples_file = open(os.path.join(self.directory, 'samples'), 'wb')
        self._events_file = open(os.path.join(self.directory, 'events'), 'wb')
        self.client.reset_event_cursor(0)
        self._cursor = 0
        self._write_header()
        if self.verbose:
            print('saving %d channels at %g Hz to %s'
                  % (self.header.nchannels, self.header.fsample, self.directory),
                  flush=True)
        return self

    def _write_header(self):
        header = Header(self.header.nchannels, self.header.fsample,
                        self.header.data_type, self.header.labels,
                        nsamples=self.nsamples, nevents=self.nevents)
        with open(os.path.join(self.directory, 'header'), 'wb') as fh:
            fh.write(header.serialize())
        lines = ['fSample=%g' % header.fsample,
                 'nChans=%d' % header.nchannels,
                 'nSamples=%d' % self.nsamples,
                 'nEvents=%d' % self.nevents,
                 'dataType=%s' % NUMPY_TYPE[header.data_type],
                 'version=1',
                 'endian=%s' % ('little' if sys.byteorder == 'little' else 'big')]
        lines += ['%d:%s' % (i + 1, label)
                  for i, label in enumerate(header.labels or [])]
        with open(os.path.join(self.directory, 'header.txt'), 'w') as fh:
            fh.write('\n'.join(lines) + '\n')

    # -- streaming ---------------------------------------------------------
    def pump(self, timeout_ms=500):
        """Copy whatever is new across; returns (new_samples, new_events)."""
        nsamples, nevents = self.client.wait(self.nsamples, self._cursor, timeout_ms)
        written = self._save_samples(nsamples)
        saved = self._save_events(nevents)
        if written or saved:
            self._write_header()
        return written, saved

    def _save_samples(self, nsamples):
        if nsamples <= self.nsamples:
            if nsamples < self.nsamples:        # the buffer was flushed under us
                self._note('the buffer restarted; keeping the samples saved so far')
                self.nsamples = nsamples
            return 0
        start = self.nsamples
        try:
            data = self.client.get_data(start, nsamples - 1)
        except ProtocolError:
            start = self._oldest_available(nsamples)
            missing = start - self.nsamples
            self._note('lost %d samples at %d (the buffer wrapped); padding with zeros'
                       % (missing, self.nsamples))
            self.gaps.append((self.nsamples, missing))
            self._samples_file.write(
                np.zeros((missing, self.header.nchannels),
                         dtype=self.header.dtype).tobytes())
            self.nsamples = start
            data = self.client.get_data(start, nsamples - 1)
        self._samples_file.write(data.astype(self.header.dtype, copy=False).tobytes())
        self._samples_file.flush()
        self.nsamples = nsamples
        return nsamples - start

    def _oldest_available(self, nsamples):
        """Find the oldest sample the buffer still holds, by probing backwards."""
        oldest, step = nsamples - 1, 1
        while step < nsamples:
            candidate = nsamples - step
            try:
                self.client.get_data(candidate, candidate)
            except ProtocolError:
                break
            oldest = candidate
            step *= 2
        return oldest

    def _save_events(self, nevents):
        if nevents <= self._cursor:
            if nevents < self._cursor:
                self._cursor = nevents
            return 0
        try:
            events = self.client.get_events(self._cursor, nevents - 1)
        except ProtocolError:                   # the event ring wrapped
            events = self.client.get_events()
            self._note('lost events: the buffer kept only the last %d' % len(events))
        for event in events:
            self._events_file.write(event.serialize())
        self._events_file.flush()
        self._cursor = nevents
        self.nevents += len(events)
        return len(events)

    def _note(self, message):
        if self.verbose:
            print('[saver] %s' % message, flush=True)

    # -- lifecycle ---------------------------------------------------------
    def start(self):
        if self.client is None:
            self.connect()
        self._running = True
        import threading
        self._thread = threading.Thread(target=self.run, name='buffer-saver',
                                        daemon=True)
        self._thread.start()
        return self

    def run(self):
        while self._running:
            self.pump()

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=5.0)
        self.close()

    def close(self):
        """Flush the last samples and events and write the final header."""
        if self.client is None:
            return self.directory
        try:
            self.pump(timeout_ms=0)
        except (OSError, ProtocolError):
            pass
        for handle in (self._samples_file, self._events_file):
            if handle is not None and not handle.closed:
                handle.close()
        self._write_header()
        self.client.disconnect()
        self.client = None
        if self.verbose:
            print('saved %d samples and %d events to %s'
                  % (self.nsamples, self.nevents, self.directory), flush=True)
        return self.directory

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()


# -- reading a recording back ---------------------------------------------
def load_session(directory):
    """Read a saved session: (header, data [nsamples x nchannels], events)."""
    directory = os.path.expanduser(directory)
    with open(os.path.join(directory, 'header'), 'rb') as fh:
        header = Header.deserialize(fh.read())
    data = np.fromfile(os.path.join(directory, 'samples'), dtype=header.dtype)
    if header.nchannels:
        data = data.reshape(-1, header.nchannels)
    with open(os.path.join(directory, 'events'), 'rb') as fh:
        events = Event.deserialize_many(fh.read())
    return header, data, events


def save_epochs(path, epochs, labels, events=None, metadata=None):
    """Store cut epochs (and their events) as a single .npz for offline work."""
    path = os.path.expanduser(path)
    os.makedirs(os.path.dirname(os.path.abspath(path)) or '.', exist_ok=True)
    payload = {'epochs': np.asarray(epochs), 'labels': np.asarray(labels)}
    if events is not None:
        payload['event_types'] = np.array([e.type for e in events])
        payload['event_values'] = np.array([str(e.value) for e in events])
        payload['event_samples'] = np.array([e.sample for e in events])
    if metadata:
        payload['metadata'] = np.array(json.dumps(metadata))
    np.savez_compressed(path, **payload)
    return path


def load_epochs(path):
    """The counterpart of save_epochs: (epochs, labels, metadata dict)."""
    with np.load(os.path.expanduser(path), allow_pickle=False) as data:
        metadata = (json.loads(str(data['metadata'])) if 'metadata' in data else {})
        return data['epochs'], data['labels'], metadata


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(
        description='save the contents of a buffer to disk as it arrives')
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', type=int, default=1972)
    parser.add_argument('--dir', default=None,
                        help='where to write (default: a timestamped session '
                             'directory under --root)')
    parser.add_argument('--root', default='~/output')
    parser.add_argument('--experiment', default='pyspeller')
    parser.add_argument('--subject', default='test')
    args = parser.parse_args(argv)
    saver = BufferSaver(args.host, args.port, args.dir, args.root,
                        args.experiment, args.subject).connect()
    try:
        saver._running = True
        saver.run()
    except KeyboardInterrupt:
        print('\nstopping')
    finally:
        saver.close()


if __name__ == '__main__':
    main()
