"""Smoke tests for the tk control panel.

They need a display, so they skip on a headless machine (use xvfb to run them
in CI: `xvfb-run python -m unittest tests.test_gui`).
"""
import unittest

import numpy as np

from pyspeller.buffer import BufferClient, BufferServer
from pyspeller.config import SpellerConfig
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

    def test_speller_window_draws_the_matrix(self):
        from pyspeller.speller.render import TkRenderer
        renderer = TkRenderer(SpellerMatrix(self.config.symbols),
                              master=self.panel.root)
        self.addCleanup(renderer.root.destroy)
        renderer.draw([(0, 0), (0, 1), (0, 2)], 'flash')
        renderer.message('look at: A')
        renderer.pump()
        self.assertEqual(renderer.canvas.itemcget(renderer._items[(0, 0)], 'fill'),
                         '#ffffff')
        self.assertEqual(renderer.canvas.itemcget(renderer._items[(1, 0)], 'fill'),
                         '#808080')


if __name__ == '__main__':
    unittest.main()
