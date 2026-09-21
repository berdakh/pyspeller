import unittest

import numpy as np

from pyspeller.buffer import BufferClient, BufferServer
from pyspeller.clock import BufferClock, Clock
from pyspeller.config import SpellerConfig
from pyspeller.acquisition.simulator import EEGSimulator


class TestSimulator(unittest.TestCase):
    def setUp(self):
        self.config = SpellerConfig(port=0, speed=20.0)
        self.server = BufferServer(port=0).start()
        self.config.port = self.server.port
        self.simulator = EEGSimulator(self.config, Clock(self.config.speed)).start()
        self.client = BufferClient(port=self.server.port).connect()
        self.header = self.client.wait_for_header()
        self.addCleanup(self.server.stop)
        self.addCleanup(self.simulator.stop)
        self.addCleanup(self.client.disconnect)

    def test_header_describes_the_montage(self):
        self.assertEqual(self.header.nchannels, self.config.n_channels)
        self.assertEqual(self.header.labels, list(self.config.channels))
        self.assertEqual(self.header.fsample, self.config.fsample)

    def test_samples_arrive_continuously(self):
        clock = BufferClock(self.client, self.config.fsample, self.config.speed)
        clock.sleep(1.0)
        nsamples = self.client.poll()[0]
        self.assertGreaterEqual(nsamples, self.config.fsample)
        data = self.client.get_data(nsamples - 64, nsamples - 1)
        self.assertEqual(data.shape, (64, self.config.n_channels))
        self.assertGreater(data.std(), 1.0)          # not a flat line

    def test_a_target_flash_produces_a_p300(self):
        clock = BufferClock(self.client, self.config.fsample, self.config.speed)
        pz = list(self.config.channels).index('Pz')
        trlen = int(0.6 * self.config.fsample)
        self.client.send_event('simulation.target', 'E')
        epochs = {True: [], False: []}
        for i in range(60):
            target = i % 2 == 0
            # row 1 contains E, row 0 does not
            self.client.send_event('stimulus.rowFlash', 1 if target else 0)
            start = self.client.poll()[0]
            clock.sleep(0.8)
            epochs[target].append(self.client.get_data(start, start + trlen - 1)[:, pz])
        mean_target = np.mean(epochs[True], axis=0)
        mean_other = np.mean(epochs[False], axis=0)
        difference = mean_target - mean_other
        peak_ms = int(np.argmax(difference) / self.config.fsample * 1000)
        self.assertGreater(difference.max(), 2.0)     # a clear positive deflection
        self.assertTrue(220 < peak_ms < 450, 'peak at %d ms' % peak_ms)


if __name__ == '__main__':
    unittest.main()
