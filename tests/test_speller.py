import unittest

from pyspeller.config import SpellerConfig
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
        self.assertEqual(renderer.frames, [(((0, 0), (0, 1)), 'flash')])
        self.assertEqual(renderer.messages, ['hello'])

    def test_text_renderer_marks_the_flashed_cells(self):
        import io
        stream = io.StringIO()
        TextRenderer(SpellerMatrix(SYMBOLS), stream).draw([(1, 0), (1, 1), (1, 2)])
        printed = stream.getvalue()
        self.assertIn('*D*', printed)
        self.assertIn(' A ', printed)


class TestConfig(unittest.TestCase):
    def test_grid_shape_follows_the_symbols(self):
        config = SpellerConfig(symbols=(('1', '2'), ('3', '4'), ('5', '6')))
        self.assertEqual((config.n_rows, config.n_cols), (3, 2))
        self.assertEqual(config.n_channels, len(config.channels))


if __name__ == '__main__':
    unittest.main()
