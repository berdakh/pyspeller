import unittest

from pyspeller.config import (LAYOUTS, SYMBOLS_6X6, SYMBOLS_6X6_CONTROL,
                              SpellerConfig)
from pyspeller.speller import text as speller_text
from pyspeller.speller.matrix import COL, ROW, SpellerMatrix
from pyspeller.speller.render import HeadlessRenderer, TextRenderer

SYMBOLS = (('A', 'B', 'C'), ('D', 'E', 'F'), ('G', 'H', 'I'))


class TestMatrix(unittest.TestCase):
    def setUp(self):
        self.matrix = SpellerMatrix(SYMBOLS)

    def test_positions_and_membership(self):
        self.assertEqual(self.matrix.position_of('F'), (1, 2))
        self.assertTrue(self.matrix.contains((ROW, 1), 'F'))
        self.assertTrue(self.matrix.contains((COL, 2), 'F'))
        self.assertFalse(self.matrix.contains((ROW, 0), 'F'))
        with self.assertRaises(KeyError):
            self.matrix.position_of('Z')

    def test_a_flash_sequence_covers_every_group_equally(self):
        import random
        sequence = self.matrix.flash_sequence(5, random.Random(0), min_gap=2)
        self.assertEqual(len(sequence), 5 * 6)
        for group in self.matrix.groups:
            self.assertEqual(sequence.count(group), 5)

    def test_a_flash_sequence_does_not_repeat_a_group_too_soon(self):
        import random
        sequence = self.matrix.flash_sequence(10, random.Random(1), min_gap=2)
        for i, group in enumerate(sequence):
            self.assertNotIn(group, sequence[i + 1:i + 3])

    def test_decode_picks_the_intersection_of_the_best_row_and_column(self):
        scores = {(ROW, 0): 0.1, (ROW, 1): 0.2, (ROW, 2): 2.0,
                  (COL, 0): 0.3, (COL, 1): 1.9, (COL, 2): 0.1}
        symbol, (row, col) = self.matrix.decode(scores)
        self.assertEqual((symbol, row, col), ('H', 2, 1))

    def test_non_rectangular_layouts_are_refused(self):
        with self.assertRaises(ValueError):
            SpellerMatrix((('A', 'B'), ('C',)))


class TestRenderers(unittest.TestCase):
    def test_headless_renderer_records_frames(self):
        renderer = HeadlessRenderer(SpellerMatrix(SYMBOLS))
        renderer.draw([(0, 0), (0, 1)], 'flash')
        renderer.message('hello')
        renderer.set_output('BCI')
        self.assertEqual(renderer.frames, [(((0, 0), (0, 1)), 'flash')])
        self.assertEqual(renderer.messages, ['hello'])
        self.assertEqual(renderer.output, 'BCI')

    def test_text_renderer_marks_the_flashed_cells(self):
        import io
        stream = io.StringIO()
        TextRenderer(SpellerMatrix(SYMBOLS), stream).draw([(1, 0), (1, 1), (1, 2)])
        printed = stream.getvalue()
        self.assertIn('*D*', printed)
        self.assertIn(' A ', printed)


class TestLayouts(unittest.TestCase):
    """The default grid is the 6x6 matrix a commercial speller uses."""

    def test_the_alphabet_grid_holds_every_letter_and_digit(self):
        symbols = [s for row in SYMBOLS_6X6 for s in row]
        self.assertEqual(len(symbols), 36)
        self.assertEqual(len(set(symbols)), 36)
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            self.assertIn(letter, symbols)
        for digit in '123456789':
            self.assertIn(digit, symbols)
        self.assertIn(speller_text.SPACE, symbols)

    def test_the_control_grid_has_the_editing_keys(self):
        symbols = [s for row in SYMBOLS_6X6_CONTROL for s in row]
        self.assertIn(speller_text.DELETE, symbols)
        self.assertIn(speller_text.SPACE, symbols)
        self.assertIn('.', symbols)

    def test_the_default_configuration_is_the_6x6_grid_with_editing_keys(self):
        config = SpellerConfig()
        self.assertEqual(config.symbols, SYMBOLS_6X6_CONTROL)
        self.assertEqual((config.n_rows, config.n_cols), (6, 6))
        symbols = [s for row in config.symbols for s in row]
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            self.assertIn(letter, symbols)
        self.assertIn(speller_text.DELETE, symbols)

    def test_every_layout_is_a_usable_matrix(self):
        for name, symbols in LAYOUTS.items():
            matrix = SpellerMatrix(symbols)
            self.assertEqual(len(matrix.groups), matrix.n_rows + matrix.n_cols)
            for group in matrix.groups:
                self.assertTrue(matrix.cells_of(group))

    def test_flashing_the_big_grid_covers_every_symbol_once_per_repetition(self):
        import random
        matrix = SpellerMatrix(SYMBOLS_6X6)
        sequence = matrix.flash_sequence(1, random.Random(0), min_gap=3)
        self.assertEqual(len(sequence), 12)
        for symbol in (s for row in SYMBOLS_6X6 for s in row):
            lit = [g for g in sequence if matrix.contains(g, symbol)]
            self.assertEqual(len(lit), 2)      # its row and its column


class TestTypedText(unittest.TestCase):
    """Decoded symbols become text: a space key, a backspace, a clear."""

    def test_letters_are_appended(self):
        self.assertEqual(speller_text.spell('BCI'), 'BCI')

    def test_the_space_key_types_a_space(self):
        self.assertEqual(speller_text.spell(['H', 'I', '_', 'A']), 'HI A')

    def test_delete_removes_the_last_character(self):
        self.assertEqual(speller_text.spell(['B', 'C', 'X', 'DEL', 'I']), 'BCI')
        self.assertEqual(speller_text.apply_symbol('', 'DEL'), '')

    def test_clear_empties_the_field(self):
        self.assertEqual(speller_text.spell(['A', 'B', 'CLR', 'C']), 'C')

    def test_a_missed_prediction_leaves_the_text_alone(self):
        self.assertEqual(speller_text.apply_symbol('BC', None), 'BC')

    def test_the_field_is_shown_with_a_caret(self):
        self.assertEqual(speller_text.display('BCI'), 'BCI_')


class TestConfig(unittest.TestCase):
    def test_grid_shape_follows_the_symbols(self):
        config = SpellerConfig(symbols=(('1', '2'), ('3', '4'), ('5', '6')))
        self.assertEqual((config.n_rows, config.n_cols), (3, 2))
        self.assertEqual(config.n_channels, len(config.channels))


if __name__ == '__main__':
    unittest.main()


class TestLayoutWords(unittest.TestCase):
    """A word can only be spelled in a matrix that holds all of its letters."""

    def test_switching_layout_keeps_words_that_still_fit(self):
        config = SpellerConfig(calibration_letters=tuple('ABC'),
                               feedback_letters=tuple('AB'))
        config.use_layout('3x3')
        self.assertEqual(config.calibration_letters, tuple('ABC'))
        self.assertEqual(config.feedback_letters, tuple('AB'))

    def test_switching_to_a_smaller_layout_replaces_words_that_do_not(self):
        config = SpellerConfig()                  # calibrates on BRAIN
        config.use_layout('3x3')
        self.assertEqual(config.missing_symbols(config.calibration_letters), [])
        self.assertEqual(config.missing_symbols(config.feedback_letters), [])

    def test_missing_symbols_lists_what_the_grid_cannot_spell(self):
        config = SpellerConfig(symbols=(('A', 'B'), ('C', 'D')))
        self.assertEqual(config.missing_symbols('BAD'), [])
        self.assertEqual(config.missing_symbols('CAB.'), ['.'])
