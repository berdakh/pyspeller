"""Turning a stream of samples plus events into epochs.

An epoch is the slice of data that follows a stimulus event -- for a P300
speller, the 600 ms after a row or column flashed.  This is the piece that
couples the buffer to the classifier.
"""
import time

import numpy as np


def slice_epochs(client, events, trlen_samples, offset_samples=0):
    """Epochs [n_events x n_channels x trlen] for events whose data has arrived.

    Events whose window runs past the end of the buffer are skipped, so the
    caller should only pass events it knows are complete (see EpochGatherer).
    """
    epochs, used = [], []
    for evt in events:
        start = evt.sample + offset_samples
        end = start + trlen_samples - 1
        if start < 0:
            continue
        data = client.get_data(start, end)          # [samples x channels]
        epochs.append(data.T)                        # -> [channels x samples]
        used.append(evt)
    if not epochs:
        nchan = client.header.nchannels if client.header else 0
        return np.zeros((0, nchan, trlen_samples)), []
    return np.stack(epochs).astype(float), used


class EpochGatherer:
    """Collects epochs for matching events until a stop event arrives.

    Mirrors bufhelp.gatherdata() from the matlab/python framework: it watches
    the event stream, waits until each event's data window is actually in the
    buffer, and returns the epochs together with the events that produced them.
    """

    def __init__(self, client, event_types, trlen_samples, offset_samples=0):
        self.client = client
        self.event_types = ([event_types] if isinstance(event_types, str)
                            else list(event_types))
        self.trlen_samples = int(trlen_samples)
        self.offset_samples = int(offset_samples)

    def gather(self, stop_types=(), timeout=30.0, poll_ms=100, on_epoch=None):
        """(epochs, events, stop_event) collected until a stop event or timeout.

        Each entry of `stop_types` is either an event type, or a (type, value)
        pair when only a particular value ends the run -- ('stimulus.training',
        'end') stops at the end of a calibration run but not at its start.

        `on_epoch(epoch, event)` is called for each epoch as it completes, which
        is what the online feedback loop uses to score flashes as they arrive.
        """
        stop_types = ([stop_types] if isinstance(stop_types, (str, tuple))
                      else list(stop_types))
        stop_specs = [(s, None) if isinstance(s, str) else (s[0], str(s[1]))
                      for s in stop_types]
        pending, epochs, events = [], [], []
        stop_event = None
        deadline = time.time() + timeout

        while time.time() < deadline:
            for evt in self.client.new_events(timeout_ms=poll_ms):
                if evt.type in self.event_types:
                    pending.append(evt)
                elif any(evt.type == t and (v is None or str(evt.value) == v)
                         for t, v in stop_specs):
                    stop_event = evt
            nsamples = self.client.poll()[0]
            ready = [e for e in pending
                     if e.sample + self.offset_samples + self.trlen_samples <= nsamples]
            if ready:
                pending = [e for e in pending if e not in ready]
                new_epochs, used = slice_epochs(self.client, ready,
                                                self.trlen_samples,
                                                self.offset_samples)
                for epoch, evt in zip(new_epochs, used):
                    epochs.append(epoch)
                    events.append(evt)
                    if on_epoch is not None:
                        on_epoch(epoch, evt)
            if stop_event is not None and not pending:
                break

        if not epochs:
            nchan = self.client.header.nchannels if self.client.header else 0
            return np.zeros((0, nchan, self.trlen_samples)), [], stop_event
        return np.stack(epochs).astype(float), events, stop_event
