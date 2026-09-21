"""The whole framework, end to end: acquisition -> epochs -> classifier -> letters.

Uses the default 6x6 alphabet grid, at speed=20 -- so an experiment that would
take four minutes with a real subject runs in about ten seconds.
"""
import unittest

import numpy as np

from pyspeller.config import SpellerConfig
from pyspeller.experiment import LocalExperiment


class TestEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = SpellerConfig(
            port=0, speed=20.0, cue_duration=1.0,
            inter_seq_duration=0.5, feedback_duration=0.5,
            calibration_letters=tuple('BRAIN'),
            feedback_letters=tuple('BC_I'))     # includes the space key
        cls.experiment = LocalExperiment(cls.config, verbose=False).start()
        cls.epochs, cls.labels = cls.experiment.calibrate()
        cls.report = cls.experiment.train()
        cls.pairs = cls.experiment.feedback()

    @classmethod
    def tearDownClass(cls):
        cls.experiment.stop()

    def test_calibration_collects_one_labelled_epoch_per_flash(self):
        flashes = (len(self.config.calibration_letters)
                   * self.config.n_repetitions
                   * (self.config.n_rows + self.config.n_cols))
        self.assertEqual(len(self.labels), flashes)
        self.assertEqual(self.epochs.shape[1], self.config.n_channels)
        self.assertEqual(self.epochs.shape[2],
                         round(self.config.trlen_ms * self.config.fsample / 1000))

    def test_the_grid_holds_the_whole_alphabet(self):
        symbols = [s for row in self.config.symbols for s in row]
        self.assertEqual((self.config.n_rows, self.config.n_cols), (6, 6))
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            self.assertIn(letter, symbols)

    def test_one_group_in_six_contains_the_target(self):
        groups = self.config.n_rows + self.config.n_cols
        self.assertAlmostEqual(self.labels.mean(), 2 / groups, places=6)

    def test_the_average_target_epoch_has_a_p300(self):
        pz = list(self.config.channels).index('Pz')
        difference = (self.epochs[self.labels == 1].mean(axis=0)[pz]
                      - self.epochs[self.labels == 0].mean(axis=0)[pz])
        peak_ms = int(np.argmax(difference) / self.config.fsample * 1000)
        self.assertGreater(difference.max(), 1.5)
        self.assertTrue(200 < peak_ms < 500, 'peak at %d ms' % peak_ms)

    def test_the_classifier_beats_chance_on_single_flashes(self):
        self.assertGreater(self.report['auc'], 0.65)

    def test_feedback_spells_the_cued_letters(self):
        self.assertEqual(len(self.pairs), len(self.config.feedback_letters))
        for target, prediction in self.pairs:
            self.assertIn(prediction, [s for row in self.config.symbols for s in row])
        correct = sum(target == prediction for target, prediction in self.pairs)
        self.assertGreaterEqual(correct, len(self.pairs) / 2.0,
                                'only spelled %s' % (self.pairs,))

    def test_the_typed_text_is_what_was_decoded(self):
        from pyspeller.speller.text import spell
        typed = self.experiment.stimulus.spelled
        self.assertEqual(typed, spell(p for _, p in self.pairs))
        self.assertEqual(len(typed.replace(' ', '_')), len(self.pairs))


if __name__ == '__main__':
    unittest.main()
