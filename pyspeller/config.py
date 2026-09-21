"""Experiment configuration -- the python counterpart of configureSpeller.m."""
from dataclasses import dataclass

#: the classic 6x6 speller matrix (Farwell & Donchin; g.tec's speller uses the
#: same layout): the whole alphabet, the digits and a space key
SYMBOLS_6X6 = (('A', 'B', 'C', 'D', 'E', 'F'),
               ('G', 'H', 'I', 'J', 'K', 'L'),
               ('M', 'N', 'O', 'P', 'Q', 'R'),
               ('S', 'T', 'U', 'V', 'W', 'X'),
               ('Y', 'Z', '1', '2', '3', '4'),
               ('5', '6', '7', '8', '9', '_'))

#: the same matrix with the editing keys a real speller needs: space, full
#: stop, comma and a backspace (DEL) for when a letter comes out wrong.
#: This is the default, because a speller you cannot correct in is not usable.
SYMBOLS_6X6_CONTROL = (('A', 'B', 'C', 'D', 'E', 'F'),
                       ('G', 'H', 'I', 'J', 'K', 'L'),
                       ('M', 'N', 'O', 'P', 'Q', 'R'),
                       ('S', 'T', 'U', 'V', 'W', 'X'),
                       ('Y', 'Z', '0', '1', '2', '3'),
                       ('4', '5', '.', ',', '_', 'DEL'))

#: a 3x3 grid, handy for quick demonstrations and tests
SYMBOLS_3X3 = (('A', 'B', 'C'),
               ('D', 'E', 'F'),
               ('G', 'H', 'I'))

LAYOUTS = {'6x6': SYMBOLS_6X6, '6x6-control': SYMBOLS_6X6_CONTROL,
           '3x3': SYMBOLS_3X3}

#: words to calibrate and spell with, per layout -- a word has to be spellable
#: in the grid it is used with
DEFAULT_WORDS = {'6x6': (tuple('BRAIN'), tuple('BCI')),
                 '6x6-control': (tuple('BRAIN'), tuple('BCI')),
                 '3x3': (tuple('AEICG'), tuple('BHD'))}

DEFAULT_SYMBOLS = SYMBOLS_6X6_CONTROL

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
    min_gap: int = 3              # flashes between two flashes of the same group
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
    calibration_letters: tuple = tuple('BRAIN')   # the word spelled while calibrating
    feedback_letters: tuple = tuple('BCI')        # the word spelled with feedback
    free_spelling_letters: int = 8                # letters per free-spelling run
    seed: int = 42

    host: str = 'localhost'
    port: int = 1972

    @property
    def symbol_set(self):
        return {symbol for row in self.symbols for symbol in row}

    def missing_symbols(self, letters):
        """Which of `letters` the current matrix cannot spell."""
        return [letter for letter in letters if letter not in self.symbol_set]

    def use_layout(self, name):
        """Switch matrix, and take words that fit it if the current ones do not."""
        self.symbols = LAYOUTS[name]
        calibration, feedback = DEFAULT_WORDS[name]
        if self.missing_symbols(self.calibration_letters):
            self.calibration_letters = calibration
        if self.missing_symbols(self.feedback_letters):
            self.feedback_letters = feedback
        return self

    @property
    def n_rows(self):
        return len(self.symbols)

    @property
    def n_cols(self):
        return len(self.symbols[0])

    @property
    def n_channels(self):
        return len(self.channels)
