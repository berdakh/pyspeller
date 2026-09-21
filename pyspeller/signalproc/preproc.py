"""Pre-processing for ERP data -- numpy only, no scipy.

All functions take epochs shaped [n_epochs x n_channels x n_samples] (or any
array whose last axis is time and second-to-last is channels) and return an
array of the same shape, so they compose into a pipeline.
"""
import numpy as np


def detrend(X, axis=-1, order=1):
    """Remove a constant (order=0) or linear (order=1) trend along `axis`."""
    X = np.asarray(X, dtype=float)
    n = X.shape[axis]
    t = np.linspace(-1.0, 1.0, n)
    basis = np.vstack([t ** k for k in range(order + 1)])        # [order+1 x n]
    Xs = np.moveaxis(X, axis, -1)
    coef = np.linalg.lstsq(basis.T, Xs.reshape(-1, n).T, rcond=None)[0]
    fitted = (basis.T @ coef).T.reshape(Xs.shape)
    return np.moveaxis(Xs - fitted, -1, axis)


def car(X, channel_axis=-2, good_channels=None):
    """Common average reference: subtract the mean over channels."""
    X = np.asarray(X, dtype=float)
    if good_channels is None:
        mean = X.mean(axis=channel_axis, keepdims=True)
    else:
        good = np.asarray(good_channels)
        mean = np.take(X, good, axis=channel_axis).mean(axis=channel_axis,
                                                        keepdims=True)
    return X - mean


def spectral_filter(X, band, fsample, axis=-1):
    """Trapezoidal band-pass in the frequency domain.

    `band` is (stop_low, pass_low, pass_high, stop_high) in Hz -- the same
    four-corner specification the matlab side uses (e.g. [.1 .5 10 12]): full
    attenuation below stop_low, full pass between pass_low and pass_high, with
    linear ramps in between.  Doing it with an FFT keeps this dependency free
    and gives exactly zero phase distortion, which matters for ERPs.
    """
    X = np.asarray(X, dtype=float)
    n = X.shape[axis]
    freqs = np.fft.rfftfreq(n, d=1.0 / fsample)
    gain = _trapezoid(freqs, band)
    spectrum = np.fft.rfft(X, axis=axis)
    shape = [1] * X.ndim
    shape[axis] = gain.size
    return np.fft.irfft(spectrum * gain.reshape(shape), n=n, axis=axis)


def _trapezoid(freqs, band):
    lo_stop, lo_pass, hi_pass, hi_stop = [float(b) for b in band]
    gain = np.ones_like(freqs)
    gain[freqs <= lo_stop] = 0.0
    gain[freqs >= hi_stop] = 0.0
    rise = (freqs > lo_stop) & (freqs < lo_pass)
    if lo_pass > lo_stop:
        gain[rise] = (freqs[rise] - lo_stop) / (lo_pass - lo_stop)
    fall = (freqs > hi_pass) & (freqs < hi_stop)
    if hi_stop > hi_pass:
        gain[fall] = (hi_stop - freqs[fall]) / (hi_stop - hi_pass)
    return gain


def subsample(X, fsample, target_fsample, axis=-1):
    """Boxcar-average down to (about) `target_fsample`; returns (X, new_fs)."""
    step = max(1, int(round(fsample / float(target_fsample))))
    if step == 1:
        return np.asarray(X, dtype=float), float(fsample)
    Xs = np.moveaxis(np.asarray(X, dtype=float), axis, -1)
    n = (Xs.shape[-1] // step) * step
    Xs = Xs[..., :n].reshape(Xs.shape[:-1] + (n // step, step)).mean(axis=-1)
    return np.moveaxis(Xs, -1, axis), fsample / step


def channel_power(X, channel_axis=-2):
    """Log RMS power per channel, pooled over epochs and time."""
    X = np.asarray(X, dtype=float)
    Xs = np.moveaxis(X, channel_axis, 0).reshape(X.shape[channel_axis], -1)
    return np.log(np.sqrt((Xs ** 2).mean(axis=1)) + 1e-12)


def find_bad_channels(X, high_ratio=4.0, low_ratio=0.2, max_fraction=0.25):
    """Channels that are far louder or far quieter than the rest of the montage.

    The test is a ratio against the median channel rather than a z-score: with
    only a handful of electrodes, a z-score flags whichever channels carry the
    ERP (they genuinely have more in-band power), while a dead or railing
    electrode stands out by an order of magnitude.  At most `max_fraction` of
    the channels are ever rejected.
    """
    rms = np.exp(channel_power(X))
    median = np.median(rms)
    if median <= 0:
        return np.array([], dtype=int)
    ratio = rms / median
    bad = np.where((ratio > high_ratio) | (ratio < low_ratio))[0]
    cap = max(1, int(len(rms) * max_fraction))
    if len(bad) > cap:
        bad = np.sort(bad[np.argsort(-np.abs(np.log(ratio[bad])))[:cap]])
    return bad


def find_bad_epochs(X, threshold=3.0):
    """Epochs whose log-power is an outlier -- blinks, movement, amplifier jumps."""
    X = np.asarray(X, dtype=float)
    power = np.log(np.sqrt((X ** 2).reshape(X.shape[0], -1).mean(axis=1)) + 1e-12)
    return _outliers(power, threshold)


def _outliers(values, threshold):
    median = np.median(values)
    mad = np.median(np.abs(values - median))
    scale = mad * 1.4826 if mad > 0 else (values.std() or 1.0)
    return np.where(np.abs(values - median) > threshold * scale)[0]
