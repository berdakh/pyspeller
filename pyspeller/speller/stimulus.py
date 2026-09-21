"""The stimulus presentation client: flashes rows/columns and sends events.

This is the only component that knows about time and the screen.  It publishes
what it did as buffer events, which is what lets the signal processing client
(and the simulated subject) stay completely independent of it:

    stimulus.rowFlash / stimulus.colFlash   value = index of the flashed group
    stimulus.tgtFlash                       value = 1/0, only during calibration
    stimulus.sequence  = end                one letter's flashes are finished
    stimulus.training  = start / end        a calibration run starts / ends
    stimulus.feedback  = start / end        a feedback run starts / ends
"""
import random

from ..buffer.protocol import Event
from ..clock import Clock
from ..speller.matrix import ROW, SpellerMatrix

PHASE_EVENT = 'startPhase.cmd'


class SpellerStimulus:
    """Runs calibration and feedback letters on a renderer."""

    def __init__(self, client, config, renderer, clock=None, rng=None):
        self.client = client
        self.config = config
        self.matrix = SpellerMatrix(config.symbols)
        self.renderer = renderer
        self.clock = clock or Clock(config.speed)
        self.rng = rng or random.Random(config.seed)
        self.predictions = []

    # -- one letter --------------------------------------------------------
    def flash_letter(self, target=None):
        """Flash every group `n_repetitions` times; labels the flashes if target."""
        config = self.config
        sequence = self.matrix.flash_sequence(config.n_repetitions, self.rng,
                                              config.min_gap)
        start = self.clock.now()
        for i, group in enumerate(sequence):
            onset = start + i * config.isi
            self.clock.sleep_until(onset)
            self._send_flash(group, target)
            self.renderer.draw(self.matrix.cells_of(group), 'flash')
            self.clock.sleep_until(onset + config.stim_duration)
            self.renderer.draw((), 'idle')
        self.clock.sleep_until(start + len(sequence) * config.isi)
        self.client.send_event('stimulus.sequence', 'end')
        return sequence

    def _send_flash(self, group, target):
        kind, index = group
        events = [Event('stimulus.rowFlash' if kind == ROW else 'stimulus.colFlash',
                        int(index))]
        if target is not None:
            # the training label: did this flash illuminate the attended symbol?
            events.append(Event('stimulus.tgtFlash',
                                int(self.matrix.contains(group, target))))
        self.client.put_events(events)     # one request -> one sample stamp

    def cue(self, symbol):
        """Show which symbol to attend to, and tell the simulated subject."""
        self.client.send_event('simulation.target', symbol)
        self.renderer.message('look at: %s' % symbol)
        self.renderer.draw([self.matrix.position_of(symbol)], 'target')
        self.clock.sleep(self.config.cue_duration)
        self.renderer.draw((), 'idle')
        self.renderer.message('')

    # -- phases ------------------------------------------------------------
    def run_calibration(self, letters=None):
        letters = list(letters or self.config.calibration_letters)
        self.renderer.message('calibration: %s' % ' '.join(letters))
        self.client.send_event('stimulus.training', 'start')
        for symbol in letters:
            self.cue(symbol)
            self.flash_letter(target=symbol)
            self.clock.sleep(self.config.inter_seq_duration)
        self.client.send_event('stimulus.training', 'end')
        self.client.send_event('simulation.target', '')
        self.renderer.message('calibration done')
        return letters

    def run_practice(self, letters=None):
        """Same as calibration but without training labels -- just a rehearsal."""
        letters = list(letters or self.config.calibration_letters[:2])
        self.renderer.message('practice')
        for symbol in letters:
            self.cue(symbol)
            self.flash_letter(target=None)
            self.clock.sleep(self.config.inter_seq_duration)
        self.client.send_event('simulation.target', '')
        self.renderer.message('practice done')
        return letters

    def run_feedback(self, letters=None, prediction_timeout=10.0):
        """Spell letters and show what the classifier decided for each."""
        letters = list(letters or self.config.feedback_letters)
        self.predictions = []
        self.client.send_event('stimulus.feedback', 'start')
        for symbol in letters:
            self.cue(symbol)
            self.flash_letter(target=None)
            prediction = self._await_prediction(prediction_timeout)
            self.predictions.append(prediction)
            if prediction is None:
                self.renderer.message('no prediction')
            else:
                self.renderer.message('predicted: %s' % prediction)
                self.renderer.draw([self.matrix.position_of(prediction)], 'prediction')
            self.clock.sleep(self.config.feedback_duration)
            self.renderer.draw((), 'idle')
            self.renderer.message('')
        self.client.send_event('stimulus.feedback', 'end')
        self.client.send_event('simulation.target', '')
        correct = sum(p == t for p, t in zip(self.predictions, letters))
        self.renderer.message('spelled %d/%d correctly' % (correct, len(letters)))
        return list(zip(letters, self.predictions))

    def _await_prediction(self, timeout):
        evt = self.client.wait_for_event('classifier.prediction',
                                         timeout=timeout / self.clock.speed)
        if evt is None:
            return None
        return evt.value if isinstance(evt.value, str) else str(evt.value)

    # -- event driven control ---------------------------------------------
    def run_phase_loop(self, stop_event=None):
        """Obey startPhase.cmd events until told to quit (the GUI drives this)."""
        self.client.reset_event_cursor()
        while stop_event is None or not stop_event.is_set():
            evt = self.client.wait_for_event(PHASE_EVENT, timeout=0.5)
            if evt is None:
                continue
            phase = str(evt.value)
            if phase == 'quit':
                break
            if phase in ('calibrate', 'calibration'):
                self.run_calibration()
            elif phase == 'practice':
                self.run_practice()
            elif phase in ('feedback', 'testing'):
                self.run_feedback()
        self.renderer.close()
