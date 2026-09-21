"""Correcting the text when the speller gets a letter wrong.

Two routes, and they must agree: the user selects DEL in the matrix like any
other key, or somebody else (the control panel's backspace button, a carer's
keyboard, another client) sends a speller.edit event.
"""
import threading
import unittest

from pyspeller.buffer import BufferClient, BufferServer
from pyspeller.clock import Clock
from pyspeller.config import SYMBOLS_6X6_CONTROL, SpellerConfig
from pyspeller.speller import text as speller_text
from pyspeller.speller.matrix import SpellerMatrix
from pyspeller.speller.render import HeadlessRenderer
from pyspeller.speller.stimulus import SpellerStimulus


class TestCorrection(unittest.TestCase):
    def setUp(self):
        self.server = BufferServer(port=0).start()
        self.config = SpellerConfig(port=self.server.port,
                                    symbols=SYMBOLS_6X6_CONTROL)
        self.client = BufferClient(port=self.server.port).connect()
        self.client.put_header(self.config.n_channels, self.config.fsample,
                               labels=list(self.config.channels))
        self.client.reset_event_cursor()
        self.other = BufferClient(port=self.server.port).connect()
        self.renderer = HeadlessRenderer(SpellerMatrix(self.config.symbols))
        self.stimulus = SpellerStimulus(self.client, self.config, self.renderer,
                                        Clock(1.0))
        self.addCleanup(self.server.stop)
        self.addCleanup(self.client.disconnect)
        self.addCleanup(self.other.disconnect)

    def test_the_default_matrix_has_a_backspace_key(self):
        symbols = [s for row in SpellerConfig().symbols for s in row]
        self.assertIn(speller_text.DELETE, symbols)
        self.assertIn(speller_text.SPACE, symbols)

    def test_selecting_del_in_the_matrix_rubs_out_the_last_letter(self):
        """DEL is a cell like any other: decoding it edits the text."""
        self.stimulus.spelled = speller_text.spell('BCX')
        self.stimulus.spelled = speller_text.apply_symbol(
            self.stimulus.spelled, speller_text.DELETE)
        self.assertEqual(self.stimulus.spelled, 'BC')

    def test_apply_edit_backspaces_and_shows_the_result(self):
        self.stimulus.spelled = 'BCX'
        self.assertEqual(self.stimulus.apply_edit(speller_text.DELETE), 'BC')
        self.assertEqual(self.renderer.output, 'BC')
        self.assertEqual(self.stimulus.apply_edit(speller_text.CLEAR), '')
        self.assertEqual(self.renderer.output, '')

    def test_an_edit_event_from_another_client_is_applied(self):
        self.stimulus.spelled = 'HELLOX'
        self.other.send_event(speller_text.EDIT_EVENT, speller_text.DELETE)
        self.assertEqual(self.stimulus.drain_edits(), 1)
        self.assertEqual(self.stimulus.spelled, 'HELLO')
        self.assertEqual(self.renderer.output, 'HELLO')

    def test_a_correction_is_applied_while_waiting_for_the_next_letter(self):
        self.stimulus.spelled = 'BCX'

        def correct_then_decode():
            self.other.send_event(speller_text.EDIT_EVENT, speller_text.DELETE)
            self.other.send_event('classifier.prediction', 'I')

        threading.Timer(0.1, correct_then_decode).start()
        prediction = self.stimulus._await_prediction(timeout=5.0)
        self.assertEqual(prediction, 'I')
        self.assertEqual(self.stimulus.spelled, 'BC')     # the edit went through

    def test_waiting_still_times_out_when_only_edits_arrive(self):
        self.other.send_event(speller_text.EDIT_EVENT, speller_text.DELETE)
        self.assertIsNone(self.stimulus._await_prediction(timeout=0.5))


if __name__ == '__main__':
    unittest.main()


class TestSpellableLetters(unittest.TestCase):
    """A run that cannot be spelled must fail loudly, before it starts."""

    def setUp(self):
        self.server = BufferServer(port=0).start()
        self.config = SpellerConfig(port=self.server.port,
                                    symbols=(('A', 'B', 'C'),
                                             ('D', 'E', 'F'),
                                             ('G', 'H', 'I')))
        self.client = BufferClient(port=self.server.port).connect()
        self.client.put_header(self.config.n_channels, self.config.fsample)
        self.stimulus = SpellerStimulus(
            self.client, self.config,
            HeadlessRenderer(SpellerMatrix(self.config.symbols)), Clock(1.0))
        self.addCleanup(self.server.stop)
        self.addCleanup(self.client.disconnect)

    def test_a_letter_outside_the_grid_is_reported(self):
        with self.assertRaises(ValueError) as caught:
            self.stimulus.run_calibration('BRAIN')
        self.assertIn("'R'", str(caught.exception))
        self.assertIn('3x3', str(caught.exception))

    def test_letters_in_the_grid_are_accepted(self):
        self.assertEqual(self.stimulus.check_spellable('BAD'), ['B', 'A', 'D'])
