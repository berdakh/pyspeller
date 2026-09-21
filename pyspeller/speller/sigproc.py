"""The online signal processing client.

It listens for phase commands, gathers epochs around flash events, trains the
ERP classifier on the calibration data, and during feedback accumulates
classifier output per row/column until a letter's flashes are over -- then puts
the decoded symbol back into the buffer as classifier.prediction.
"""
import collections
import os

import numpy as np

from ..acquisition.saver import save_epochs
from ..signalproc.classifier import ERPClassifier
from ..signalproc.epochs import EpochGatherer
from ..speller.matrix import COL, ROW, SpellerMatrix

PHASE_EVENT = 'startPhase.cmd'
FLASH_EVENTS = ('stimulus.rowFlash', 'stimulus.colFlash')


class SignalProcessor:
    """Calibrate -> train -> apply, all driven by buffer events."""

    def __init__(self, client, config, verbose=True, save_dir=None):
        self.client = client
        self.config = config
        self.matrix = SpellerMatrix(config.symbols)
        self.verbose = verbose
        self.save_dir = save_dir      # where calibration epochs and models go
        self.classifier = None
        self.calibration = None        # (epochs, labels) from the last calibration
        self.training_report = None
        self.trlen_samples = client.samples_for(config.trlen_ms)

    # -- calibration -------------------------------------------------------
    def gather_calibration(self, timeout=600.0):
        """Collect labelled epochs until the stimulus client says training ended."""
        gatherer = EpochGatherer(self.client, 'stimulus.tgtFlash', self.trlen_samples)
        epochs, events, _ = gatherer.gather(
            stop_types=[('stimulus.training', 'end')],
            timeout=timeout / self.client_speed)
        labels = np.array([int(e.value) for e in events], dtype=int)
        self.calibration = (epochs, labels)
        self._log('gathered %d epochs (%d target, %d non-target)'
                  % (len(labels), int((labels == 1).sum()), int((labels == 0).sum())))
        if self.save_dir and len(labels):
            path = save_epochs(
                os.path.join(self.save_dir, 'calibration_epochs.npz'),
                epochs, labels, events,
                metadata={'fsample': self.client.fsample,
                          'channels': list(self.config.channels),
                          'trlen_ms': self.config.trlen_ms})
            self._log('saved the calibration epochs to %s' % path)
        return epochs, labels

    @property
    def client_speed(self):
        return getattr(self.config, 'speed', 1.0)

    # -- training ----------------------------------------------------------
    def train(self, epochs=None, labels=None, cross_validate=True):
        if epochs is None:
            if self.calibration is None:
                raise RuntimeError('no calibration data to train on')
            epochs, labels = self.calibration
        if len(np.unique(labels)) < 2:
            raise RuntimeError('calibration data has only one class')
        config = self.config
        self.classifier = ERPClassifier(self.client.fsample, config.freq_band,
                                        config.analysis_fsample,
                                        config.regularisation,
                                        channels=list(config.channels),
                                        spatial_filter=config.spatial_filter)
        self.classifier.fit(epochs, labels, verbose=self.verbose)
        report = {'n_epochs': int(len(labels)), 'n_targets': int((labels == 1).sum())}
        if cross_validate and min(np.bincount(labels)) >= 5:
            report['auc'], report['accuracy'] = self.classifier.cross_validate(
                epochs, labels)
            self._log('classifier trained: cross-validated AUC %.3f, accuracy %.2f'
                      % (report['auc'], report['accuracy']))
        else:
            self._log('classifier trained on %d epochs' % len(labels))
        self.training_report = report
        if self.save_dir:
            path = self.classifier.save(os.path.join(self.save_dir, 'classifier.pkl'))
            self._log('saved the classifier to %s' % path)
        self.client.send_event('sigproc.training', 'done')
        return report

    # -- feedback ----------------------------------------------------------
    def run_feedback_letter(self, timeout=60.0):
        """Score one letter's flashes and publish the decoded symbol."""
        if self.classifier is None:
            raise RuntimeError('no trained classifier')
        scores = collections.defaultdict(float)
        counts = collections.defaultdict(int)

        def score(epoch, event):
            kind = ROW if event.type == 'stimulus.rowFlash' else COL
            group = (kind, int(event.value))
            scores[group] += float(self.classifier.decision_function(epoch[None])[0])
            counts[group] += 1

        gatherer = EpochGatherer(self.client, list(FLASH_EVENTS), self.trlen_samples)
        _, events, stop = gatherer.gather(
            stop_types=[('stimulus.sequence', 'end'), ('stimulus.feedback', 'end')],
            timeout=timeout / self.client_speed, on_epoch=score)
        if not events:
            return None, dict(scores)
        if stop is not None and stop.type == 'stimulus.feedback' and str(stop.value) == 'end':
            return None, dict(scores)
        # average so groups flashed a different number of times stay comparable
        mean_scores = {g: scores[g] / max(1, counts[g]) for g in scores}
        symbol, _ = self.matrix.decode(mean_scores)
        self.client.send_event('classifier.prediction', symbol)
        self._log('predicted %r from %d flashes' % (symbol, len(events)))
        return symbol, mean_scores

    def run_feedback(self, n_letters=None, timeout=60.0):
        predictions = []
        while n_letters is None or len(predictions) < n_letters:
            symbol, _ = self.run_feedback_letter(timeout=timeout)
            if symbol is None:
                break
            predictions.append(symbol)
        return predictions

    # -- event driven control ---------------------------------------------
    def run_phase_loop(self, stop_event=None, model_path=None):
        """The counterpart of SpellerStimulus.run_phase_loop, for the GUI."""
        self.client.reset_event_cursor()
        while stop_event is None or not stop_event.is_set():
            evt = self.client.wait_for_event(PHASE_EVENT, timeout=0.5)
            if evt is None:
                continue
            phase = str(evt.value)
            if phase == 'quit':
                break
            try:
                if phase in ('calibrate', 'calibration'):
                    self.gather_calibration()
                elif phase in ('train', 'trainerp'):
                    self.train()
                    if model_path:
                        self.classifier.save(model_path)
                elif phase in ('feedback', 'testing'):
                    self.run_feedback()
            except Exception as err:                  # keep the client alive
                self._log('phase %r failed: %s' % (phase, err))
                self.client.send_event('sigproc.error', str(err))

    def _log(self, message):
        if self.verbose:
            print('[sigproc] %s' % message, flush=True)
