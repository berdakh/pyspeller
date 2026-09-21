"""Pausing, stopping, and switching phase while a block is running."""
import threading
import time
import unittest

from pyspeller.buffer import BufferClient, BufferServer
from pyspeller.clock import Clock
from pyspeller.config import SYMBOLS_3X3, SpellerConfig
from pyspeller.speller import text as speller_text
from pyspeller.speller.matrix import SpellerMatrix
from pyspeller.speller.render import HeadlessRenderer
from pyspeller.speller.stimulus import SpellerStimulus

FLASHES = ('stimulus.rowFlash', 'stimulus.colFlash')


class ControlTestCase(unittest.TestCase):
    def setUp(self):
        self.server = BufferServer(port=0).start()
        self.config = SpellerConfig(
            port=self.server.port, symbols=SYMBOLS_3X3, speed=5.0,
            n_repetitions=20, cue_duration=0.2, inter_seq_duration=0.2,
            feedback_duration=0.2, calibration_letters=('A', 'B'),
            feedback_letters=('A',))
        self.client = BufferClient(port=self.server.port).connect()
        self.client.put_header(self.config.n_channels, self.config.fsample)
        self.operator = BufferClient(port=self.server.port).connect()
        self.operator.reset_event_cursor()
        self.renderer = HeadlessRenderer(SpellerMatrix(self.config.symbols))
        self.stimulus = SpellerStimulus(self.client, self.config, self.renderer,
                                        Clock(self.config.speed))
        self.addCleanup(self.server.stop)
        self.addCleanup(self.client.disconnect)
        self.addCleanup(self.operator.disconnect)

    def flashes_so_far(self):
        return len([e for e in self.operator.get_events() if e.type in FLASHES])

    def wait_for_flashes(self, at_least, timeout=10.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.flashes_so_far() >= at_least:
                return True
            time.sleep(0.05)
        self.fail('only %d flashes after %gs' % (self.flashes_so_far(), timeout))

    def events_of_type(self, type_name):
        return [e for e in self.operator.get_events() if e.type == type_name]


class TestPause(ControlTestCase):
    def test_pause_holds_the_flashing_and_resume_carries_on(self):
        worker = threading.Thread(target=self.stimulus.run_calibration, daemon=True)
        worker.start()
        self.wait_for_flashes(3)

        self.operator.send_event(speller_text.CONTROL_EVENT, speller_text.PAUSE)
        time.sleep(0.4)                       # let the pause take effect
        held = self.flashes_so_far()
        time.sleep(0.6)
        self.assertEqual(self.flashes_so_far(), held, 'flashing went on while paused')
        self.assertTrue(self.stimulus.paused)
        self.assertIn('paused', self.renderer.messages)

        self.operator.send_event(speller_text.CONTROL_EVENT, speller_text.RESUME)
        self.wait_for_flashes(held + 3)
        self.assertFalse(self.stimulus.paused)

        self.operator.send_event(speller_text.CONTROL_EVENT, speller_text.STOP)
        worker.join(timeout=10)
        self.assertFalse(worker.is_alive())

    def test_a_pause_does_not_bunch_the_flashes_up_afterwards(self):
        """The paused time is given back, so the rhythm survives the pause."""
        def flash_until_stopped():
            from pyspeller.speller.stimulus import RunStopped
            try:
                self.stimulus.flash_letter()
            except RunStopped:
                pass

        worker = threading.Thread(target=flash_until_stopped, daemon=True)
        worker.start()
        self.wait_for_flashes(3)
        self.operator.send_event(speller_text.CONTROL_EVENT, speller_text.PAUSE)
        time.sleep(0.5)
        self.operator.send_event(speller_text.CONTROL_EVENT, speller_text.RESUME)
        self.wait_for_flashes(12)
        self.operator.send_event(speller_text.CONTROL_EVENT, speller_text.STOP)
        worker.join(timeout=10)

        samples = [e.sample for e in self.operator.get_events() if e.type in FLASHES]
        gaps = [b - a for a, b in zip(samples, samples[1:])]
        expected = self.config.isi * self.config.fsample
        # every gap is one inter-stimulus interval; none is the pause itself
        self.assertLess(max(gaps), expected * 3,
                        'flashes bunched up after the pause: %s' % gaps)


class TestStop(ControlTestCase):
    def test_stop_ends_the_block_and_still_closes_it_off(self):
        worker = threading.Thread(target=self.stimulus.run_calibration, daemon=True)
        worker.start()
        self.wait_for_flashes(3)
        self.operator.send_event(speller_text.CONTROL_EVENT, speller_text.STOP)
        worker.join(timeout=10)
        self.assertFalse(worker.is_alive(), 'the block did not stop')

        # the analysis client must not be left waiting for data
        training = self.events_of_type('stimulus.training')
        self.assertEqual([str(e.value) for e in training], ['start', 'end'])
        self.assertIn('end', [str(e.value)
                              for e in self.events_of_type('stimulus.sequence')])
        self.assertFalse(self.stimulus.stopped)      # cleared for the next block

    def test_stopping_a_feedback_block_closes_it_off_too(self):
        worker = threading.Thread(target=self.stimulus.run_feedback, daemon=True)
        worker.start()
        self.wait_for_flashes(3)
        self.operator.send_event(speller_text.CONTROL_EVENT, speller_text.STOP)
        worker.join(timeout=10)
        self.assertEqual([str(e.value) for e in self.events_of_type('stimulus.feedback')],
                         ['start', 'end'])


class TestPhaseSwitching(ControlTestCase):
    def test_a_new_phase_interrupts_the_running_one(self):
        stop = threading.Event()
        worker = threading.Thread(target=self.stimulus.run_phase_loop, args=(stop,),
                                  daemon=True)
        worker.start()
        self.addCleanup(stop.set)

        self.operator.send_event('startPhase.cmd', 'practice')
        self.wait_for_flashes(3)
        self.assertIn('practice', self.renderer.messages)

        # pressing calibrate during practice: no need to stop it first
        self.operator.send_event('startPhase.cmd', 'calibrate')
        deadline = time.time() + 10
        while time.time() < deadline and not self.events_of_type('stimulus.training'):
            time.sleep(0.05)
        self.assertTrue(self.events_of_type('stimulus.training'),
                        'calibration never started')
        self.assertEqual(str(self.events_of_type('stimulus.training')[0].value),
                         'start')

        self.operator.send_event('startPhase.cmd', 'quit')
        worker.join(timeout=10)
        self.assertFalse(worker.is_alive())

    def test_quitting_during_a_block_leaves_the_loop(self):
        stop = threading.Event()
        worker = threading.Thread(target=self.stimulus.run_phase_loop, args=(stop,),
                                  daemon=True)
        worker.start()
        self.addCleanup(stop.set)
        self.operator.send_event('startPhase.cmd', 'practice')
        self.wait_for_flashes(3)
        self.operator.send_event('startPhase.cmd', 'quit')
        worker.join(timeout=10)
        self.assertFalse(worker.is_alive())


if __name__ == '__main__':
    unittest.main()
