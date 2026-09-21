"""Tk control panel: run the experiment and watch the signals while it runs.

The panel is just another buffer client.  Its buttons publish startPhase.cmd
events, which the stimulus and signal processing clients obey, and it watches
the data and event streams to draw the scope, the per-channel signal quality
and the spelled text.  It therefore works the same whether the samples come
from the simulator or from a g.tec amplifier over LSL.
"""
import collections
import json
import time

import numpy as np

from ..buffer.client import BufferClient
from ..speller import text as speller_text

PHASES = [('Practice', 'practice'), ('Calibrate', 'calibrate'),
          ('Train classifier', 'train'), ('Feedback', 'feedback'),
          ('Free spelling', 'free')]

BG = '#1a1d21'
FG = '#e6e6e6'
ACCENT = '#4fc3f7'
TRACE_COLOURS = ['#4fc3f7', '#81c784', '#ffb74d', '#e57373', '#ba68c8',
                 '#4db6ac', '#fff176', '#90a4ae']


class ControlPanel:
    """The experiment's control window, with a live scope."""

    def __init__(self, config, client=None, window_seconds=5.0, refresh_ms=50,
                 renderers=(), on_quit=None, recording=None, source=None):
        import tkinter as tk
        self.tk = tk
        self.config = config
        self.client = client or BufferClient(config.host, config.port).connect(retries=20)
        self.header = self.client.wait_for_header()
        self.window_seconds = float(window_seconds)
        self.refresh_ms = int(refresh_ms)
        self.renderers = list(renderers)      # extra tk renderers to pump
        self.on_quit = on_quit
        self.recording = recording            # directory the saver writes to
        self.source = source                  # where the samples come from

        self.nchannels = self.header.nchannels
        self.labels = self.header.labels or ['ch%d' % (i + 1)
                                             for i in range(self.nchannels)]
        self.window_samples = max(64, int(self.window_seconds * self.header.fsample))
        self.buffer = np.zeros((self.nchannels, self.window_samples))
        self.cursor = self.client.poll()[0]
        self.spelled = ''
        self.scale = 50.0                     # microvolts per trace, before autoscale
        self.autoscale = True
        self._last_stats = (time.time(), self.cursor)
        self._rate = 0.0
        self.paused = False
        self.ready = set()            # clients that have said they are listening
        self.training = None          # the last training summary, as published
        self.training_view = None

        self.root = tk.Tk()
        self.root.title('pyspeller control panel')
        self.root.configure(bg=BG)
        self.root.protocol('WM_DELETE_WINDOW', self.quit)
        self.client.reset_event_cursor()
        self._build()

    # -- layout ------------------------------------------------------------
    def _build(self):
        tk = self.tk
        left = tk.Frame(self.root, bg=BG, padx=12, pady=12)
        left.pack(side='left', fill='y')
        right = tk.Frame(self.root, bg=BG, padx=8, pady=12)
        right.pack(side='right', fill='both', expand=True)

        tk.Label(left, text='experiment', bg=BG, fg=ACCENT,
                 font=('Helvetica', 14, 'bold')).pack(anchor='w')
        for text, phase in PHASES:
            tk.Button(left, text=text, width=18, bg='#2b3036', fg=FG,
                      activebackground=ACCENT, relief='flat', pady=6,
                      command=lambda p=phase: self.send_phase(p)).pack(pady=3)
        # correcting the text: the user can also select DEL in the matrix, this
        # is the same edit from the operator's side
        edits = tk.Frame(left, bg=BG)
        edits.pack(pady=(10, 0))
        tk.Button(edits, text='\u232b backspace', width=11, bg='#2b3036', fg=FG,
                  relief='flat', pady=5,
                  command=lambda: self.send_edit(speller_text.DELETE)).pack(side='left')
        tk.Button(edits, text='clear', width=5, bg='#2b3036', fg=FG, relief='flat',
                  pady=5,
                  command=lambda: self.send_edit(speller_text.CLEAR)).pack(side='left',
                                                                           padx=(4, 0))
        # hold or abandon whatever block is running
        running = tk.Frame(left, bg=BG)
        running.pack(pady=(10, 0))
        self.pause_text = tk.StringVar(value='\u23f8 pause')
        tk.Button(running, textvariable=self.pause_text, width=11, bg='#2b3036',
                  fg=FG, relief='flat', pady=5,
                  command=self.toggle_pause).pack(side='left')
        tk.Button(running, text='\u25a0 stop', width=5, bg='#2b3036', fg=FG,
                  relief='flat', pady=5,
                  command=self.stop_block).pack(side='left', padx=(4, 0))

        tk.Button(left, text='Quit', width=18, bg='#3a2b2b', fg=FG, relief='flat',
                  pady=6, command=self.quit).pack(pady=(12, 3))

        self.status = tk.StringVar(value='connected')
        tk.Label(left, textvariable=self.status, bg=BG, fg=FG, wraplength=170,
                 justify='left').pack(anchor='w', pady=(14, 0))
        self.spelled_var = tk.StringVar(value='typed: _')
        tk.Label(left, textvariable=self.spelled_var, bg=BG, fg='#81c784',
                 font=('Courier', 15, 'bold'), wraplength=170,
                 justify='left').pack(anchor='w', pady=(10, 0))
        if self.source:
            tk.Label(left, text='source: %s' % self.source, bg=BG, fg='#9aa0a6',
                     wraplength=170, justify='left',
                     font=('Helvetica', 9)).pack(anchor='w', pady=(8, 0))
        if self.recording:
            tk.Label(left, text='recording to\n%s' % self.recording, bg=BG,
                     fg='#9aa0a6', wraplength=170, justify='left',
                     font=('Helvetica', 8)).pack(anchor='w', pady=(4, 0))

        tk.Label(left, text='signal quality (uV rms)', bg=BG, fg=ACCENT,
                 font=('Helvetica', 10, 'bold')).pack(anchor='w', pady=(16, 2))
        self.quality = tk.Canvas(left, width=180, height=18 * self.nchannels,
                                 bg='#14171a', highlightthickness=0)
        self.quality.pack(anchor='w')
        self._quality_items = []
        for i, label in enumerate(self.labels):
            y = 18 * i + 9
            self.quality.create_text(22, y, text=label, fill=FG,
                                     font=('Helvetica', 9))
            bar = self.quality.create_rectangle(44, y - 5, 44, y + 5,
                                                fill=ACCENT, width=0)
            value = self.quality.create_text(160, y, text='', fill='#9aa0a6',
                                             font=('Helvetica', 9))
            self._quality_items.append((bar, value))

        self.scope = tk.Canvas(right, bg='#0f1215', highlightthickness=0, height=420)
        self.scope.pack(fill='both', expand=True)
        self._traces = [self.scope.create_line(0, 0, 0, 0, fill=TRACE_COLOURS[i % 8],
                                               width=1)
                        for i in range(self.nchannels)]
        self._trace_labels = [self.scope.create_text(24, 0, text=label, fill='#6b7075',
                                                     font=('Helvetica', 9))
                              for label in self.labels]

        tk.Label(right, text='events', bg=BG, fg=ACCENT,
                 font=('Helvetica', 10, 'bold')).pack(anchor='w', pady=(8, 0))
        self.log = tk.Listbox(right, height=7, bg='#14171a', fg=FG,
                              highlightthickness=0, relief='flat',
                              font=('Courier', 9))
        self.log.pack(fill='x')
        self._log_lines = collections.deque(maxlen=200)

    # -- control -----------------------------------------------------------
    def send_phase(self, phase):
        self._set_paused(False)
        self.client.send_event('startPhase.cmd', phase)
        self._log('-> startPhase.cmd %s' % phase)
        self.status.set('running: %s' % phase)

    def send_control(self, value):
        """Pause, resume or stop the block that is running."""
        self.client.send_event(speller_text.CONTROL_EVENT, value)
        return value

    def toggle_pause(self):
        """Hold the flashing where it is, or let it go on."""
        return self.send_control(speller_text.RESUME if self.paused
                                 else speller_text.PAUSE)

    def stop_block(self):
        """End the running block early; the session itself carries on."""
        return self.send_control(speller_text.STOP)

    def send_edit(self, symbol=speller_text.DELETE):
        """Correct the typed text -- backspace or clear -- for every client."""
        self.client.send_event(speller_text.EDIT_EVENT, symbol)
        return symbol

    def quit(self):
        try:
            self.client.send_event('startPhase.cmd', 'quit')
        except Exception:
            pass
        if self.on_quit is not None:
            self.on_quit()
        self.root.quit()

    # -- periodic update ---------------------------------------------------
    def tick(self):
        try:
            self._pump_data()
            self._pump_events()
            self._draw_scope()
            self._draw_quality()
        except Exception as err:               # never let the ui die on a hiccup
            self.status.set('error: %s' % err)
        for renderer in self.renderers:
            renderer.pump()
        self.root.after(self.refresh_ms, self.tick)

    def _pump_data(self):
        nsamples = self.client.poll()[0]
        if nsamples <= self.cursor:
            return
        start = max(self.cursor, nsamples - self.window_samples)
        data = self.client.get_data(start, nsamples - 1).T      # [channels x samples]
        n = data.shape[1]
        if n >= self.window_samples:
            self.buffer = data[:, -self.window_samples:]
        else:
            self.buffer = np.hstack([self.buffer[:, n:], data])
        now = time.time()
        elapsed = now - self._last_stats[0]
        if elapsed > 1.0:
            self._rate = (nsamples - self._last_stats[1]) / elapsed
            self._last_stats = (now, nsamples)
        self.cursor = nsamples
        self.status.set('%d samples, %d events\n%.0f Hz in'
                        % (nsamples, self.client.poll()[1], self._rate))

    def _pump_events(self):
        for evt in self.client.new_events(timeout_ms=0):
            if evt.type == speller_text.CONTROL_EVENT:
                # follow the control events rather than the button presses, so
                # the panel agrees with whoever sent them
                value = str(evt.value)
                if value == speller_text.PAUSE:
                    self._set_paused(True)
                elif value == speller_text.RESUME:
                    self._set_paused(False)
                elif value == speller_text.STOP:
                    self._set_paused(False)
                    self.status.set('block stopped')
            if evt.type in ('classifier.prediction', speller_text.EDIT_EVENT):
                # DEL and the other control keys edit the text, they are not
                # characters to append -- the speller window shows the same.
                # Corrections are applied when the event comes back from the
                # buffer, so every client ends up with the same text.
                self.spelled = speller_text.apply_symbol(self.spelled, evt.value)
                self.spelled_var.set('typed: %s' % speller_text.display(self.spelled))
            elif evt.type == 'speller.ready':
                self.ready.add(str(evt.value))
                self.status.set('ready: %s' % ', '.join(sorted(self.ready)))
            elif evt.type == 'stimulus.feedback' and str(evt.value) == 'start':
                self.spelled = ''          # a new block types a new line
                self.spelled_var.set('typed: %s' % speller_text.display(''))
            elif evt.type == 'sigproc.training' and str(evt.value) == 'done':
                self.status.set('classifier trained')
            elif evt.type == 'classifier.summary':
                self.show_training(evt.value)
            elif evt.type == 'sigproc.error':
                self.status.set('sigproc error: %s' % evt.value)
            if evt.type not in ('stimulus.rowFlash', 'stimulus.colFlash',
                                'stimulus.tgtFlash'):
                self._log('%8d %s %s' % (evt.sample, evt.type, evt.value))

    def show_training(self, summary):
        """Open (or refresh) the window showing what training found."""
        if isinstance(summary, str):
            try:
                summary = json.loads(summary)
            except ValueError:
                return None
        self.training = summary
        self.status.set('classifier trained: AUC %.3f, accuracy %.0f%%'
                        % (summary['auc'], 100 * summary['accuracy']))
        try:
            from .training_view import TrainingView
            if self.training_view is None:
                self.training_view = TrainingView(master=self.root)
            self.training_view.update(summary)
        except Exception as err:            # a headless run has no window
            self._log('training view unavailable: %s' % err)
        return summary

    def _set_paused(self, paused):
        self.paused = paused
        self.pause_text.set('\u25b6 resume' if paused else '\u23f8 pause')
        if paused:
            self.status.set('paused')

    def _log(self, line):
        self.log.insert('end', line)
        self.log.see('end')
        if self.log.size() > 200:
            self.log.delete(0)

    # -- drawing -----------------------------------------------------------
    def _draw_scope(self):
        width = max(self.scope.winfo_width(), 100)
        height = max(self.scope.winfo_height(), 100)
        row = height / self.nchannels
        if self.autoscale:
            spread = float(np.percentile(np.abs(self.buffer), 95)) or 1.0
            self.scale = max(1.0, 2.5 * spread)
        step = max(1, self.buffer.shape[1] // int(width))
        samples = self.buffer[:, ::step]
        xs = np.linspace(40, width - 8, samples.shape[1])
        for i in range(self.nchannels):
            centre = row * (i + 0.5)
            ys = centre - samples[i] * (row * 0.45 / self.scale)
            ys = np.clip(ys, centre - row / 2, centre + row / 2)
            self.scope.coords(self._traces[i],
                              *[c for pair in zip(xs, ys) for c in pair])
            self.scope.coords(self._trace_labels[i], 24, centre)

    def _draw_quality(self):
        rms = np.sqrt((self.buffer ** 2).mean(axis=1))
        for i, (bar, value) in enumerate(self._quality_items):
            y = 18 * i + 9
            length = float(np.clip(rms[i] / 50.0, 0, 1)) * 100
            colour = '#81c784' if rms[i] < 30 else ('#ffb74d' if rms[i] < 60
                                                    else '#e57373')
            self.quality.coords(bar, 44, y - 5, 44 + length, y + 5)
            self.quality.itemconfigure(bar, fill=colour)
            self.quality.itemconfigure(value, text='%5.1f' % rms[i])

    # -- run ---------------------------------------------------------------
    def run(self):
        self.root.after(self.refresh_ms, self.tick)
        self.root.mainloop()
        try:
            self.root.destroy()
        except Exception:
            pass
