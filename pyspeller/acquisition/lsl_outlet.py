"""Publish buffer data as an LSL stream -- useful to test the LSL path.

With no g.tec amplifier at hand this plays the role of the device: it takes the
simulator's samples out of the buffer and pushes them onto the network as an
LSL stream, which lsl_bridge.py can then consume exactly as it would the real
g.NEEDaccess stream.
"""
import time

import numpy as np

from ..buffer.client import BufferClient
from .lsl_bridge import _import_pylsl


class LSLOutlet:
    """Replays a buffer's samples onto an LSL outlet."""

    def __init__(self, host='localhost', port=1972, name='pyspeller-sim',
                 stream_type='EEG', source_id='pyspeller-sim'):
        pylsl = _import_pylsl()
        self.pylsl = pylsl
        self.client = BufferClient(host, port).connect(retries=20)
        header = self.client.wait_for_header()
        info = pylsl.StreamInfo(name, stream_type, header.nchannels,
                                header.fsample, 'float32', source_id)
        channels = info.desc().append_child('channels')
        for label in (header.labels or
                      ['ch%d' % (i + 1) for i in range(header.nchannels)]):
            channel = channels.append_child('channel')
            channel.append_child_value('label', label)
            channel.append_child_value('unit', 'microvolts')
            channel.append_child_value('type', 'EEG')
        self.outlet = pylsl.StreamOutlet(info)
        self.sent = self.client.poll()[0]

    def pump(self):
        """Push whatever new samples the buffer holds; returns how many."""
        nsamples = self.client.poll()[0]
        if nsamples <= self.sent:
            return 0
        data = self.client.get_data(self.sent, nsamples - 1)
        self.outlet.push_chunk(np.asarray(data, dtype='float32').tolist())
        moved = nsamples - self.sent
        self.sent = nsamples
        return moved

    def run(self, interval=0.02):
        while True:
            if not self.pump():
                time.sleep(interval)
