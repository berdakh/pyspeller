"""The LSL path: what a g.tec amplifier looks like from the framework's side.

pylsl is optional, so these tests skip when it is not installed.  They put a
stream on the network themselves (as g.NEEDaccess would) and check that the
bridge moves samples and markers into the buffer.
"""
import time
import unittest

import numpy as np

from pyspeller.buffer import BufferClient, BufferServer

try:
    import pylsl
except ImportError:                       # pragma: no cover
    pylsl = None


@unittest.skipIf(pylsl is None, 'pylsl is not installed')
class TestLSLBridge(unittest.TestCase):
    def setUp(self):
        from pyspeller.acquisition.lsl_bridge import LSLBridge
        self.LSLBridge = LSLBridge
        self.name = 'pyspeller-test-%d' % (time.time() * 1000 % 1e6)
        info = pylsl.StreamInfo(self.name, 'EEG', 3, 100.0, 'float32', self.name)
        channels = info.desc().append_child('channels')
        for label in ('Fz', 'Cz', 'Pz'):
            channels.append_child('channel').append_child_value('label', label)
        self.outlet = pylsl.StreamOutlet(info)
        self.server = BufferServer(port=0).start()
        self.addCleanup(self.server.stop)

    def _bridge(self):
        bridge = self.LSLBridge(port=self.server.port, name=self.name,
                                marker_type=None, verbose=False).connect()
        self.addCleanup(bridge.stop)
        return bridge

    def test_stream_is_discoverable(self):
        from pyspeller.acquisition.lsl_bridge import list_streams, resolve_stream
        names = [s['name'] for s in list_streams(timeout=2.0)]
        self.assertIn(self.name, names)
        self.assertEqual(resolve_stream(self.name, 'EEG', 2.0).channel_count(), 3)

    def test_bridge_writes_the_header_from_the_stream_info(self):
        self._bridge()
        client = BufferClient(port=self.server.port).connect()
        self.addCleanup(client.disconnect)
        header = client.wait_for_header(timeout=5)
        self.assertEqual(header.nchannels, 3)
        self.assertEqual(header.fsample, 100.0)
        self.assertEqual(header.labels, ['Fz', 'Cz', 'Pz'])

    def test_samples_reach_the_buffer(self):
        bridge = self._bridge()
        client = BufferClient(port=self.server.port).connect()
        self.addCleanup(client.disconnect)
        client.wait_for_header(timeout=5)
        samples = np.arange(30, dtype='float32').reshape(10, 3)
        bridge.pump(timeout=0.1)          # the inlet subscribes on its first pull
        deadline = time.time() + 10
        while client.poll()[0] < 10 and time.time() < deadline:
            self.outlet.push_chunk(samples.tolist())
            bridge.pump(timeout=0.1)
        self.assertGreaterEqual(client.poll()[0], 10)
        np.testing.assert_allclose(client.get_data(0, 9), samples, rtol=1e-5)


if __name__ == '__main__':
    unittest.main()
