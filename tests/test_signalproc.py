import unittest

import numpy as np

from pyspeller.signalproc import preproc
from pyspeller.signalproc.classifier import ERPClassifier, ShrinkageLDA, auc


class TestPreproc(unittest.TestCase):
    def setUp(self):
        self.fs = 128.0
        self.t = np.arange(0, 2, 1 / self.fs)

    def test_detrend_removes_a_linear_ramp(self):
        X = (np.arange(50, dtype=float) * 0.3)[None, None, :]
        self.assertLess(np.abs(preproc.detrend(X)).max(), 1e-9)

    def test_spectral_filter_keeps_the_passband_and_kills_the_rest(self):
        signal = (np.sin(2 * np.pi * 5 * self.t)
                  + np.sin(2 * np.pi * 40 * self.t))[None, None, :]
        filtered = preproc.spectral_filter(signal, (0.1, 0.5, 10, 12), self.fs)
        spectrum = np.abs(np.fft.rfft(filtered[0, 0])) / (len(self.t) / 2)
        freqs = np.fft.rfftfreq(len(self.t), 1 / self.fs)
        self.assertGreater(spectrum[np.argmin(np.abs(freqs - 5))], 0.95)
        self.assertLess(spectrum[np.argmin(np.abs(freqs - 40))], 0.01)

    def test_spectral_filter_keeps_the_shape(self):
        X = np.random.default_rng(0).normal(size=(3, 4, 77))
        self.assertEqual(preproc.spectral_filter(X, (0.1, .5, 10, 12), 128).shape,
                         X.shape)

    def test_car_removes_what_every_channel_shares(self):
        common = np.sin(2 * np.pi * 3 * self.t)
        X = np.stack([common + 0.1 * i for i in range(4)])[None]
        referenced = preproc.car(X)
        np.testing.assert_allclose(referenced.mean(axis=1), 0, atol=1e-12)

    def test_subsample_averages_in_blocks(self):
        X = np.arange(16, dtype=float).reshape(1, 1, 16)
        out, fs = preproc.subsample(X, 16.0, 4.0)
        self.assertEqual(fs, 4.0)
        np.testing.assert_allclose(out[0, 0], [1.5, 5.5, 9.5, 13.5])

    def test_bad_channels_and_epochs_are_spotted(self):
        rng = np.random.default_rng(1)
        X = rng.normal(size=(20, 4, 64))
        X[:, 2] *= 30                                  # a dead / noisy electrode
        X[7] *= 25                                     # one artefact epoch
        self.assertIn(2, preproc.find_bad_channels(X))
        self.assertIn(7, preproc.find_bad_epochs(X))


class TestClassifier(unittest.TestCase):
    def test_auc_is_one_for_perfect_separation(self):
        labels = np.array([0, 0, 1, 1])
        self.assertEqual(auc(labels, np.array([0.0, 0.1, 0.9, 1.0])), 1.0)
        self.assertEqual(auc(labels, np.array([1.0, 0.9, 0.1, 0.0])), 0.0)
        self.assertEqual(auc(labels, np.ones(4)), 0.5)

    def test_lda_separates_two_gaussian_clouds(self):
        rng = np.random.default_rng(0)
        features = np.vstack([rng.normal(0, 1, (100, 5)),
                              rng.normal(0, 1, (100, 5)) + 1.5])
        labels = np.array([0] * 100 + [1] * 100)
        lda = ShrinkageLDA(0.1).fit(features, labels)
        self.assertGreater((lda.predict(features) == labels).mean(), 0.85)

    def test_erp_classifier_finds_a_simulated_p300(self):
        rng = np.random.default_rng(2)
        fs, n = 128.0, 77
        t = np.arange(n) / fs
        p300 = 6 * np.exp(-0.5 * ((t - 0.3) / 0.08) ** 2)
        # per-channel noise plus a common mode the reference should remove
        epochs = (rng.normal(0, 5, (120, 4, n))
                  + rng.normal(0, 7, (120, 1, n)))
        labels = np.array([i % 3 == 0 for i in range(120)]).astype(int)
        epochs[labels == 1] += p300 * np.array([0.2, 0.8, 1.0, 0.3])[:, None]
        clf = ERPClassifier(fs, channels=['Fz', 'Cz', 'Pz', 'Oz'])
        clf.fit(epochs, labels)
        area, accuracy = clf.cross_validate(epochs, labels)
        self.assertGreater(area, 0.8)
        self.assertGreater(accuracy, 0.6)

    def test_classifier_survives_a_round_trip_to_disk(self):
        import tempfile, os
        rng = np.random.default_rng(3)
        epochs = rng.normal(size=(40, 3, 64))
        labels = np.array([0, 1] * 20)
        epochs[labels == 1, 1, 20:30] += 5
        clf = ERPClassifier(128.0).fit(epochs, labels)
        path = os.path.join(tempfile.mkdtemp(), 'clsfr.pkl')
        clf.save(path)
        loaded = ERPClassifier.load(path)
        np.testing.assert_allclose(loaded.decision_function(epochs),
                                   clf.decision_function(epochs))

    def test_training_needs_two_classes(self):
        with self.assertRaises(ValueError):
            ShrinkageLDA().fit(np.zeros((10, 3)), np.zeros(10, dtype=int))


if __name__ == '__main__':
    unittest.main()


class TestChannelNames(unittest.TestCase):
    """The amplifier decides the montage; nothing may assume the configured one."""

    def test_a_channel_beyond_the_given_labels_still_has_a_name(self):
        clf = ERPClassifier(128.0, channels=['Fz', 'Cz'])
        self.assertEqual(clf.channel_name(0), 'Fz')
        self.assertEqual(clf.channel_name(7), 'ch8')

    def test_training_reports_bad_channels_of_a_wider_montage(self):
        rng = np.random.default_rng(4)
        epochs = rng.normal(0, 5, (40, 16, 64))      # 16 channel amplifier ...
        epochs[:, 11] *= 50                          # ... with a dead electrode
        labels = np.array([0, 1] * 20)
        clf = ERPClassifier(128.0, channels=['Fz', 'Cz', 'Pz'])   # 3 names only
        clf.fit(epochs, labels, verbose=True)        # must not raise
        self.assertIn(11, clf.bad_channels)
