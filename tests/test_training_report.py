"""What training reports back: metrics, class averages, and where they differ."""
import json
import unittest

import numpy as np

from pyspeller.buffer import BufferClient, BufferServer
from pyspeller.config import SYMBOLS_3X3, SpellerConfig
from pyspeller.speller.sigproc import SignalProcessor


def synthetic_epochs(n=120, n_channels=4, n_samples=77, seed=0):
    """Epochs with a P300 on the target trials, as the simulator would give."""
    rng = np.random.default_rng(seed)
    t = np.arange(n_samples) / 128.0
    p300 = 8 * np.exp(-0.5 * ((t - 0.3) / 0.08) ** 2)
    epochs = rng.normal(0, 5, (n, n_channels, n_samples)) + rng.normal(
        0, 7, (n, 1, n_samples))
    labels = np.array([i % 3 == 0 for i in range(n)]).astype(int)
    epochs[labels == 1] += p300 * np.array([0.2, 0.9, 1.0, 0.3])[:, None]
    return epochs, labels


class TestTrainingSummary(unittest.TestCase):
    def setUp(self):
        self.server = BufferServer(port=0).start()
        self.config = SpellerConfig(port=self.server.port, symbols=SYMBOLS_3X3,
                                    channels=('Fz', 'Cz', 'Pz', 'Oz'))
        self.client = BufferClient(port=self.server.port).connect()
        self.client.put_header(4, 128.0, labels=['Fz', 'Cz', 'Pz', 'Oz'])
        self.client.wait_for_header()
        self.processor = SignalProcessor(self.client, self.config, verbose=False)
        self.epochs, self.labels = synthetic_epochs()
        self.addCleanup(self.server.stop)
        self.addCleanup(self.client.disconnect)

    def test_training_publishes_a_summary_for_the_operator(self):
        reader = BufferClient(port=self.server.port).connect()
        self.addCleanup(reader.disconnect)
        reader.reset_event_cursor()

        self.processor.train(self.epochs, self.labels)
        summaries = [e for e in reader.new_events(timeout_ms=1000)
                     if e.type == 'classifier.summary']
        self.assertEqual(len(summaries), 1)
        summary = json.loads(summaries[0].value)
        self.assertGreater(summary['auc'], 0.7)
        self.assertEqual(summary['n_epochs'], len(self.labels))
        self.assertEqual(summary['n_targets'], int(self.labels.sum()))
        self.assertEqual(summary['channels'], ['Fz', 'Cz', 'Pz', 'Oz'])

    def test_the_summary_carries_the_two_class_averages(self):
        self.processor.train(self.epochs, self.labels)
        summary = self.processor.training_summary(self.epochs, self.labels)
        target = np.array(summary['erp_target'])
        nontarget = np.array(summary['erp_nontarget'])
        self.assertEqual(target.shape, nontarget.shape)
        self.assertEqual(target.shape[0], 4)                  # one row per channel
        self.assertEqual(target.shape[1], len(summary['times_ms']))
        # the P300 shows up in the difference, at the right electrode and time
        difference = target - nontarget
        channel = int(np.argmax(difference.max(axis=1)))
        peak_ms = summary['times_ms'][int(np.argmax(difference[channel]))]
        self.assertIn(summary['channels'][channel], ('Cz', 'Pz'))
        self.assertTrue(150 < peak_ms < 450, 'peak at %s ms' % peak_ms)

    def test_the_summary_says_where_the_classes_differ(self):
        self.processor.train(self.epochs, self.labels)
        summary = self.processor.training_summary(self.epochs, self.labels)
        values = np.array(summary['discriminability'])
        self.assertEqual(values.shape, (4, len(summary['times_ms'])))
        self.assertTrue(((values >= 0) & (values <= 1)).all())
        self.assertGreater(values.max(), 0.7)      # somewhere they clearly differ

    def test_the_confusion_matrix_adds_up(self):
        self.processor.train(self.epochs, self.labels)
        summary = self.processor.training_summary(self.epochs, self.labels)
        confusion = summary['confusion']
        self.assertEqual(sum(sum(row) for row in confusion), len(self.labels))
        self.assertEqual(sum(confusion[1]), int(self.labels.sum()))

    def test_the_summary_is_kept_with_the_recording(self):
        import os
        import tempfile
        directory = tempfile.mkdtemp()
        self.processor.save_dir = directory
        self.processor.train(self.epochs, self.labels)
        path = os.path.join(directory, 'training_summary.json')
        self.assertTrue(os.path.exists(path))
        with open(path) as handle:
            self.assertIn('discriminability', json.load(handle))


if __name__ == '__main__':
    unittest.main()
