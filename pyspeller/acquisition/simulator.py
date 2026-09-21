"""A simulated EEG amplifier that reacts to the speller's flash events.

This is the stand-in for real hardware: it fills the buffer with plausible EEG
(1/f background, an alpha rhythm, a common mode shared by all electrodes and
the odd eye blink) and, whenever the stimulus client flashes a group that
contains the attended symbol, adds a P300 to the ongoing signal.
Every flash also gets a small visual evoked response, so the classifier has to
find the target/non-target difference rather than "flash vs nothing".
"""
import threading

import numpy as np

from ..buffer.client import BufferClient
from ..clock import Clock
from ..speller.matrix import COL, ROW, SpellerMatrix

TARGET_EVENT = 'simulation.target'     # tells the simulated subject what to attend
FLASH_EVENTS = ('stimulus.rowFlash', 'stimulus.colFlash')


class EEGSimulator:
    """Generates data into the buffer in (scaled) real time, in a thread."""

    def __init__(self, config, clock=None, erp_amplitude=8.0, noise_amplitude=10.0,
                 common_mode=0.6, blink_rate=0.1, seed=None, block_ms=40,
                 response_latency_ms=20.0, jitter_ms=8.0):
        self.config = config
        self.clock = clock or Clock(config.speed)
        self.matrix = SpellerMatrix(config.symbols)
        self.erp_amplitude = float(erp_amplitude)     # microvolt peak of the P300
        self.noise_amplitude = float(noise_amplitude) # microvolt std of the background
        self.common_mode = float(common_mode)         # fraction of noise shared by all channels
        self.blink_rate = float(blink_rate)           # eye blinks per second
        self.block_ms = float(block_ms)
        self.response_latency_ms = float(response_latency_ms)
        self.jitter_ms = float(jitter_ms)
        self.rng = np.random.default_rng(seed if seed is not None else config.seed)
        self.client = None
        self._thread = None
        self._running = False
        self._target = None
        self._pending = []        # [(onset_sample, [n_channels x n_samples] response)]
        self._written = 0
        self._ar_states = {}
        self._erp_cache = {}

    # -- lifecycle ---------------------------------------------------------
    def start(self):
        self.client = BufferClient(self.config.host, self.config.port).connect(retries=20)
        self.client.put_header(self.config.n_channels, self.config.fsample,
                               labels=list(self.config.channels))
        self.client.reset_event_cursor(0)
        self._running = True
        self._thread = threading.Thread(target=self._run, name='eeg-simulator',
                                        daemon=True)
        self._thread.start()
        return self

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=5.0)
        if self.client is not None:
            self.client.disconnect()

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()

    # -- acquisition loop --------------------------------------------------
    def _run(self):
        fs = self.config.fsample
        block = max(1, int(round(self.block_ms * fs / 1000.0)))
        next_deadline = self.block_ms / 1000.0
        while self._running:
            self.clock.sleep_until(next_deadline)
            next_deadline += self.block_ms / 1000.0
            due = int(self.clock.now() * fs) - self._written
            if due < block:
                continue
            try:
                self._handle_events()
                self.client.put_data(self._next_block(due).T.astype('float32'))
            except (OSError, IOError):
                break
            self._written += due

    def _handle_events(self):
        for evt in self.client.new_events(timeout_ms=0):
            if evt.type == TARGET_EVENT:
                self._target = evt.value or None
            elif evt.type in FLASH_EVENTS and self._target is not None:
                kind = ROW if evt.type == 'stimulus.rowFlash' else COL
                index = int(evt.value)
                is_target = self.matrix.contains((kind, index), self._target)
                self._schedule_response(evt.sample, is_target)

    def _schedule_response(self, sample, is_target):
        fs = self.config.fsample
        latency = self.response_latency_ms + self.rng.normal(0, self.jitter_ms)
        onset = int(sample + round(latency * fs / 1000.0))
        gain = self.rng.normal(1.0, 0.15)          # trial-to-trial variability
        self._pending.append((onset, gain * self._response(is_target)))

    def _response(self, is_target):
        """[n_channels x n_samples] evoked response, cached per condition."""
        if is_target in self._erp_cache:
            return self._erp_cache[is_target]
        fs = self.config.fsample
        t = np.arange(0, int(0.7 * fs)) / fs
        # early visual response to any flash, much the same at every electrode
        vep = -0.45 * _gaussian(t, 0.10, 0.03) + 0.6 * _gaussian(t, 0.17, 0.04)
        response = np.outer(np.ones(self.config.n_channels) * 0.5,
                            vep * self.erp_amplitude)
        if is_target:
            # P3b at ~320 ms, preceded by a small N200
            p300 = (_gaussian(t, 0.32, 0.075) - 0.25 * _gaussian(t, 0.20, 0.04))
            response = response + np.outer(self._channel_weights(),
                                           p300 * self.erp_amplitude)
        self._erp_cache[is_target] = response
        return response

    def _channel_weights(self):
        """P300 is centro-parietal: strongest at Pz/Cz, weak frontally."""
        topography = {'Pz': 1.0, 'Cz': 0.8, 'P3': 0.75, 'P4': 0.75, 'Fz': 0.2,
                      'C3': 0.45, 'C4': 0.45, 'Oz': 0.25}
        return np.array([topography.get(ch, 0.5) for ch in self.config.channels])

    # -- signal generation -------------------------------------------------
    def _next_block(self, nsamples):
        data = self._background(nsamples)
        start, end = self._written, self._written + nsamples
        still_pending = []
        for onset, response in self._pending:
            first = max(onset, start)
            last = min(onset + response.shape[1], end)
            if last > first:
                data[:, first - start:last - start] += response[:, first - onset:last - onset]
            if onset + response.shape[1] > end:
                still_pending.append((onset, response))
        self._pending = still_pending
        return data

    def _background(self, nsamples):
        """1/f-ish noise, an alpha rhythm, a shared common mode and blinks.

        Part of the noise is common to every electrode -- reference drift,
        muscle and eye activity all are -- which is exactly what the common
        average reference in the analysis pipeline is there to remove.
        """
        n_ch = self.config.n_channels
        shared = np.sqrt(self.common_mode)
        private = np.sqrt(1.0 - self.common_mode)

        local = self._ar_noise(n_ch, nsamples)
        common = np.repeat(self._ar_noise(1, nsamples), n_ch, axis=0)

        t = (np.arange(self._written, self._written + nsamples) / self.config.fsample)
        alpha = np.outer(self.rng.normal(0.5, 0.1, n_ch),
                         np.sin(2 * np.pi * 10.0 * t + self.rng.uniform(0, 2 * np.pi)))
        # AR(1) with a=0.92 has unit-innovation std ~2.6; scale to the wanted level
        raw = private * local + shared * (common + alpha)
        return (self.noise_amplitude / 2.6) * raw + self._blinks(nsamples)

    def _ar_noise(self, n_ch, nsamples):
        states = self._ar_states.setdefault(n_ch, self.rng.normal(0, 1, n_ch))
        out = np.empty((n_ch, nsamples))
        innovation = self.rng.normal(0, 1, (n_ch, nsamples))
        state = states
        for i in range(nsamples):
            state = 0.92 * state + innovation[:, i]
            out[:, i] = state
        self._ar_states[n_ch] = state
        return out

    def _blinks(self, nsamples):
        """Occasional large frontal deflections -- what artefact rejection is for."""
        out = np.zeros((self.config.n_channels, nsamples))
        if self.blink_rate <= 0:
            return out
        expected = self.blink_rate * nsamples / self.config.fsample
        weights = np.array([{'Fz': 1.0, 'Cz': 0.4, 'C3': 0.35, 'C4': 0.35}.get(ch, 0.15)
                            for ch in self.config.channels])
        for _ in range(self.rng.poisson(expected)):
            centre = self.rng.integers(0, nsamples)
            width = max(2, int(0.15 * self.config.fsample))
            idx = np.arange(nsamples)
            shape = np.exp(-0.5 * ((idx - centre) / (width / 2.0)) ** 2)
            out += np.outer(weights * self.rng.normal(45.0, 10.0), shape)
        return out


def _gaussian(t, centre, width):
    return np.exp(-0.5 * ((t - centre) / width) ** 2)


def main(argv=None):
    import argparse
    from ..config import SpellerConfig
    parser = argparse.ArgumentParser(description='simulated EEG acquisition client')
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', type=int, default=1972)
    parser.add_argument('--erp-amplitude', type=float, default=8.0,
                        help='microvolt peak of the simulated P300')
    parser.add_argument('--noise-amplitude', type=float, default=10.0,
                        help='microvolt std of the simulated background EEG')
    parser.add_argument('--speed', type=float, default=1.0)
    args = parser.parse_args(argv)
    config = SpellerConfig(host=args.host, port=args.port, speed=args.speed)
    sim = EEGSimulator(config, erp_amplitude=args.erp_amplitude,
                       noise_amplitude=args.noise_amplitude).start()
    print('simulated amplifier streaming %d channels at %g Hz into %s:%d'
          % (config.n_channels, config.fsample, args.host, args.port), flush=True)
    try:
        while True:
            sim._thread.join(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        sim.stop()


if __name__ == '__main__':
    main()
