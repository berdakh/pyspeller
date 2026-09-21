"""What training found, drawn on a canvas.

The matlab side of buffer_bci plots the class averages and where the classes
differ after `train_erp_clsfr`; this is the same report for the python
speller, in a window the operator can leave open:

  * the cross-validated AUC and accuracy, and the confusion matrix behind them
  * the target and non-target averages, per channel
  * where in space and time the two classes differ (AUC per channel per sample)

It draws with tk primitives, so it needs no plotting library.
"""

BG = '#1a1d21'
PANEL = '#14171a'
FG = '#e6e6e6'
MUTED = '#9aa0a6'
ACCENT = '#4fc3f7'
TARGET = '#81c784'
NONTARGET = '#8a9299'


def _colour(value, low=0.2, high=0.8):
    """Blue → grey → red for a value in [low, high] (0.5 is the middle)."""
    span = max(1e-6, (high - low) / 2.0)
    scaled = max(-1.0, min(1.0, (value - (low + high) / 2.0) / span))
    if scaled >= 0:
        red, green, blue = 255, int(255 - 140 * scaled), int(255 - 200 * scaled)
    else:
        red, green, blue = int(255 + 200 * scaled), int(255 + 140 * scaled), 255
    return '#%02x%02x%02x' % (red, green, blue)


