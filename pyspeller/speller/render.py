"""Ways of showing the speller matrix.

Every renderer implements the same small interface, so the stimulus code does
not care whether it is driving a window, a terminal, or nothing at all:

    draw(highlight=..., style=...)   show the grid, optionally highlighting cells
    message(text)                    show a line of status text under the grid
    set_output(text)                 show the letters spelled so far
    mainloop(worker)                 run the display until the worker finishes

The stimulus sequence always runs in a worker thread; a GUI toolkit needs the
main thread, so renderers marshal draw commands onto it.
"""
import queue
import threading

# style -> (foreground, background) of the highlighted cells
STYLES = {
    'idle': ('#808080', '#101010'),
    'flash': ('#ffffff', '#101010'),
    'target': ('#00ff00', '#101010'),
    'prediction': ('#00ff00', '#101010'),
}


class Renderer:
    """Base class: does nothing, and records nothing."""

    def __init__(self, matrix):
        self.matrix = matrix

    def draw(self, highlight=(), style='flash'):
        pass

    def message(self, text):
        pass

    def set_output(self, text):
        """Show the text the user has spelled so far."""
        pass

    def close(self):
        pass

    def mainloop(self, worker=None):
        """Run the display until `worker` (a thread) is done."""
        if worker is not None:
            worker.join()


class HeadlessRenderer(Renderer):
    """Records what would have been drawn -- used by the tests and the demo."""

    def __init__(self, matrix):
        super().__init__(matrix)
        self.frames = []
        self.messages = []
        self.output = ''

    def draw(self, highlight=(), style='flash'):
        self.frames.append((tuple(highlight), style))

    def message(self, text):
        self.messages.append(text)

    def set_output(self, text):
        self.output = text


class TextRenderer(Renderer):
    """Prints the matrix to the terminal -- enough to run without any display."""

    def __init__(self, matrix, stream=None):
        super().__init__(matrix)
        import sys
        self.stream = stream or sys.stdout

    def draw(self, highlight=(), style='flash'):
        highlight = set(highlight)
        marker = {'flash': '*', 'target': '>', 'prediction': '#'}.get(style, '*')
        lines = []
        for r, row in enumerate(self.matrix.symbols):
            cells = []
            for c, symbol in enumerate(row):
                cells.append('%s%s%s' % (marker, symbol, marker)
                             if (r, c) in highlight else ' %s ' % symbol)
            lines.append(' '.join(cells))
        print('\n'.join(lines) + '\n', file=self.stream, flush=True)

    def message(self, text):
        print('-- %s' % text, file=self.stream, flush=True)

    def set_output(self, text):
        print('   typed: %s_' % text, file=self.stream, flush=True)


class TkRenderer(Renderer):
    """A full-screen-ish tkinter window showing the speller matrix.

    Draw calls can come from any thread: they are queued and executed on the
    thread running the tk event loop.
    """

    def __init__(self, matrix, title='P300 speller', size=(720, 720), master=None):
        super().__init__(matrix)
        import tkinter as tk
        self.tk = tk
        self.owns_root = master is None
        self.root = tk.Tk() if master is None else tk.Toplevel(master)
        self.root.title(title)
        self.root.configure(bg='#101010')
        if master is not None:      # sit next to the control panel, not on top of it
            self.root.geometry('%dx%d+%d+%d' % (size[0], size[1], 660, 30))
        self.canvas = tk.Canvas(self.root, width=size[0], height=size[1],
                                bg='#101010', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.size = size
        self._queue = queue.Queue()
        self._closed = threading.Event()
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)
        self._items = {}
        self._build()

    def _build(self):
        w, h = self.size
        top, bottom = 70, 60          # room for the spelled text and the status line
        grid_height = h - top - bottom
        self._items = {}
        for r in range(self.matrix.n_rows):
            for c in range(self.matrix.n_cols):
                x = w * (c + 0.5) / self.matrix.n_cols
                y = top + grid_height * (r + 0.5) / self.matrix.n_rows
                symbol = self.matrix.symbol_at(r, c)
                self._items[(r, c)] = self.canvas.create_text(
                    x, y, text=symbol, fill=STYLES['idle'][0],
                    font=('Helvetica', self._font_size(symbol, w, grid_height),
                          'bold'))
        # the text field: what the user has spelled so far
        self.canvas.create_rectangle(16, 14, w - 16, top - 16, outline='#2f3439',
                                     fill='#181b1e')
        self._output = self.canvas.create_text(28, top / 2 - 2, text='_', anchor='w',
                                               fill=STYLES['prediction'][0],
                                               font=('Courier', 24, 'bold'))
        self._message = self.canvas.create_text(w / 2, h - 30, text='', fill='#a0a0a0',
                                                font=('Helvetica', 18))

    def _font_size(self, symbol, width, grid_height):
        """Fit the symbol in its cell -- keys like DEL need a smaller font."""
        cell = min(width / self.matrix.n_cols, grid_height / self.matrix.n_rows)
        size = int(cell * 0.55)
        if len(symbol) > 1:                     # bold helvetica is ~0.75 em wide
            size = int(min(size, cell * 0.8 / (0.75 * len(symbol))))
        return max(8, size)

    # -- public API (thread safe) -----------------------------------------
    def draw(self, highlight=(), style='flash'):
        self._queue.put(('draw', (tuple(highlight), style)))

    def message(self, text):
        self._queue.put(('message', text))

    def set_output(self, text):
        self._queue.put(('output', text))

    def close(self):
        self._closed.set()

    # -- tk thread ---------------------------------------------------------
    def _on_close(self):
        self._closed.set()

    def pump(self):
        """Apply queued draw commands; call this from the tk thread."""
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == 'draw':
                    self._apply_draw(*payload)
                elif kind == 'message':
                    self.canvas.itemconfigure(self._message, text=payload)
                elif kind == 'output':
                    self.canvas.itemconfigure(self._output, text='%s_' % payload)
        except queue.Empty:
            pass

    def _apply_draw(self, highlight, style):
        highlight = set(highlight)
        fg = STYLES.get(style, STYLES['flash'])[0]
        for cell, item in self._items.items():
            self.canvas.itemconfigure(item, fill=fg if cell in highlight
                                      else STYLES['idle'][0])

    def mainloop(self, worker=None):
        def tick():
            self.pump()
            if self._closed.is_set() or (worker is not None and not worker.is_alive()):
                self.root.quit()
            else:
                self.root.after(10, tick)
        self.root.after(10, tick)
        try:
            self.root.mainloop()
        finally:
            if self.owns_root:
                try:
                    self.root.destroy()
                except Exception:
                    pass


def make_renderer(kind, matrix, **kwargs):
    """Build a renderer by name, falling back to text when tk is unavailable."""
    if kind == 'tk':
        try:
            return TkRenderer(matrix, **kwargs)
        except Exception as err:
            print('tk display unavailable (%s); falling back to text' % err)
            return TextRenderer(matrix)
    return {'text': TextRenderer, 'headless': HeadlessRenderer,
            'none': Renderer}[kind](matrix)
