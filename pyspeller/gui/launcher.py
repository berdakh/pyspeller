"""The start screen: choose where the data comes from, with the mouse.

Everything a session needs before the first flash -- amplifier or simulator,
who the participant is, which matrix, how many repetitions, whether to record
-- is picked here and handed back to the caller, so no one has to remember a
command line.  The same choices exist as flags on `python -m pyspeller run`.
"""
import threading

from ..config import LAYOUTS, LAYOUT_LANGUAGE
from ..speller.messages import LANGUAGES

def pylsl_installed():
    """Whether an LSL device can be reached at all from this machine."""
    import importlib.util
    return importlib.util.find_spec('pylsl') is not None


BG = '#1a1d21'
FG = '#e6e6e6'
ACCENT = '#4fc3f7'
MUTED = '#9aa0a6'


class SessionLauncher:
    """A small dialog; `run()` returns the chosen settings, or None if closed."""

    def __init__(self, config, title='pyspeller — start a session'):
        import tkinter as tk
        self.tk = tk
        self.config = config
        self.choices = None
        self.streams = []

        self.root = tk.Tk()
        self.root.title(title)
        self.root.configure(bg=BG)
        self.source = tk.StringVar(value='simulator')
        self.subject = tk.StringVar(value='test')
        self.experiment = tk.StringVar(value='speller')
        self.layout = tk.StringVar(value='6x6-control')
        self.language = tk.StringVar(value=config.language)
        self.repetitions = tk.IntVar(value=config.n_repetitions)
        self.record = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value='')
        self._build()

    # -- layout ------------------------------------------------------------
    def _build(self):
        tk = self.tk
        self.root.minsize(520, 470)
        frame = tk.Frame(self.root, bg=BG, padx=24, pady=20)
        frame.pack(fill='both', expand=True)
        frame.columnconfigure(0, weight=1)

        tk.Label(frame, text='P300 speller', bg=BG, fg=FG,
                 font=('Helvetica', 17, 'bold')).pack(anchor='w')
        tk.Label(frame, text='set up a session, then press start', bg=BG, fg=MUTED,
                 font=('Helvetica', 10)).pack(anchor='w', pady=(0, 16))

        # -- where the data comes from
        tk.Label(frame, text='WHERE DOES THE DATA COME FROM?', bg=BG, fg=ACCENT,
                 font=('Helvetica', 10, 'bold')).pack(anchor='w')
        source = tk.Frame(frame, bg=BG)
        source.pack(fill='x', pady=(4, 0))
        amplifier_text = 'g.tec amplifier   (over Lab Streaming Layer)'
        if not pylsl_installed():
            amplifier_text += '   -- needs pylsl'
        for value, text in [('simulator', 'simulated subject   (no hardware needed)'),
                            ('lsl', amplifier_text)]:
            tk.Radiobutton(source, text=text, value=value, variable=self.source,
                           bg=BG, fg=FG, selectcolor='#2b3036', activebackground=BG,
                           activeforeground=FG, highlightthickness=0,
                           command=self._source_changed, anchor='w',
                           font=('Helvetica', 11)).pack(fill='x')

        amplifiers = tk.Frame(frame, bg=BG)
        amplifiers.pack(fill='x', pady=(6, 0))
        tk.Button(amplifiers, text='scan for amplifiers', bg='#2b3036', fg=FG,
                  relief='flat', padx=12, pady=4, command=self.scan).pack(side='left')
        tk.Label(amplifiers, textvariable=self.status, bg=BG, fg=MUTED,
                 anchor='w', font=('Helvetica', 9)).pack(side='left', padx=(12, 0))
        self.stream_list = tk.Listbox(frame, height=4, bg='#14171a', fg=FG,
                                      highlightthickness=0, relief='flat',
                                      font=('Courier', 9), exportselection=False)
        self.stream_list.pack(fill='x', pady=(6, 16))

        # -- the session itself
        tk.Label(frame, text='SESSION', bg=BG, fg=ACCENT,
                 font=('Helvetica', 10, 'bold')).pack(anchor='w')
        options = tk.Frame(frame, bg=BG)
        options.pack(fill='x', pady=(6, 0))
        options.columnconfigure(1, weight=1)
        self._entry(options, 'participant', self.subject, 0)
        self._entry(options, 'experiment', self.experiment, 1)

        tk.Label(options, text='matrix', bg=BG, fg=FG, anchor='w'
                 ).grid(row=2, column=0, sticky='w', pady=4, padx=(0, 16))
        menu = tk.OptionMenu(options, self.layout, *sorted(LAYOUTS),
                             command=self._layout_changed)
        menu.configure(bg='#2b3036', fg=FG, relief='flat', highlightthickness=0,
                       activebackground=ACCENT, width=14, anchor='w')
        menu['menu'].configure(bg='#2b3036', fg=FG)
        menu.grid(row=2, column=1, sticky='w')

        tk.Label(options, text='language on screen', bg=BG, fg=FG, anchor='w'
                 ).grid(row=3, column=0, sticky='w', pady=4, padx=(0, 16))
        language_menu = tk.OptionMenu(options, self.language, *sorted(LANGUAGES))
        language_menu.configure(bg='#2b3036', fg=FG, relief='flat',
                                highlightthickness=0, activebackground=ACCENT,
                                width=14, anchor='w')
        language_menu['menu'].configure(bg='#2b3036', fg=FG)
        language_menu.grid(row=3, column=1, sticky='w')

        tk.Label(options, text='repetitions per letter', bg=BG, fg=FG, anchor='w'
                 ).grid(row=4, column=0, sticky='w', pady=4, padx=(0, 16))
        tk.Spinbox(options, from_=1, to=30, textvariable=self.repetitions, width=6,
                   bg='#14171a', fg=FG, relief='flat', insertbackground=FG,
                   buttonbackground='#2b3036').grid(row=4, column=1, sticky='w')

        tk.Checkbutton(frame, text='record this session to disk', variable=self.record,
                       bg=BG, fg=FG, selectcolor='#2b3036', activebackground=BG,
                       activeforeground=FG, highlightthickness=0, anchor='w'
                       ).pack(fill='x', pady=(10, 0))

        buttons = tk.Frame(frame, bg=BG)
        buttons.pack(fill='x', pady=(20, 0))
        tk.Button(buttons, text='Start session', bg=ACCENT, fg='#10232b',
                  relief='flat', padx=18, pady=7, font=('Helvetica', 11, 'bold'),
                  command=self.start).pack(side='left')
        tk.Button(buttons, text='Quit', bg='#3a2b2b', fg=FG, relief='flat',
                  padx=14, pady=7, command=self.cancel).pack(side='left', padx=10)

        self.root.protocol('WM_DELETE_WINDOW', self.cancel)
        self._source_changed()

    def _entry(self, parent, label, variable, row):
        tk = self.tk
        tk.Label(parent, text=label, bg=BG, fg=FG, anchor='w').grid(
            row=row, column=0, sticky='w', pady=4, padx=(0, 16))
        tk.Entry(parent, textvariable=variable, width=18, bg='#14171a', fg=FG,
                 relief='flat', insertbackground=FG).grid(row=row, column=1,
                                                          sticky='w', ipady=2)

    # -- behaviour ---------------------------------------------------------
    def _layout_changed(self, layout):
        """Choosing the Kazakh or Russian matrix suggests its language too."""
        if layout in LAYOUT_LANGUAGE:
            self.language.set(LAYOUT_LANGUAGE[layout])

    def _source_changed(self):
        using_lsl = self.source.get() == 'lsl'
        self.stream_list.configure(state='normal' if using_lsl else 'disabled')
        if using_lsl and not self.streams:
            if pylsl_installed():
                self.status.set('press scan to find the amplifier')
            else:
                self.status.set('pylsl is not installed  --  run:  pip install pylsl')
        elif not using_lsl:
            self.status.set('the simulator needs no hardware')

    def scan(self):
        """Look for LSL streams on the network, without freezing the window."""
        self.source.set('lsl')
        self._source_changed()
        self.status.set('scanning ...')
        self.stream_list.delete(0, 'end')

        def look():
            try:
                from ..acquisition.lsl_bridge import list_streams
                found = list_streams(timeout=2.0)
            except ImportError:
                message = 'pylsl is not installed  --  run:  pip install pylsl'
                self.root.after(0, lambda m=message: self.status.set(m))
                return
            except Exception as err:
                message = 'scan failed: %s' % err
                self.root.after(0, lambda m=message: self.status.set(m))
                return
            self.root.after(0, lambda: self._show_streams(found))

        threading.Thread(target=look, name='lsl-scan', daemon=True).start()

    def _show_streams(self, found):
        # only regularly sampled streams: the buffer stores a sample rate
        self.streams = [s for s in found if s['fsample'] > 0]
        self.stream_list.configure(state='normal')      # a disabled list ignores inserts
        self.stream_list.delete(0, 'end')
        for stream in self.streams:
            self.stream_list.insert(
                'end', '%-22s %-6s %2d ch  %g Hz' % (stream['name'][:22],
                                                     stream['type'],
                                                     stream['channels'],
                                                     stream['fsample']))
        if self.streams:
            self.stream_list.selection_set(0)
            self.status.set('%d stream(s) found -- pick one' % len(self.streams))
        else:
            self.status.set('nothing found: is the g.tec LSL connector streaming?')

    def selected_stream(self):
        selection = self.stream_list.curselection()
        if not self.streams:
            return None
        return self.streams[selection[0] if selection else 0]

    def start(self):
        choices = {'source': self.source.get(),
                   'subject': self.subject.get().strip() or 'test',
                   'experiment': self.experiment.get().strip() or 'speller',
                   'layout': self.layout.get(),
                   'language': self.language.get(),
                   'n_repetitions': max(1, int(self.repetitions.get())),
                   'record': bool(self.record.get()),
                   'lsl_name': None, 'lsl_type': 'EEG'}
        if choices['source'] == 'lsl':
            stream = self.selected_stream()
            if stream is None:
                self.status.set('scan and pick an amplifier first')
                return None
            choices['lsl_name'] = stream['name']
            choices['lsl_type'] = stream['type']
        self.choices = choices
        self.root.quit()
        return choices

    def cancel(self):
        self.choices = None
        self.root.quit()

    def run(self):
        """Show the dialog; returns the chosen settings, or None if cancelled."""
        self.root.mainloop()
        try:
            self.root.destroy()
        except Exception:
            pass
        return self.choices


def ask_for_session(config):
    """Show the launcher; None when tk is unavailable or the user cancelled."""
    try:
        return SessionLauncher(config).run()
    except Exception as err:                 # no display, no tk
        print('no graphical launcher available (%s)' % err)
        return None