class TrainingView:
    """A window showing one training summary; `update()` replaces its contents."""

    def __init__(self, master=None, title='classifier training'):
        import tkinter as tk
        self.tk = tk
        self.owns_root = master is None
        self.root = tk.Tk() if master is None else tk.Toplevel(master)
        self.root.title(title)
        self.root.configure(bg=BG)
        self.root.geometry('980x620+40+60')

        self.headline = tk.StringVar(value='')
        tk.Label(self.root, textvariable=self.headline, bg=BG, fg=FG, anchor='w',
                 font=('Helvetica', 13, 'bold'), padx=14, pady=8).pack(fill='x')
        self.subhead = tk.StringVar(value='')
        tk.Label(self.root, textvariable=self.subhead, bg=BG, fg=MUTED, anchor='w',
                 font=('Helvetica', 10), padx=14).pack(fill='x')

        body = tk.Frame(self.root, bg=BG, padx=10, pady=8)
        body.pack(fill='both', expand=True)
        self.erp_canvas = tk.Canvas(body, bg=PANEL, highlightthickness=0)
        self.erp_canvas.pack(side='left', fill='both', expand=True, padx=(0, 6))
        right = tk.Frame(body, bg=BG)
        right.pack(side='right', fill='both', expand=True)
        self.auc_canvas = tk.Canvas(right, bg=PANEL, highlightthickness=0)
        self.auc_canvas.pack(fill='both', expand=True)
        self.confusion_canvas = tk.Canvas(right, bg=PANEL, highlightthickness=0,
                                          height=110)
        self.confusion_canvas.pack(fill='x', pady=(6, 0))

        tk.Button(self.root, text='close', bg='#2b3036', fg=FG, relief='flat',
                  padx=14, pady=5, command=self.close).pack(anchor='e', padx=14,
                                                            pady=(4, 10))
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.summary = None

    # -- contents ----------------------------------------------------------
    def update(self, summary):
        """Draw a summary dictionary (as published in classifier.summary)."""
        self.summary = summary
        quality = ('good' if summary['auc'] >= 0.75 else
                   'usable' if summary['auc'] >= 0.65 else 'too low to spell with')
        self.headline.set('cross-validated AUC %.3f  ·  accuracy %.0f%%   (%s)'
                          % (summary['auc'], 100 * summary['accuracy'], quality))
        bad = summary.get('bad_channels') or []
        self.subhead.set('%d epochs, %d of them targets%s'
                         % (summary['n_epochs'], summary['n_targets'],
                            '  ·  dropped: %s' % ', '.join(bad) if bad else ''))
        self.root.update_idletasks()
        self._draw_erps(summary)
        self._draw_discriminability(summary)
        self._draw_confusion(summary)
        try:
            self.root.deiconify()
            self.root.lift()
        except Exception:
            pass

    def _draw_erps(self, summary):
        canvas = self.erp_canvas
        canvas.delete('all')
        channels = summary['channels']
        target = summary['erp_target']
        nontarget = summary['erp_nontarget']
        times = summary['times_ms']
        width = max(canvas.winfo_width(), 300)
        height = max(canvas.winfo_height(), 200)
        canvas.create_text(10, 12, text='target vs non-target average', anchor='w',
                           fill=ACCENT, font=('Helvetica', 10, 'bold'))
        canvas.create_text(width - 10, 12, anchor='e', fill=MUTED,
                           font=('Helvetica', 8),
                           text='as the classifier sees it: referenced, filtered')

        columns = 2 if len(channels) > 4 else 1
        rows = (len(channels) + columns - 1) // columns
        cell_w = (width - 16) / columns
        cell_h = (height - 30) / rows
        limit = max(1e-6, max(max(abs(v) for v in row) for row in target + nontarget))

        for index, name in enumerate(channels):
            column, row = index % columns, index // columns
            x0 = 8 + column * cell_w
            y0 = 26 + row * cell_h
            middle = y0 + cell_h / 2
            canvas.create_line(x0, middle, x0 + cell_w - 8, middle, fill='#2b3036')
            for values, colour in ((nontarget[index], NONTARGET),
                                   (target[index], TARGET)):
                points = []
                for i, value in enumerate(values):
                    x = x0 + (cell_w - 8) * i / max(1, len(values) - 1)
                    points += [x, middle - value / limit * (cell_h / 2 - 8)]
                canvas.create_line(*points, fill=colour, width=2, smooth=True)
            canvas.create_text(x0 + 4, y0 + 10, text=name, anchor='w', fill=MUTED,
                               font=('Helvetica', 9, 'bold'))
        canvas.create_text(width - 10, height - 8,
                           text='%d–%d ms   ±%.1f µV' % (times[0], times[-1], limit),
                           anchor='e', fill=MUTED, font=('Helvetica', 8))

    def _draw_discriminability(self, summary):
        canvas = self.auc_canvas
        canvas.delete('all')
        values = summary['discriminability']
        channels = summary['channels']
        times = summary['times_ms']
        width = max(canvas.winfo_width(), 260)
        height = max(canvas.winfo_height(), 160)
        canvas.create_text(10, 12, text='where the classes differ (AUC)', anchor='w',
                           fill=ACCENT, font=('Helvetica', 10, 'bold'))

        left, top = 44, 26
        cell_w = (width - left - 12) / max(1, len(times))
        cell_h = (height - top - 26) / max(1, len(channels))
        for row, name in enumerate(channels):
            for column in range(len(times)):
                x = left + column * cell_w
                y = top + row * cell_h
                canvas.create_rectangle(x, y, x + cell_w, y + cell_h, width=0,
                                        fill=_colour(values[row][column]))
            canvas.create_text(left - 6, top + (row + 0.5) * cell_h, text=name,
                               anchor='e', fill=MUTED, font=('Helvetica', 8))
        canvas.create_text(left, height - 10, text='%d ms' % times[0], anchor='w',
                           fill=MUTED, font=('Helvetica', 8))
        canvas.create_text(width - 12, height - 10, text='%d ms' % times[-1],
                           anchor='e', fill=MUTED, font=('Helvetica', 8))
        best = max(max(row) for row in values)
        canvas.create_text(width / 2, height - 10,
                           text='best %.2f' % best, fill=MUTED,
                           font=('Helvetica', 8))

    def _draw_confusion(self, summary):
        canvas = self.confusion_canvas
        canvas.delete('all')
        confusion = summary.get('confusion')
        if not confusion:
            return
        canvas.create_text(10, 12, text='confusion (cross-validated)', anchor='w',
                           fill=ACCENT, font=('Helvetica', 10, 'bold'))
        labels = ['non-target', 'target']
        left, top, cell = 96, 26, 34
        for column, name in enumerate(labels):
            canvas.create_text(left + (column + 0.5) * 110, top - 6,
                               text='said %s' % name, fill=MUTED,
                               font=('Helvetica', 8))
        for row, name in enumerate(labels):
            # each row is read across: of the flashes that really were X,
            # how many did the classifier call X?
            in_row = max(1, sum(confusion[row]))
            canvas.create_text(left - 8, top + (row + 0.5) * cell,
                               text='was %s' % name, anchor='e', fill=MUTED,
                               font=('Helvetica', 8))
            for column in range(2):
                count = confusion[row][column]
                share = count / in_row
                x, y = left + column * 110, top + row * cell
                right = row == column
                intensity = int(90 + 120 * share)
                fill = ('#%02x%02x%02x' % (40, intensity, 60) if right
                        else '#%02x%02x%02x' % (intensity, 50, 50))
                canvas.create_rectangle(x, y, x + 106, y + cell - 4, width=0,
                                        fill=fill)
                canvas.create_text(x + 53, y + (cell - 4) / 2,
                                   text='%d  (%.0f%%)' % (count, 100 * share),
                                   fill='#f0f0f0', font=('Helvetica', 9, 'bold'))
        canvas.create_text(left, top + 2 * cell + 10, anchor='w', fill=MUTED,
                           font=('Helvetica', 8),
                           text='each row adds up to 100%: what was done with the '
                                'flashes of that kind')

    # -- lifecycle ---------------------------------------------------------
    def close(self):
        try:
            self.root.withdraw()
        except Exception:
            pass

    def destroy(self):
        try:
            self.root.destroy()
        except Exception:
            pass
