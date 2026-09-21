"""Wiring the components together into a runnable experiment.

The framework is a set of independent clients around a buffer, and normally
each runs in its own process.  For the demo and the tests it is convenient to
run them as threads in one process, which is what this module does.
"""
import threading

import numpy as np

from .acquisition.saver import BufferSaver
from .acquisition.simulator import EEGSimulator
from .buffer.client import BufferClient
from .buffer.server import BufferServer
from .clock import BufferClock, Clock
from .config import SpellerConfig
from .speller.matrix import SpellerMatrix
from .speller.render import make_renderer
from .speller.sigproc import SignalProcessor
from .speller.stimulus import SpellerStimulus


class LocalExperiment:
    """Buffer + simulated amplifier + stimulus + signal processing, in one process."""

    def __init__(self, config=None, renderer='headless', erp_amplitude=8.0,
                 noise_amplitude=10.0, verbose=True, save_dir=None):
        self.config = config or SpellerConfig()
        self.verbose = verbose
        self.save_dir = save_dir
        self.saver = None
        self.erp_amplitude = erp_amplitude
        self.noise_amplitude = noise_amplitude
        self.renderer_kind = renderer
        self.server = None
        self.simulator = None
        self.stimulus = None
        self.processor = None
        self.clock = Clock(self.config.speed)

    # -- lifecycle ---------------------------------------------------------
    def start(self):
        self.server = BufferServer(self.config.host, self.config.port).start()
        self.config.port = self.server.port          # resolves port=0
        self.simulator = EEGSimulator(self.config, self.clock,
                                      erp_amplitude=self.erp_amplitude,
                                      noise_amplitude=self.noise_amplitude).start()

        stim_client = BufferClient(self.config.host, self.config.port).connect(retries=20)
        stim_client.wait_for_header()
        # pace the stimulus on the sample counter, so a sped-up run stays exact
        stim_clock = BufferClock(stim_client, self.config.fsample, self.config.speed)
        proc_client = BufferClient(self.config.host, self.config.port).connect(retries=20)
        proc_client.wait_for_header()

        renderer = make_renderer(self.renderer_kind,
                                 SpellerMatrix(self.config.symbols))
        self.stimulus = SpellerStimulus(stim_client, self.config, renderer, stim_clock)
        self.processor = SignalProcessor(proc_client, self.config,
                                         verbose=self.verbose,
                                         save_dir=self.save_dir)
        if self.save_dir:
            self.saver = BufferSaver(self.config.host, self.config.port,
                                     directory=self.save_dir,
                                     verbose=self.verbose).start()
        return self

    def stop(self):
        for component in (self.saver, self.simulator):
            if component is not None:
                component.stop()
        for client in (getattr(self.stimulus, 'client', None),
                       getattr(self.processor, 'client', None)):
            if client is not None:
                client.disconnect()
        if self.server is not None:
            self.server.stop()

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()

    # -- phases ------------------------------------------------------------
    def calibrate(self, letters=None):
        """Run a calibration block; returns (epochs, labels)."""
        self.stimulus.check_spellable(letters or self.config.calibration_letters)
        self.processor.client.reset_event_cursor()
        failure = {}
        worker = threading.Thread(
            target=_guard(self.stimulus.run_calibration, failure, letters),
            name='stimulus-calibration', daemon=True)
        worker.start()
        epochs, labels = self.processor.gather_calibration()
        worker.join()
        if failure:
            raise failure['error']
        return epochs, labels

    def train(self):
        return self.processor.train()

    def feedback(self, letters=None):
        """Run a feedback block; returns [(target, prediction), ...]."""
        letters = self.stimulus.check_spellable(
            letters or self.config.feedback_letters)
        self.processor.client.reset_event_cursor()
        result = {}
        worker = threading.Thread(
            target=lambda: result.update(pairs=self.stimulus.run_feedback(letters)),
            name='stimulus-feedback', daemon=True)
        worker.start()
        self.processor.run_feedback(n_letters=len(letters))
        worker.join()
        return result.get('pairs', [])


def run_demo(config=None, erp_amplitude=8.0, noise_amplitude=10.0,
             renderer='headless', verbose=True, save_dir=None):
    """Calibrate, train and spell -- the whole pipeline, end to end."""
    config = config or SpellerConfig()
    with LocalExperiment(config, renderer=renderer, erp_amplitude=erp_amplitude,
                         noise_amplitude=noise_amplitude, verbose=verbose,
                         save_dir=save_dir) as exp:
        if verbose:
            print('calibrating on %s ...' % ' '.join(config.calibration_letters))
        epochs, labels = exp.calibrate()
        report = exp.train()
        if verbose:
            print('spelling %s ...' % ' '.join(config.feedback_letters))
        pairs = exp.feedback()
        correct = sum(p == t for t, p in pairs)
        results = {'training': report, 'pairs': pairs,
                   'spelled': exp.stimulus.spelled, 'save_dir': save_dir,
                   'n_epochs': int(len(labels)),
                   'letter_accuracy': correct / max(1, len(pairs)),
                   'erp': target_vs_nontarget(epochs, labels)}
        if verbose:
            print('\nspelled: %s' % ' '.join(
                '%s->%s' % (t, p if p else '?') for t, p in pairs))
            print('typed: %r  (cued: %r)'
                  % (exp.stimulus.spelled, ''.join(config.feedback_letters)))
            print('letter accuracy: %d/%d' % (correct, len(pairs)))
        return results


def _guard(function, failure, *args):
    """Run `function` in a thread but keep its exception for the caller."""
    def wrapped():
        try:
            function(*args)
        except Exception as error:         # re-raised on the calling thread
            failure['error'] = error
    return wrapped


def target_vs_nontarget(epochs, labels):
    """Mean target and non-target ERP, for plotting or sanity checking."""
    epochs, labels = np.asarray(epochs), np.asarray(labels)
    return {'target': epochs[labels == 1].mean(axis=0) if (labels == 1).any() else None,
            'nontarget': epochs[labels == 0].mean(axis=0) if (labels == 0).any() else None}
