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

    def test_a_training_summary_opens_the_result_window(self):
        summary = {
            'auc': 0.78, 'accuracy': 0.72, 'n_epochs': 360, 'n_targets': 60,
            'channels': ['Fz', 'Cz', 'Pz'], 'bad_channels': ['Oz'],
            'times_ms': [0, 100, 200, 300, 400, 500],
            'erp_target': [[0, 1, 2, 6, 3, 1]] * 3,
            'erp_nontarget': [[0, 0, 1, 1, 0, 0]] * 3,
            'discriminability': [[0.5, 0.5, 0.6, 0.8, 0.6, 0.5]] * 3,
            'confusion': [[200, 100], [20, 40]],
        }
        self.assertIsNotNone(self.panel.show_training(summary))
        self._tick()
        self.assertIsNotNone(self.panel.training_view)
        self.assertIn('0.78', self.panel.training_view.headline.get())
        self.assertIn('72%', self.panel.training_view.headline.get())
        self.assertIn('360 epochs', self.panel.training_view.subhead.get())
        self.assertIn('Oz', self.panel.training_view.subhead.get())
        self.assertIn('AUC 0.780', self.panel.status.get())
        self.addCleanup(self.panel.training_view.destroy)

    def test_a_summary_that_arrives_as_an_event_is_shown_too(self):
        import json
        summary = {'auc': 0.66, 'accuracy': 0.61, 'n_epochs': 120, 'n_targets': 20,
                   'channels': ['Cz'], 'bad_channels': [],
                   'times_ms': [0, 200, 400], 'erp_target': [[0, 3, 1]],
                   'erp_nontarget': [[0, 0, 0]],
                   'discriminability': [[0.5, 0.7, 0.5]],
                   'confusion': [[80, 20], [8, 12]]}
        self.writer.send_event('classifier.summary', json.dumps(summary))
        self._tick()
        self.assertEqual(self.panel.training['auc'], 0.66)
        self.assertIn('usable', self.panel.training_view.headline.get())
        self.addCleanup(self.panel.training_view.destroy)

    def test_a_new_block_starts_a_new_line_of_text(self):
        self.writer.send_event('classifier.prediction', 'A')
        self._tick()
        self.assertEqual(self.panel.spelled, 'A')
        self.writer.send_event('stimulus.feedback', 'start')
        self._tick()
        self.assertEqual(self.panel.spelled, '')

    def test_the_pause_button_asks_for_a_pause_then_a_resume(self):
        from pyspeller.speller import text as speller_text
        reader = BufferClient(port=self.server.port).connect()
        self.addCleanup(reader.disconnect)
        reader.reset_event_cursor()

        self.assertEqual(self.panel.toggle_pause(), speller_text.PAUSE)
        self._tick()                       # the panel follows the event back
        self.assertTrue(self.panel.paused)
        self.assertIn('resume', self.panel.pause_text.get())

        self.assertEqual(self.panel.toggle_pause(), speller_text.RESUME)
        self._tick()
        self.assertFalse(self.panel.paused)
        self.assertIn('pause', self.panel.pause_text.get())
        self.assertEqual([(e.type, str(e.value)) for e in reader.new_events()],
                         [(speller_text.CONTROL_EVENT, 'pause'),
                          (speller_text.CONTROL_EVENT, 'resume')])

    def test_the_stop_button_ends_the_block(self):
        self.panel.toggle_pause()
        self._tick()
        self.panel.stop_block()
        self._tick()
        self.assertFalse(self.panel.paused)      # a stop clears the pause too
        self.assertIn('stopped', self.panel.status.get())

    def test_starting_a_phase_clears_a_pause(self):
        self.panel.toggle_pause()
        self._tick()
        self.assertTrue(self.panel.paused)
        self.panel.send_phase('calibrate')
        self.assertFalse(self.panel.paused)

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
