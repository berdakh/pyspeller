"""ERP classification: shrinkage LDA on top of the pre-processing pipeline."""
import pickle

import numpy as np

from . import preproc


class ShrinkageLDA:
    """Linear discriminant analysis with a regularised covariance.

    ERP features are high dimensional (channels x time points) relative to the
    number of epochs, so the empirical covariance is badly conditioned.
    Shrinking it towards a scaled identity is the standard fix and is what
    makes a small calibration run usable.
    """

    def __init__(self, regularisation=0.1):
        self.regularisation = float(regularisation)
        self.weights = None
        self.bias = 0.0

    def fit(self, features, labels):
        features = np.asarray(features, dtype=float)
        labels = np.asarray(labels).astype(int)
        classes = np.unique(labels)
        if len(classes) != 2:
            raise ValueError('need exactly two classes, got %s' % classes)
        neg, pos = features[labels == classes[0]], features[labels == classes[1]]
        mu_neg, mu_pos = neg.mean(axis=0), pos.mean(axis=0)

        centred = np.vstack([neg - mu_neg, pos - mu_pos])
        cov = centred.T @ centred / max(1, centred.shape[0] - 2)
        lam = self.regularisation
        cov = (1 - lam) * cov + lam * (np.trace(cov) / cov.shape[0]) * np.eye(cov.shape[0])

        self.weights = np.linalg.solve(cov, mu_pos - mu_neg)
        self.bias = -self.weights @ (mu_pos + mu_neg) / 2.0
        return self

    def decision_function(self, features):
        return np.asarray(features, dtype=float) @ self.weights + self.bias

    def predict(self, features):
        return (self.decision_function(features) > 0).astype(int)


class ERPClassifier:
    """The full ERP pipeline: pre-process, extract features, classify.

    Fitted on calibration epochs, then applied unchanged online -- every
    parameter learned at training time (bad channels, filter settings, the
    discriminant) is kept so that feedback sees exactly the training pipeline.
    """

    def __init__(self, fsample, freq_band=(0.1, 0.5, 10.0, 12.0),
                 analysis_fsample=16.0, regularisation=0.5, channels=None,
                 spatial_filter='car'):
        self.fsample = float(fsample)
        self.freq_band = tuple(freq_band)
        self.analysis_fsample = float(analysis_fsample)
        self.spatial_filter = spatial_filter
        self.channels = list(channels) if channels is not None else None
        self.lda = ShrinkageLDA(regularisation)
        self.bad_channels = np.array([], dtype=int)
        self.feature_shape = None

    # -- feature pipeline --------------------------------------------------
    def preprocess(self, epochs):
        X = np.asarray(epochs, dtype=float)
        if X.ndim == 2:                      # a single epoch
            X = X[None]
        X = preproc.detrend(X)
        good = [c for c in range(X.shape[1]) if c not in set(self.bad_channels)]
        if self.spatial_filter == 'car':
            X = preproc.car(X, good_channels=good)
        if len(self.bad_channels):
            X[:, self.bad_channels, :] = 0.0
        X = preproc.spectral_filter(X, self.freq_band, self.fsample)
        X, _ = preproc.subsample(X, self.fsample, self.analysis_fsample)
        return X

    def features(self, epochs):
        X = self.preprocess(epochs)
        self.feature_shape = X.shape[1:]
        return X.reshape(X.shape[0], -1)

    # -- training ----------------------------------------------------------
    def fit(self, epochs, labels, remove_bad_epochs=True, verbose=False):
        X = np.asarray(epochs, dtype=float)
        labels = np.asarray(labels).astype(int)
        # look for bad channels in the band we actually analyse, so that slow
        # drift and mains noise outside it do not condemn a good electrode
        in_band = preproc.spectral_filter(preproc.detrend(X), self.freq_band,
                                          self.fsample)
        self.bad_channels = preproc.find_bad_channels(in_band)
        if remove_bad_epochs:
            bad = preproc.find_bad_epochs(in_band)
            if len(bad) and len(bad) < len(labels) // 4:
                keep = np.setdiff1d(np.arange(len(labels)), bad)
                X, labels = X[keep], labels[keep]
                if verbose:
                    print('dropped %d artefact epochs' % len(bad))
        if verbose and len(self.bad_channels):
            print('dropped bad channels: %s'
                  % ', '.join(self.channel_name(c) for c in self.bad_channels))
        self.lda.fit(self.features(X), labels)
        return self

    def decision_function(self, epochs):
        return self.lda.decision_function(self.features(epochs))

    def predict(self, epochs):
        return (self.decision_function(epochs) > 0).astype(int)

    def channel_name(self, index):
        """A channel's label, falling back to its index.

        The amplifier decides how many channels there are, so never assume the
        names handed in cover them all.
        """
        if self.channels and index < len(self.channels):
            return self.channels[index]
        return 'ch%d' % (index + 1)

    # -- evaluation --------------------------------------------------------
    def cross_validate(self, epochs, labels, n_folds=5):
        """Stratified k-fold (AUC, accuracy) -- an honest calibration report."""
        X = np.asarray(epochs, dtype=float)
        labels = np.asarray(labels).astype(int)
        folds = _stratified_folds(labels, n_folds)
        scores = np.zeros(len(labels))
        for test_idx in folds:
            train_idx = np.setdiff1d(np.arange(len(labels)), test_idx)
            fold = ERPClassifier(self.fsample, self.freq_band,
                                 self.analysis_fsample,
                                 self.lda.regularisation, self.channels,
                                 self.spatial_filter)
            fold.fit(X[train_idx], labels[train_idx], remove_bad_epochs=False)
            scores[test_idx] = fold.decision_function(X[test_idx])
        return auc(labels, scores), float(((scores > 0).astype(int) == labels).mean())

    # -- persistence -------------------------------------------------------
    def save(self, path):
        with open(path, 'wb') as fh:
            pickle.dump(self, fh)
        return path

    @staticmethod
    def load(path):
        with open(path, 'rb') as fh:
            return pickle.load(fh)


def _stratified_folds(labels, n_folds):
    rng = np.random.default_rng(0)
    folds = [[] for _ in range(n_folds)]
    for cls in np.unique(labels):
        idx = np.where(labels == cls)[0]
        rng.shuffle(idx)
        for i, sample in enumerate(idx):
            folds[i % n_folds].append(sample)
    return [np.array(sorted(f), dtype=int) for f in folds]


def auc(labels, scores):
    """Area under the ROC curve, via the rank-sum identity."""
    labels = np.asarray(labels).astype(int)
    scores = np.asarray(scores, dtype=float)
    pos, neg = (labels == 1).sum(), (labels == 0).sum()
    if pos == 0 or neg == 0:
        return float('nan')
    order = np.argsort(scores)
    ranks = np.empty(len(scores), dtype=float)
    ranks[order] = np.arange(1, len(scores) + 1)
    # average the ranks of tied scores so ties count as chance
    unique, inverse, counts = np.unique(scores, return_inverse=True, return_counts=True)
    for value in unique[counts > 1]:
        tied = scores == value
        ranks[tied] = ranks[tied].mean()
    return float((ranks[labels == 1].sum() - pos * (pos + 1) / 2.0) / (pos * neg))
