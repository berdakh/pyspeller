import threading
import unittest

import numpy as np

from pyspeller.buffer import BufferClient, BufferServer
from pyspeller.signalproc.epochs import EpochGatherer, slice_epochs


class TestEpochs(unittest.TestCase):
    def setUp(self):
        self.server = BufferServer(port=0).start()
        self.writer = BufferClient(port=self.server.port).connect()
        self.reader = BufferClient(port=self.server.port).connect()
        self.writer.put_header(2, 100.0, labels=['a', 'b'])
        self.reader.wait_for_header()
        self.addCleanup(self.server.stop)
        self.addCleanup(self.writer.disconnect)
        self.addCleanup(self.reader.disconnect)

    def _put(self, nsamples, value=1.0):
        self.writer.put_data(np.full((nsamples, 2), value, dtype='float32'))

    def test_slice_epochs_cuts_at_the_event_sample(self):
        self._put(10, 0.0)
        self.writer.send_event('flash', 1)          # stamped at sample 10
        self._put(10, 5.0)
        events = self.reader.get_events()
        epochs, used = slice_epochs(self.reader, events, trlen_samples=5)
        self.assertEqual(epochs.shape, (1, 2, 5))
        np.testing.assert_allclose(epochs[0], 5.0)
        self.assertEqual(used, events)

    def test_gatherer_waits_for_the_data_behind_each_event(self):
        self.reader.reset_event_cursor()
        gatherer = EpochGatherer(self.reader, 'flash', trlen_samples=20)

        def stimulate():
            for i in range(3):
                self._put(5)
                self.writer.send_event('flash', i)
                self._put(25)
            self.writer.send_event('stimulus.training', 'end')
            self._put(25)

        threading.Thread(target=stimulate, daemon=True).start()
        epochs, events, stop = gatherer.gather(
            stop_types=[('stimulus.training', 'end')], timeout=10)
        self.assertEqual(epochs.shape, (3, 2, 20))
        self.assertEqual([e.value for e in events], [0, 1, 2])
        self.assertEqual(stop.value, 'end')

    def test_gatherer_ignores_a_stop_event_with_another_value(self):
        self.reader.reset_event_cursor()
        gatherer = EpochGatherer(self.reader, 'flash', trlen_samples=10)
        self.writer.send_event('stimulus.training', 'start')
        self._put(5)
        self.writer.send_event('flash', 9)
        self._put(15)
        self.writer.send_event('stimulus.training', 'end')
        epochs, events, stop = gatherer.gather(
            stop_types=[('stimulus.training', 'end')], timeout=5)
        self.assertEqual(len(events), 1)
        self.assertEqual(stop.value, 'end')

    def test_on_epoch_callback_runs_as_epochs_complete(self):
        self.reader.reset_event_cursor()
        seen = []
        gatherer = EpochGatherer(self.reader, 'flash', trlen_samples=10)
        self._put(2)
        self.writer.send_event('flash', 1)
        self._put(12)
        self.writer.send_event('stimulus.sequence', 'end')
        gatherer.gather(stop_types=[('stimulus.sequence', 'end')], timeout=5,
                        on_epoch=lambda epoch, event: seen.append(event.value))
        self.assertEqual(seen, [1])


if __name__ == '__main__':
    unittest.main()
