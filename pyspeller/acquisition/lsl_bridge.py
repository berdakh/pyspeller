"""Lab Streaming Layer -> buffer bridge, for real amplifiers such as g.tec.

g.tec devices (g.USBamp, g.HIamp, g.Nautilus) publish an LSL stream through
g.NEEDaccess / the gtec LSL connector.  This client resolves that stream, pulls
chunks from it and puts them into the buffer, so everything downstream (the
speller, the signal processing, the GUI) is unchanged whether the samples come
from the simulator or from the amplifier.

A marker stream, if present, is forwarded as buffer events with the sample
index the markers line up with, using the LSL timestamps for alignment.

Requires pylsl (`pip install pylsl`), which ships liblsl.
"""
import threading
import time

import numpy as np

from ..buffer.client import BufferClient


def _import_pylsl():
    try:
        import pylsl
    except ImportError as err:      # pragma: no cover - depends on the install
        raise ImportError(
            'pylsl is required to talk to an LSL device. Install it with '
            '"pip install pylsl" (it bundles liblsl).') from err
    return pylsl


def list_streams(timeout=2.0):
    """Every LSL stream currently on the network, as info dictionaries."""
    pylsl = _import_pylsl()
    streams = pylsl.resolve_streams(wait_time=timeout)
    return [{'name': s.name(), 'type': s.type(), 'channels': s.channel_count(),
             'fsample': s.nominal_srate(), 'source_id': s.source_id(),
             'format': s.channel_format(), 'hostname': s.hostname()}
            for s in streams]


def resolve_stream(name=None, stream_type='EEG', timeout=5.0):
    """Find one LSL stream by name and/or type, or raise."""
    pylsl = _import_pylsl()
    candidates = pylsl.resolve_streams(wait_time=timeout)
    matches = [s for s in candidates
               if (name is None or s.name() == name)
               and (stream_type is None or s.type() == stream_type)]
    if not matches:
        available = ', '.join('%s (%s)' % (s.name(), s.type()) for s in candidates)
        raise RuntimeError('no LSL stream matching name=%r type=%r. Available: %s'
                           % (name, stream_type, available or 'none'))
    if len(matches) > 1:
        names = ', '.join(s.name() for s in matches)
        raise RuntimeError('several LSL streams match (%s); pass --name' % names)
    return matches[0]


def channel_labels(info):
    """Channel names from the stream's XML description, with a fallback."""
    labels = []
    try:
        channels = info.desc().child('channels').child('channel')
        while not channels.empty():
            label = channels.child_value('label') or channels.child_value('name')
            labels.append(label or 'ch%d' % (len(labels) + 1))
            channels = channels.next_sibling()
    except Exception:                       # malformed desc: fall back to indices
        labels = []
    if len(labels) != info.channel_count():
        labels = ['ch%d' % (i + 1) for i in range(info.channel_count())]
    return labels


