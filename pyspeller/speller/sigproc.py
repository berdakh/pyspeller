"""The online signal processing client.

It listens for phase commands, gathers epochs around flash events, trains the
ERP classifier on the calibration data, and during feedback accumulates
classifier output per row/column until a letter's flashes are over -- then puts
the decoded symbol back into the buffer as classifier.prediction.
"""
import collections
import json
import os

import numpy as np

from ..acquisition.saver import save_epochs
from ..signalproc.classifier import ERPClassifier
from ..signalproc.epochs import EpochGatherer
from ..speller.matrix import COL, ROW, SpellerMatrix

PHASE_EVENT = 'startPhase.cmd'
READY_EVENT = 'speller.ready'
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
        self.next_phase = None         # a phase asked for while a block was running
        self.calibration = None        # (epochs, labels) from the last calibration
        self.training_report = None
        self.trlen_samples = client.samples_for(config.trlen_ms)

    # -- calibration -------------------------------------------------------
    def gather_calibration(self, timeout=600.0):
        """Collect labelled epochs until the stimulus client says training ended."""
        gatherer = EpochGatherer(self.client, 'stimulus.tgtFlash', self.trlen_samples)
        epochs, events, stop = gatherer.gather(
            stop_types=[('stimulus.training', 'end'), PHASE_EVENT],
            timeout=timeout / self.client_speed)
        self._note_phase(stop)
        labels = np.array([int(e.value) for e in events], dtype=int)
        self.calibration = (epochs, labels)
        self._log('gathered %d epochs (%d target, %d non-target)'
                  % (len(labels), int((labels == 1).sum()), int((labels == 0).sum())))
        if self.save_dir and len(labels):
            path = save_epochs(
                os.path.join(self.save_dir, 'calibration_epochs.npz'),
                epochs, labels, events,
                metadata={'fsample': self.client.fsample,
                          'channels': self.channel_names,
                          'trlen_ms': self.config.trlen_ms})
            self._log('saved the calibration epochs to %s' % path)
        return epochs, labels

    @property
    def client_speed(self):
        return getattr(self.config, 'speed', 1.0)

    @property
    def channel_names(self):
        """The montage the amplifier reports, or the configured one."""
        header = self.client.header
        if header is not None and header.labels:
            return list(header.labels)
        return list(self.config.channels)

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
                                        channels=self.channel_names,
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
        try:
            self.publish_training_summary(epochs, labels, report)
        except Exception as err:                  # a picture is not worth a crash
            self._log('could not summarise the training: %s' % err)
        if self.save_dir:
            path = self.classifier.save(os.path.join(self.save_dir, 'classifier.pkl'))
            self._log('saved the classifier to %s' % path)
        self.client.send_event('sigproc.training', 'done')
        return report

    def training_summary(self, epochs, labels, report=None):
        """Everything worth showing after training, as plain lists and numbers.

        The same things the matlab side plots: the two class averages, where
        the classes differ in space and time, the confusion matrix, and the
        cross-validated scores.
        """
        from ..signalproc.classifier import auc
        labels = np.asarray(labels).astype(int)
        clf = self.classifier
        processed = clf.preprocess(epochs)
        times = np.linspace(0, self.config.trlen_ms, processed.shape[2]).tolist()
        summary = {
            'channels': [clf.channel_name(c) for c in range(processed.shape[1])],
            'bad_channels': [clf.channel_name(c) for c in clf.bad_channels],
            'times_ms': times,
            'erp_target': processed[labels == 1].mean(axis=0).tolist(),
            'erp_nontarget': processed[labels == 0].mean(axis=0).tolist(),
            'discriminability': clf.discriminability(epochs, labels).tolist(),
            'n_epochs': int(len(labels)),
            'n_targets': int((labels == 1).sum()),
        }
        scores = clf.cross_validated_scores(epochs, labels)
        predicted = (scores > 0).astype(int)
        summary['auc'] = float(auc(labels, scores))
        summary['accuracy'] = float((predicted == labels).mean())
        summary['confusion'] = [
            [int(((labels == actual) & (predicted == guess)).sum())
             for guess in (0, 1)] for actual in (0, 1)]
        if report:
            summary['report'] = {k: float(v) for k, v in report.items()}
        return summary

    def publish_training_summary(self, epochs, labels, report=None):
        """Send the summary to whoever is watching, and keep a copy on disk."""
        summary = self.training_summary(epochs, labels, report)
        self.client.send_event('classifier.summary', json.dumps(summary))
        if self.save_dir:
            path = os.path.join(self.save_dir, 'training_summary.json')
            with open(path, 'w') as handle:
                json.dump(summary, handle)
            self._log('saved the training summary to %s' % path)
        return summary

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
            stop_types=[('stimulus.sequence', 'end'), ('stimulus.feedback', 'end'),
                        PHASE_EVENT],
            timeout=timeout / self.client_speed, on_epoch=score)
        self._note_phase(stop)
        if self.next_phase:
            return None, dict(scores)
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
            if symbol is None or self.next_phase:
                break
            predictions.append(symbol)
        return predictions

    def _note_phase(self, stop_event):
        """Remember a phase command that arrived while we were gathering."""
        if stop_event is not None and stop_event.type == PHASE_EVENT:
            self.next_phase = str(stop_event.value)
        return self.next_phase

    # -- event driven control ---------------------------------------------
    def run_phase_loop(self, stop_event=None, model_path=None):
        """The counterpart of SpellerStimulus.run_phase_loop, for the GUI.

        Like the stimulus, a phase asked for while this one is gathering data
        interrupts it, so the operator can switch blocks at any time.
        """
        self.client.reset_event_cursor()
        self.client.send_event(READY_EVENT, 'sigproc')
        phase = None
        while stop_event is None or not stop_event.is_set():
            try:
                if phase is None:
                    evt = self.client.wait_for_event(PHASE_EVENT, timeout=0.5)
                    if evt is None:
                        continue
                    phase = str(evt.value)
            except (OSError, IOError, ConnectionError):
                break                  # the buffer went away: the session ended
            if phase == 'quit':
                break
            self.next_phase = None
            try:
                if phase in ('calibrate', 'calibration'):
                    self.gather_calibration()
                elif phase in ('train', 'trainerp'):
                    self.train()
                    if model_path:
                        self.classifier.save(model_path)
                elif phase in ('feedback', 'testing', 'free', 'freespelling'):
                    self.run_feedback()
            except Exception as err:                  # keep the client alive
                self._log('phase %r failed: %s' % (phase, err))
                self.client.send_event('sigproc.error', str(err))
            phase, self.next_phase = self.next_phase, None

    def _log(self, message):
        if self.verbose:
            print('[sigproc] %s' % message, flush=True)
