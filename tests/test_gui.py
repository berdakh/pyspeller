"""Smoke tests for the tk control panel.

They need a display, so they skip on a headless machine (use xvfb to run them
in CI: `xvfb-run python -m unittest tests.test_gui`).
"""
import unittest

import numpy as np

from pyspeller.buffer import BufferClient, BufferServer
from pyspeller.config import SYMBOLS_6X6, SpellerConfig
from pyspeller.speller.matrix import SpellerMatrix

try:
    import tkinter
    tkinter.Tk().destroy()
    HAVE_DISPLAY = True
except Exception:                     # pragma: no cover - depends on the machine
    HAVE_DISPLAY = False


@unittest.skipUnless(HAVE_DISPLAY, 'no tk display available')
class TestControlPanel(unittest.TestCase):
    def setUp(self):
        from pyspeller.gui.control_panel import ControlPanel
        self.server = BufferServer(port=0).start()
        self.config = SpellerConfig(port=self.server.port)
        self.writer = BufferClient(port=self.server.port).connect()
        self.writer.put_header(self.config.n_channels, self.config.fsample,
                               labels=list(self.config.channels))
        self.panel = ControlPanel(self.config)
        self.addCleanup(self.server.stop)
        self.addCleanup(self.writer.disconnect)
        self.addCleanup(self.panel.root.destroy)

    def _tick(self):
        """One update cycle, without scheduling the next one."""
        self.panel._pump_data()
        self.panel._pump_events()
        self.panel.root.update()
        self.panel._draw_scope()
        self.panel._draw_quality()

    def test_buttons_publish_phase_commands(self):
        reader = BufferClient(port=self.server.port).connect()
        self.addCleanup(reader.disconnect)
        reader.reset_event_cursor()
        self.panel.send_phase('calibrate')
        events = reader.new_events(timeout_ms=1000)
        self.assertEqual([(e.type, e.value) for e in events],
                         [('startPhase.cmd', 'calibrate')])

    def test_scope_follows_the_data(self):
        rng = np.random.default_rng(0)
        self.writer.put_data(rng.normal(0, 10, (256, self.config.n_channels))
                             .astype('float32'))
        self._tick()
        self.assertEqual(self.panel.cursor, 256)
        coords = self.panel.scope.coords(self.panel._traces[0])
        self.assertGreater(len(coords), 4)
        self.assertIn('256 samples', self.panel.status.get())

    def test_predictions_build_up_the_spelled_text(self):
        self.writer.send_event('classifier.prediction', 'H')
        self.writer.send_event('classifier.prediction', 'I')
        self._tick()
        self.assertEqual(self.panel.spelled, 'HI')
        self.assertIn('HI', self.panel.spelled_var.get())

    def test_the_backspace_button_corrects_a_wrong_letter(self):
        for symbol in ('B', 'C', 'X'):
            self.writer.send_event('classifier.prediction', symbol)
        self._tick()
        self.assertEqual(self.panel.spelled, 'BCX')
        self.panel.send_edit()               # what the backspace button does
        self._tick()
        self.assertEqual(self.panel.spelled, 'BC')
        self.assertIn('BC_', self.panel.spelled_var.get())

    def test_the_clear_button_empties_the_text(self):
        self.writer.send_event('classifier.prediction', 'A')
        self._tick()
        from pyspeller.speller import text as speller_text
        self.panel.send_edit(speller_text.CLEAR)
        self._tick()
        self.assertEqual(self.panel.spelled, '')

    def test_the_control_keys_edit_the_typed_text(self):
        for symbol in ('B', 'C', 'X', 'DEL', 'I', '_', 'A'):
            self.writer.send_event('classifier.prediction', symbol)
        self._tick()
        self.assertEqual(self.panel.spelled, 'BCI A')

    def test_speller_window_draws_the_alphabet_matrix(self):
        from pyspeller.speller.render import TkRenderer
        renderer = TkRenderer(SpellerMatrix(SYMBOLS_6X6), master=self.panel.root)
        self.addCleanup(renderer.root.destroy)
        self.assertEqual(len(renderer._items), 36)
        renderer.draw([(0, c) for c in range(6)], 'flash')
        renderer.message('look at: A')
        renderer.pump()
        self.assertEqual(renderer.canvas.itemcget(renderer._items[(0, 0)], 'fill'),
                         '#ffffff')
        self.assertEqual(renderer.canvas.itemcget(renderer._items[(1, 0)], 'fill'),
                         '#808080')

    def test_the_speller_window_shows_the_typed_text(self):
        from pyspeller.speller.render import TkRenderer
        renderer = TkRenderer(SpellerMatrix(SYMBOLS_6X6), master=self.panel.root)
        self.addCleanup(renderer.root.destroy)
        renderer.set_output('HELLO')
        renderer.pump()
        self.assertEqual(renderer.canvas.itemcget(renderer._output, 'text'),
                         'HELLO_')

    def test_multi_character_keys_get_a_smaller_font(self):
        from pyspeller.config import SYMBOLS_6X6_CONTROL
        from pyspeller.speller.render import TkRenderer
        renderer = TkRenderer(SpellerMatrix(SYMBOLS_6X6_CONTROL),
                              master=self.panel.root)
        self.addCleanup(renderer.root.destroy)
        letter = renderer.canvas.itemcget(renderer._items[(0, 0)], 'font')
        delete = renderer.canvas.itemcget(renderer._items[(5, 5)], 'font')
        self.assertLess(int(delete.split()[1]), int(letter.split()[1]))


if __name__ == '__main__':
    unittest.main()
