"""A clock with an adjustable speed, so experiments can run faster than real time.

Every timed component (stimulus presentation, acquisition) takes its time from
one of these.  With speed=1 it is the wall clock.  With speed=20 an experiment
that takes a minute of "subject time" finishes in three seconds, while the data
in the buffer -- which is indexed by samples, not seconds -- is identical.
That is what makes the end-to-end tests fast without making them unrealistic.
"""
import time


class Clock:
    def __init__(self, speed=1.0):
        if speed <= 0:
            raise ValueError('speed must be positive')
        self.speed = float(speed)
        self.t0 = time.time()

    def now(self):
        """Seconds of experiment time since the clock was created."""
        return (time.time() - self.t0) * self.speed

    def sleep(self, seconds):
        """Sleep for `seconds` of experiment time."""
        if seconds > 0:
            time.sleep(seconds / self.speed)

    def sleep_until(self, deadline):
        """Sleep until `deadline` (experiment time); returns the lateness."""
        remaining = deadline - self.now()
        self.sleep(remaining)
        return max(0.0, -remaining)


class BufferClock:
    """Experiment time taken from the data stream instead of the wall clock.

    The stimulus client stamps its events with the buffer's sample counter, so
    what actually has to be regular is the number of samples between flashes,
    not the number of milliseconds.  Pacing on the sample counter keeps the
    stimulus in step with acquisition even when the machine is loaded or the
    simulator is running many times faster than real time -- two flashes can
    then never end up on the same sample, which would confuse the epoching.

    For a real experiment at speed 1 this behaves like the wall clock, with the
    difference that it stalls if acquisition stalls, which is what you want.
    """

    def __init__(self, client, fsample=None, speed=1.0, timeout_ms=2000):
        self.client = client
        self.fsample = float(fsample or client.fsample)
        self.speed = float(speed)
        self.timeout_ms = int(timeout_ms)
        self.offset = self.client.poll()[0] / self.fsample

    def now(self):
        return self.client.poll()[0] / self.fsample - self.offset

    def sleep(self, seconds):
        if seconds > 0:
            self.sleep_until(self.now() + seconds)

    def sleep_until(self, deadline):
        target = int((deadline + self.offset) * self.fsample)
        while True:
            nsamples, _ = self.client.wait(max(0, target - 1), 0xFFFFFFFF,
                                           self.timeout_ms)
            if nsamples >= target:
                return max(0.0, nsamples / self.fsample - self.offset - deadline)
