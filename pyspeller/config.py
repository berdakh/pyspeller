"""Experiment configuration -- the python counterpart of configureSpeller.m."""
from dataclasses import dataclass

DEFAULT_SYMBOLS = (('A', 'B', 'C'),
                   ('D', 'E', 'F'),
                   ('G', 'H', 'I'))

# 10-20 positions where the P300 is largest; a small, realistic montage
DEFAULT_CHANNELS = ('Fz', 'Cz', 'Pz', 'Oz', 'P3', 'P4', 'C3', 'C4')


@dataclass
class SpellerConfig:
    # -- display -----------------------------------------------------------
    symbols: tuple = DEFAULT_SYMBOLS
    # -- stimulus timing (seconds of experiment time) ----------------------
    isi: float = 0.15             # onset-to-onset time between flashes
    stim_duration: float = 0.1    # how long a row/column stays highlighted
    cue_duration: float = 1.5     # target cue at the start of a calibration letter
    inter_seq_duration: float = 1.0
    feedback_duration: float = 1.5
    n_repetitions: int = 12       # flashes of each row/column per letter
    min_gap: int = 2              # flashes between two flashes of the same group
    # -- acquisition -------------------------------------------------------
    fsample: float = 128.0
    channels: tuple = DEFAULT_CHANNELS
    # -- analysis ----------------------------------------------------------
    trlen_ms: float = 600.0             # epoch length after each flash
    freq_band: tuple = (0.1, 0.5, 10.0, 12.0)   # trapezoidal spectral filter
    analysis_fsample: float = 16.0      # rate the classifier features live at
    spatial_filter: str = 'car'         # 'car' (common average reference) or 'none'
    regularisation: float = 0.6         # shrinkage of the LDA covariance
    # -- run control -------------------------------------------------------
    speed: float = 1.0            # >1 compresses experiment time (see clock.py)
    calibration_letters: tuple = ('A', 'E', 'I', 'C', 'G', 'F')
    feedback_letters: tuple = ('B', 'H', 'D')
    seed: int = 42

    host: str = 'localhost'
    port: int = 1972

    @property
    def n_rows(self):
        return len(self.symbols)

    @property
    def n_cols(self):
        return len(self.symbols[0])

    @property
    def n_channels(self):
        return len(self.channels)