class LSLBridge:
    """Streams one LSL data stream (and optionally markers) into the buffer."""

    def __init__(self, host='localhost', port=1972, name=None, stream_type='EEG',
                 marker_type='Markers', marker_name=None, chunk_seconds=0.05,
                 max_buflen=30, verbose=True):
        self.host = host
        self.port = port
        self.name = name
        self.stream_type = stream_type
        self.marker_type = marker_type
        self.marker_name = marker_name
        self.chunk_seconds = float(chunk_seconds)
        self.max_buflen = int(max_buflen)
        self.verbose = verbose
        self.client = None
        self.inlet = None
        self.marker_inlet = None
        self.fsample = None
        self.labels = []
        self.nsamples = 0
        self._last_timestamp = None
        self._thread = None
        self._running = False

    # -- setup -------------------------------------------------------------
    def connect(self, timeout=5.0):
        pylsl = _import_pylsl()
        info = resolve_stream(self.name, self.stream_type, timeout)
        self.inlet = pylsl.StreamInlet(info, max_buflen=self.max_buflen,
                                       processing_flags=pylsl.proc_clocksync)
        full_info = self.inlet.info()
        self.labels = channel_labels(full_info)
        self.fsample = full_info.nominal_srate()
        if self.fsample <= 0:
            raise RuntimeError('stream %r has no nominal sample rate; the buffer '
                               'needs a regularly sampled stream' % full_info.name())
        self.marker_inlet = self._resolve_markers(pylsl, timeout=0.5)

        self.client = BufferClient(self.host, self.port).connect(retries=20)
        self.client.put_header(len(self.labels), self.fsample, labels=self.labels)
        self.client.reset_event_cursor()
        if self.verbose:
            print('bridging LSL stream %r (%d channels @ %g Hz) into buffer %s:%d'
                  % (full_info.name(), len(self.labels), self.fsample,
                     self.host, self.port), flush=True)
        return self

    def _resolve_markers(self, pylsl, timeout):
        if not (self.marker_type or self.marker_name):
            return None
        try:
            info = resolve_stream(self.marker_name, self.marker_type, timeout)
        except RuntimeError:
            return None
        if self.verbose:
            print('forwarding markers from %r' % info.name(), flush=True)
        return pylsl.StreamInlet(info, processing_flags=pylsl.proc_clocksync)

    # -- streaming ---------------------------------------------------------
    def start(self):
        if self.inlet is None:
            self.connect()
        self._running = True
        self._thread = threading.Thread(target=self.run, name='lsl-bridge', daemon=True)
        self._thread.start()
        return self

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=5.0)
        if self.client is not None:
            self.client.disconnect()

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()

    def run(self):
        while self._running:
            if not self.pump():
                time.sleep(self.chunk_seconds / 4.0)

    def pump(self, timeout=None):
        """Move one chunk of samples (and any markers) across. True if data moved."""
        timeout = self.chunk_seconds if timeout is None else timeout
        samples, timestamps = self.inlet.pull_chunk(timeout=timeout)
        moved = False
        if samples:
            data = np.asarray(samples, dtype='float32')
            self.client.put_data(data)
            self.nsamples += data.shape[0]
            self._last_timestamp = timestamps[-1]
            moved = True
        self._forward_markers()
        return moved

    def _forward_markers(self):
        if self.marker_inlet is None:
            return
        while True:
            marker, timestamp = self.marker_inlet.pull_sample(timeout=0.0)
            if marker is None:
                break
            value = marker[0] if isinstance(marker, (list, tuple)) else marker
            self.client.send_event('lsl.marker', str(value),
                                   sample=self._sample_for(timestamp))

    def _sample_for(self, timestamp):
        """Sample index a marker timestamp corresponds to (-1 = 'now')."""
        if self._last_timestamp is None or not self.fsample:
            return -1
        offset = int(round((timestamp - self._last_timestamp) * self.fsample))
        return max(0, self.nsamples - 1 + offset)


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(
        description='stream an LSL device (e.g. a g.tec amplifier) into the buffer')
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', type=int, default=1972)
    parser.add_argument('--name', default=None, help='LSL stream name')
    parser.add_argument('--type', dest='stream_type', default='EEG',
                        help='LSL stream type (default: EEG)')
    parser.add_argument('--marker-type', default='Markers',
                        help='marker stream type to forward as events ("" for none)')
    parser.add_argument('--list', action='store_true',
                        help='list the LSL streams on the network and exit')
    args = parser.parse_args(argv)

    if args.list:
        found = list_streams()
        if not found:
            print('no LSL streams found')
        for stream in found:
            print('%-24s type=%-10s channels=%-4d rate=%g Hz  host=%s'
                  % (stream['name'], stream['type'], stream['channels'],
                     stream['fsample'], stream['hostname']))
        return

    bridge = LSLBridge(args.host, args.port, args.name, args.stream_type,
                       args.marker_type or None).connect()
    try:
        bridge._running = True
        bridge.run()
    except KeyboardInterrupt:
        print('\nstopping bridge')
    finally:
        bridge.stop()


if __name__ == '__main__':
    main()
