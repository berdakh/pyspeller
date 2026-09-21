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
import time

from ..buffer.protocol import Event
from ..clock import Clock
from ..speller.matrix import ROW, SpellerMatrix
from . import text as speller_text

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
        self.spelled = ''        # the letters decoded so far, as shown on screen

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

    def check_spellable(self, letters):
        """Raise before a run starts if the matrix cannot spell these letters."""
        missing = [l for l in letters
                   if l not in {s for row in self.matrix.symbols for s in row}]
        if missing:
            raise ValueError('the %dx%d speller matrix has no %s'
                             % (self.matrix.n_rows, self.matrix.n_cols,
                                ', '.join(repr(m) for m in missing)))
        return list(letters)

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
        letters = self.check_spellable(letters or self.config.calibration_letters)
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
        letters = self.check_spellable(letters or self.config.calibration_letters[:2])
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
        letters = self.check_spellable(letters or self.config.feedback_letters)
        self.predictions = []
        self.spelled = ''
        self.renderer.set_output(self.spelled)
        self.client.send_event('stimulus.feedback', 'start')
        for symbol in letters:
            self.drain_edits()
            self.cue(symbol)
            self.flash_letter(target=None)
            prediction = self._await_prediction(prediction_timeout)
            self.predictions.append(prediction)
            if prediction is None:
                self.renderer.message('no prediction')
            else:
                # the decoded letter: highlighted in the grid and applied to
                # the text field, so the user sees what they have typed
                self.spelled = speller_text.apply_symbol(self.spelled, prediction)
                self.renderer.set_output(self.spelled)
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

    def run_free_spelling(self, n_letters=None, prediction_timeout=10.0,
                          stop_event=None):
        """Spell without a cue -- the mode a user actually works in.

        Nothing tells the speller what the user is attending to, so there is no
        target to show and nothing to score: letters simply appear in the text
        field as the classifier decides them.  The run ends after `n_letters`
        or when `stop_event` is set.
        """
        n_letters = n_letters or self.config.free_spelling_letters
        self.predictions = []
        self.spelled = ''
        self.renderer.set_output(self.spelled)
        self.renderer.message('free spelling')
        self.client.send_event('stimulus.feedback', 'start')
        while len(self.predictions) < n_letters:
            if stop_event is not None and stop_event.is_set():
                break
            self.drain_edits()
            self.clock.sleep(self.config.inter_seq_duration)
            self.flash_letter(target=None)
            prediction = self._await_prediction(prediction_timeout)
            self.predictions.append(prediction)
            if prediction is not None:
                self.spelled = speller_text.apply_symbol(self.spelled, prediction)
                self.renderer.set_output(self.spelled)
                self.renderer.draw([self.matrix.position_of(prediction)], 'prediction')
                self.clock.sleep(self.config.feedback_duration)
                self.renderer.draw((), 'idle')
        self.client.send_event('stimulus.feedback', 'end')
        self.renderer.message('typed: %s' % self.spelled)
        return self.spelled

    def _await_prediction(self, timeout):
        """The next decoded letter, applying any corrections that arrive first.

        This one waits in wall-clock time: the classifier takes as long as the
        machine takes, whatever factor experiment time is running at.
        """
        deadline = time.time() + timeout
        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                return None
            evt = self.client.wait_for_event(
                ['classifier.prediction', speller_text.EDIT_EVENT],
                timeout=remaining)
            if evt is None:
                return None
            if evt.type == speller_text.EDIT_EVENT:
                self.apply_edit(evt.value)
                continue
            return evt.value if isinstance(evt.value, str) else str(evt.value)

    def apply_edit(self, symbol=speller_text.DELETE):
        """Correct the text field: DEL rubs out the last letter, CLR the line.

        The user can select DEL in the matrix like any other key; this is the
        same edit arriving from somewhere else -- the control panel's backspace
        button, or any client that sends a speller.edit event.
        """
        symbol = str(symbol or speller_text.DELETE)
        self.spelled = speller_text.apply_symbol(self.spelled, symbol)
        self.renderer.set_output(self.spelled)
        return self.spelled

    def drain_edits(self):
        """Apply any corrections waiting in the event stream; returns how many."""
        applied = 0
        for evt in self.client.new_events(timeout_ms=0):
            if evt.type == speller_text.EDIT_EVENT:
                self.apply_edit(evt.value)
                applied += 1
        return applied

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
            elif phase in ('free', 'freespelling'):
                self.run_free_spelling(stop_event=stop_event)
        self.renderer.close()
