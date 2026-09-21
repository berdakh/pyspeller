"""The speller matrix: symbol layout, flash sequences and symbol decoding."""
import random

import numpy as np

ROW = 'row'
COL = 'col'


class SpellerMatrix:
    """A row/column speller grid.

    Groups are flashed one at a time; a group is one row or one column, so a
    3x3 grid needs 6 flashes to cover every symbol once.  Each symbol sits at
    the intersection of exactly one row and one column, which is what lets the
    decoder turn per-group evidence into a letter.
    """

    def __init__(self, symbols):
        self.symbols = tuple(tuple(row) for row in symbols)
        self.n_rows = len(self.symbols)
        self.n_cols = len(self.symbols[0])
        if any(len(row) != self.n_cols for row in self.symbols):
            raise ValueError('all rows of the speller matrix must be equal length')

    @property
    def groups(self):
        """Every flashable group as (kind, index)."""
        return ([(ROW, r) for r in range(self.n_rows)]
                + [(COL, c) for c in range(self.n_cols)])

    def symbol_at(self, row, col):
        return self.symbols[row][col]

    def position_of(self, symbol):
        for r, row in enumerate(self.symbols):
            for c, sym in enumerate(row):
                if sym == symbol:
                    return r, c
        raise KeyError('%r is not in the speller matrix' % symbol)

    def contains(self, group, symbol):
        """True when flashing `group` illuminates `symbol`."""
        row, col = self.position_of(symbol)
        kind, index = group
        return index == (row if kind == ROW else col)

    def cells_of(self, group):
        kind, index = group
        if kind == ROW:
            return [(index, c) for c in range(self.n_cols)]
        return [(r, index) for r in range(self.n_rows)]

    # -- stimulus sequence -------------------------------------------------
    def flash_sequence(self, n_repetitions, rng=None, min_gap=2):
        """A randomised flash order covering every group `n_repetitions` times.

        Within each repetition every group appears exactly once, and the order
        is re-drawn until no group is flashed again within `min_gap` positions
        of its previous flash -- back-to-back repeats produce a refractory
        (attenuated) ERP and hurt the classifier.
        """
        rng = rng or random.Random()
        groups = self.groups
        sequence = []
        for _ in range(n_repetitions):
            for _attempt in range(100):
                block = groups[:]
                rng.shuffle(block)
                if self._gap_ok(sequence, block, min_gap):
                    break
            sequence.extend(block)
        return sequence

    @staticmethod
    def _gap_ok(sequence, block, min_gap):
        combined = sequence[-min_gap:] + block
        for i, group in enumerate(combined):
            for j in range(i + 1, min(i + 1 + min_gap, len(combined))):
                if combined[j] == group:
                    return False
        return True

    # -- decoding ----------------------------------------------------------
    def decode(self, scores):
        """Most likely symbol from accumulated per-group evidence.

        `scores` maps (kind, index) -> summed classifier output.  The best row
        and the best column intersect at the predicted symbol.
        """
        row_scores = np.array([scores.get((ROW, r), 0.0) for r in range(self.n_rows)])
        col_scores = np.array([scores.get((COL, c), 0.0) for c in range(self.n_cols)])
        row, col = int(np.argmax(row_scores)), int(np.argmax(col_scores))
        return self.symbol_at(row, col), (row, col)

    def __str__(self):
        return '\n'.join(' '.join(row) for row in self.symbols)
