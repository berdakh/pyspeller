"""Recording a session to disk, and reading it back."""
import os
import shutil
import tempfile
import unittest

import numpy as np

from pyspeller.acquisition.saver import (BufferSaver, load_epochs, load_session,
                                         save_epochs, session_directory)
from pyspeller.buffer import BufferClient, BufferServer


class TestBufferSaver(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()
        self.server = BufferServer(port=0, max_samples=500).start()
        self.writer = BufferClient(port=self.server.port).connect()
        self.writer.put_header(3, 100.0, labels=['Fz', 'Cz', 'Pz'])
        self.saver = BufferSaver(port=self.server.port, directory=self.directory,
                                 verbose=False).connect()
        self.addCleanup(shutil.rmtree, self.directory, True)
        self.addCleanup(self.saver.close)
        self.addCleanup(self.server.stop)
        self.addCleanup(self.writer.disconnect)

    def test_samples_and_events_land_on_disk(self):
        data = np.arange(30, dtype='float32').reshape(10, 3)
        self.writer.put_data(data)
        self.writer.send_event('stimulus.tgtFlash', 1)
        self.writer.send_event('classifier.prediction', 'H')
        self.saver.pump(timeout_ms=200)
        self.saver.close()

        header, samples, events = load_session(self.directory)
        self.assertEqual(header.nchannels, 3)
        self.assertEqual(header.fsample, 100.0)
        self.assertEqual(header.labels, ['Fz', 'Cz', 'Pz'])
        self.assertEqual(header.nsamples, 10)
        np.testing.assert_allclose(samples, data)
        self.assertEqual([(e.type, e.value, e.sample) for e in events],
                         [('stimulus.tgtFlash', 1, 10),
                          ('classifier.prediction', 'H', 10)])

    def test_the_ascii_header_describes_the_recording(self):
        self.writer.put_data(np.zeros((4, 3), dtype='float32'))
        self.saver.pump(timeout_ms=200)
        self.saver.close()
        with open(os.path.join(self.directory, 'header.txt')) as fh:
            text = fh.read()
        for line in ('fSample=100', 'nChans=3', 'nSamples=4', 'dataType=float32',
                     '1:Fz', '3:Pz'):
            self.assertIn(line, text)

    def test_saving_continues_across_several_blocks(self):
        for block in range(5):
            self.writer.put_data(np.full((20, 3), block, dtype='float32'))
            self.saver.pump(timeout_ms=200)
        self.saver.close()
        _, samples, _ = load_session(self.directory)
        self.assertEqual(samples.shape, (100, 3))
        np.testing.assert_allclose(samples[0], 0)
        np.testing.assert_allclose(samples[-1], 4)

    def test_a_gap_is_padded_so_event_samples_stay_valid(self):
        """If the buffer wraps before we read it, keep the sample numbering."""
        self.writer.put_data(np.ones((10, 3), dtype='float32'))
        self.saver.pump(timeout_ms=100)
        for _ in range(6):                    # overrun the 500 sample ring
            self.writer.put_data(np.full((100, 3), 7, dtype='float32'))
        self.writer.send_event('late', 'event')
        self.saver.pump(timeout_ms=200)
        self.saver.close()

        header, samples, events = load_session(self.directory)
        self.assertEqual(samples.shape[0], header.nsamples)
        self.assertEqual(samples.shape[0], self.writer.poll()[0])
        self.assertTrue(self.saver.gaps, 'the lost samples should be recorded')
        # the event still points at the sample it was stamped with
        self.assertEqual(events[-1].sample, samples.shape[0])
        np.testing.assert_allclose(samples[-1], 7)

    def test_the_session_directory_follows_the_buffer_bci_convention(self):
        path = session_directory('/tmp/out', 'speller', 'S1', now=0)
        self.assertTrue(path.startswith('/tmp/out/speller/S1/'))
        self.assertTrue(path.endswith('raw_buffer'))


class TestEpochFiles(unittest.TestCase):
    def test_epochs_survive_a_round_trip(self):
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory, True)
        epochs = np.random.default_rng(0).normal(size=(12, 4, 77))
        labels = np.array([0, 1] * 6)
        path = save_epochs(os.path.join(directory, 'cal.npz'), epochs, labels,
                           metadata={'fsample': 128.0})
        loaded, loaded_labels, metadata = load_epochs(path)
        np.testing.assert_allclose(loaded, epochs)
        np.testing.assert_array_equal(loaded_labels, labels)
        self.assertEqual(metadata['fsample'], 128.0)


if __name__ == '__main__':
    unittest.main()
