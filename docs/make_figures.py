# -*- coding: utf-8 -*-
"""Draw the explanatory figures for the sensors page of the tutorial.

Run ``python3 make_figures.py`` from this directory to redraw them all, or
name the ones you want: ``python3 make_figures.py dipole artifacts``.
The waveforms are generated, not traced, so editing a number here and
rerunning is the way to change a figure. The other SVGs in assets/img were
drawn by hand and are not produced by this script.
"""
import io, math, os
import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'img') + os.sep

FONT = '-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif'
STYLE = """
    .t{fill:#16202c;font-size:14px;font-weight:600}
    .s{fill:#64748b;font-size:12px}
    .tiny{fill:#64748b;font-size:10.5px}
    .lbl{fill:#16202c;font-size:11.5px;font-weight:600}
    .mono{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:11px;fill:#16202c}
"""
BLUE, ORANGE, RED, GREEN, GREY = '#1f6feb', '#d97706', '#c2410c', '#15803d', '#94a3b8'


def svg(w, h, title, body, style=''):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" font-family="%s">\n'
            '  <rect width="%d" height="%d" rx="12" fill="#f6f8fa"/>\n'
            '  <style>%s%s</style>\n'
            '  <defs>\n'
            '    <marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="%s"/></marker>\n'
            '    <marker id="ao" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="%s"/></marker>\n'
            '    <marker id="ag" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#64748b"/></marker>\n'
            '  </defs>\n'
            '  <text x="30" y="34" class="t" font-size="16">%s</text>\n%s\n</svg>\n'
            % (w, h, FONT, w, h, STYLE, style, BLUE, ORANGE, title, body))


def panel(x, y, w, h, label=None, sub=None):
    out = '<rect x="%g" y="%g" width="%g" height="%g" rx="10" fill="#fff" stroke="#c9d3de"/>' % (x, y, w, h)
    if label:
        out += '\n<text x="%g" y="%g" class="lbl">%s</text>' % (x + 16, y + 26, label)
    if sub:
        out += '\n<text x="%g" y="%g" class="tiny">%s</text>' % (x + 16, y + 43, sub)
    return out


def trace(xs, ys, color=BLUE, width=1.6, dash=None):
    pts = ' '.join('%.1f,%.1f' % (x, y) for x, y in zip(xs, ys))
    d = ' stroke-dasharray="%s"' % dash if dash else ''
    return '<polyline points="%s" fill="none" stroke="%s" stroke-width="%g"%s/>' % (pts, color, width, d)


def text(x, y, s, cls='tiny', anchor='start', extra=''):
    return '<text x="%g" y="%g" class="%s" text-anchor="%s"%s>%s</text>' % (x, y, cls, anchor, extra, s)


def arrow(x1, y1, x2, y2, color=BLUE, width=1.6, marker='a', dash=None):
    d = ' stroke-dasharray="%s"' % dash if dash else ''
    return '<path d="M%g %g L%g %g" stroke="%s" stroke-width="%g" fill="none" marker-end="url(#%s)"%s/>' % (
        x1, y1, x2, y2, color, width, marker, d)


def frame(x, y, w, h, fill='#fbfdff'):
    return '<rect x="%g" y="%g" width="%g" height="%g" rx="6" fill="%s" stroke="#dbe3ec"/>' % (x, y, w, h, fill)


def highpass(x, dt, fc):
    rc = 1.0 / (2 * math.pi * fc)
    a = rc / (rc + dt)
    y = np.zeros_like(x)
    for n in range(1, len(x)):
        y[n] = a * (y[n - 1] + x[n] - x[n - 1])
    return y


def bump(t, centre=0.42, width=0.075):
    return np.exp(-0.5 * ((t - centre) / width) ** 2)


# --------------------------------------------------------------------------
# 1. how a dipole is made
# --------------------------------------------------------------------------
def fig_dipole():
    W, H = 960, 470
    b = []
    px, py, pw, ph = 30, 56, 285, 386
    b.append(panel(px, py, pw, ph, '1 · one cell, for a few thousandths of a second'))
    g = []
    # neuron: apical dendrite up, triangular soma, basal dendrites, axon down
    g.append('<path d="M72 150 L72 88" stroke="#334155" stroke-width="2.4" fill="none"/>')
    g.append('<path d="M72 96 L54 72 M72 96 L90 72 M72 88 L72 64 M54 72 L46 58 M90 72 L98 58" '
             'stroke="#334155" stroke-width="1.6" fill="none"/>')
    g.append('<path d="M56 186 L88 186 L72 148 z" fill="#e8eef7" stroke="#334155" stroke-width="2"/>')
    g.append('<path d="M56 186 L36 204 M56 186 L44 210 M88 186 L108 204 M88 186 L100 210" '
             'stroke="#334155" stroke-width="1.5" fill="none"/>')
    g.append('<path d="M72 186 L72 268" stroke="#334155" stroke-width="1.8" fill="none"/>')
    g.append(text(72, 286, 'one cortical cell', 'tiny', 'middle'))
    # ions in at the top
    g.append(arrow(30, 84, 62, 90, BLUE, 1.6))
    g.append('<text x="14" y="80" class="ion" fill="%s" font-size="11" font-weight="700">Na+</text>' % BLUE)
    g.append(arrow(30, 108, 62, 102, BLUE, 1.6))
    # ions out lower down
    g.append(arrow(96, 170, 126, 160, ORANGE, 1.6, marker='ao'))
    g.append(arrow(96, 196, 126, 206, ORANGE, 1.6, marker='ao'))
    # the loop through the fluid
    g.append('<path d="M132 182 C176 176 176 104 128 96" stroke="#94a3b8" stroke-width="1.4" '
             'fill="none" stroke-dasharray="4 3" marker-end="url(#ag)"/>')
    g.append(text(150, 140, 'the loop closes', 'tiny', 'middle'))
    g.append(text(150, 153, 'through the fluid', 'tiny', 'middle'))
    # charge signs
    g.append('<circle cx="96" cy="96" r="9" fill="#e8f0fe" stroke="%s"/>' % BLUE)
    g.append('<text x="96" y="100" text-anchor="middle" font-size="13" font-weight="700" fill="%s">&#8722;</text>' % BLUE)
    g.append('<circle cx="96" cy="222" r="9" fill="#fdeee0" stroke="%s"/>' % ORANGE)
    g.append('<text x="96" y="227" text-anchor="middle" font-size="13" font-weight="700" fill="%s">+</text>' % ORANGE)
    b.append('<g transform="translate(%d,%d)">%s</g>' % (px, py, '\n'.join(g)))
    # captions under panel 1
    cap = []
    cap.append(text(16, 316, 'A message arrives near the top and positive ions', 'tiny'))
    cap.append(text(16, 329, 'rush IN; a little lower down they leak back OUT.', 'tiny'))
    cap.append(text(16, 349, 'So one end of the cell is briefly negative and the', 'tiny'))
    cap.append(text(16, 362, 'other positive: a tiny battery, a few millionths', 'tiny'))
    cap.append(text(16, 375, 'of a volt, lasting a few thousandths of a second.', 'tiny'))
    b.append('<g transform="translate(%d,%d)">%s</g>' % (px, py, '\n'.join(cap)))

    # panel 2 -- alignment
    px2 = 337
    b.append(panel(px2, py, pw, ph, '2 · why we can detect it at all'))
    g = []
    g.append(frame(16, 52, 253, 136))
    g.append(text(28, 72, 'cortex cells, all facing the same way', 'tiny'))
    for i in range(9):
        x = 32 + i * 18
        g.append(arrow(x, 160, x, 100, BLUE, 2.2))
    g.append(text(28, 178, 'their little batteries point the same way &#8594; they ADD', 'tiny'))
    g.append('<path d="M210 168 L210 92" stroke="%s" stroke-width="9" fill="none" marker-end="url(#a)"/>' % BLUE)
    g.append(text(228, 134, 'big', 'lbl'))

    g.append(frame(16, 206, 253, 136))
    g.append(text(28, 226, 'cells pointing every which way, as in deeper tissue', 'tiny'))
    rng = np.random.RandomState(4)
    for i in range(9):
        x = 32 + i * 18
        ang = rng.uniform(0, 2 * math.pi)
        g.append(arrow(x, 292, x + 24 * math.cos(ang), 292 + 24 * math.sin(ang), GREY, 1.8, marker='ag'))
    g.append(text(28, 332, 'they point in all directions &#8594; they CANCEL', 'tiny'))
    g.append('<circle cx="206" cy="286" r="5" fill="%s"/>' % GREY)
    g.append(text(220, 290, 'nothing', 'lbl'))
    g.append(text(16, 366, 'Tens of thousands of aligned cells doing the same thing', 'tiny'))
    g.append(text(16, 379, 'at once is what makes a measurable signal.', 'tiny'))
    b.append('<g transform="translate(%d,%d)">%s</g>' % (px2, py, '\n'.join(g)))

    # panel 3 -- out through the head
    px3 = 644
    pw3 = 286
    b.append(panel(px3, py, pw3, ph, '3 · out through the head'))
    g = []
    layers = [(84, 26, '#f6e7db', '#d9c7b8', 'scalp'),
              (110, 34, '#e7e7ea', '#cdced4', 'skull &#8212; a poor conductor'),
              (144, 20, '#e2eef0', '#c3d8dc', 'fluid'),
              (164, 60, '#f0e2ef', '#d8bdd6', 'cortex')]
    for (y0, hh, fill, stroke, name) in layers:
        g.append('<rect x="18" y="%g" width="250" height="%g" fill="%s" stroke="%s"/>' % (y0, hh, fill, stroke))
        g.append(text(26, y0 + hh / 2 + 4, name, 'tiny'))
    # the dipole down in the cortex
    g.append('<circle cx="143" cy="182" r="7" fill="#e8f0fe" stroke="%s"/>' % BLUE)
    g.append('<text x="143" y="186" text-anchor="middle" font-size="11" font-weight="700" fill="%s">&#8722;</text>' % BLUE)
    g.append('<circle cx="143" cy="208" r="7" fill="#fdeee0" stroke="%s"/>' % ORANGE)
    g.append('<text x="143" y="212" text-anchor="middle" font-size="11" font-weight="700" fill="%s">+</text>' % ORANGE)
    g.append(text(158, 196, 'many thousands,', 'tiny'))
    g.append(text(158, 209, 'all lined up', 'tiny'))
    # spreading field lines
    for dx, curve in [(-96, -60), (-56, -34), (-20, -12), (20, 12), (56, 34), (96, 60)]:
        g.append('<path d="M143 174 C%g 144 %g 116 %g 90" stroke="#b9c6d6" stroke-width="1.3" '
                 'fill="none" stroke-dasharray="4 4"/>' % (143 + curve, 143 + dx, 143 + dx))
    g.append('<path d="M143 172 L143 94" stroke="#b9c6d6" stroke-width="1.3" fill="none" stroke-dasharray="4 4"/>')
    # electrode on top
    g.append('<rect x="118" y="66" width="50" height="16" rx="5" fill="#dbe7fb" stroke="%s"/>' % BLUE)
    g.append(text(143, 78, 'electrode', 'tiny', 'middle'))
    g.append(arrow(196, 62, 172, 70, GREY, 1.3, marker='ag'))
    g.append(text(200, 58, 'about 5 &#181;V arrives here', 'tiny', 'end'))
    g.append(text(18, 254, 'The current does not run along a wire: it spreads', 'tiny'))
    g.append(text(18, 267, 'through fluid, skull and scalp the way heat spreads', 'tiny'))
    g.append(text(18, 280, 'through a pan. So an electrode never sees one small', 'tiny'))
    g.append(text(18, 293, 'spot of brain, but a blurred region a few cm across.', 'tiny'))
    g.append(frame(18, 308, 250, 64, '#f6f8fa'))
    g.append(text(30, 329, 'Inside the head the current is carried by ions.', 'tiny'))
    g.append(text(30, 342, 'In the cable it is carried by electrons. The', 'tiny'))
    g.append(text(30, 355, 'electrode is what translates between them.', 'tiny'))
    b.append('<g transform="translate(%d,%d)">%s</g>' % (px3, py, '\n'.join(g)))
    return svg(W, H, 'where the signal comes from', '\n'.join(b))


# --------------------------------------------------------------------------
# 2. everything on one scale
# --------------------------------------------------------------------------
def fig_scale():
    W, H = 960, 340
    lo, hi = -7.0, 1.0          # log10 volts: 0.1 uV .. 10 V
    x0, x1, axis_y = 70, 900, 250

    def X(v):
        return x0 + (math.log10(v) - lo) / (hi - lo) * (x1 - x0)

    b = [panel(30, 56, 900, 236)]
    b.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#94a3b8" stroke-width="1.5"/>' % (x0, axis_y, x1, axis_y))
    ticks = [(1e-7, '0.1 &#181;V'), (1e-6, '1 &#181;V'), (1e-5, '10 &#181;V'), (1e-4, '100 &#181;V'),
             (1e-3, '1 mV'), (1e-2, '10 mV'), (1e-1, '100 mV'), (1.0, '1 V'), (10.0, '10 V')]
    for v, lab in ticks:
        b.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#c9d3de"/>' % (X(v), axis_y, X(v), axis_y + 6))
        b.append(text(X(v), axis_y + 21, lab, 'tiny', 'middle'))
    # the band of ongoing EEG
    b.append('<rect x="%g" y="%g" width="%g" height="%g" fill="#e8f0fe" stroke="%s" stroke-dasharray="3 3"/>'
             % (X(1e-5), axis_y - 92, X(1e-4) - X(1e-5), 92, BLUE))
    b.append(text((X(1e-5) + X(1e-4)) / 2, axis_y - 100, 'the ongoing EEG', 'lbl', 'middle'))
    b.append(text((X(1e-5) + X(1e-4)) / 2, axis_y - 74, '10&#8211;100 &#181;V', 'tiny', 'middle'))

    items = [(5e-7, 50, 'the amplifier&#8217;s own hiss', GREY),
             (5e-6, 138, 'the P300 you are hunting &#8212; 5 &#181;V', RED),
             (3e-4, 54, 'a big eye blink', GREY),
             (2e-2, 110, 'mains hum floating the whole body', GREY),
             (0.22, 160, 'each electrode&#8217;s own private voltage', ORANGE),
             (1.5, 58, 'an AA battery', GREY)]
    for v, h, lab, colour in items:
        x = X(v)
        b.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="%g"/>'
                 % (x, axis_y, x, axis_y - h, colour, 2.4 if colour in (RED, ORANGE) else 1.4))
        b.append('<circle cx="%g" cy="%g" r="%g" fill="%s"/>' % (x, axis_y - h, 4.5 if colour == RED else 3.5, colour))
        cls = 'lbl' if colour in (RED, ORANGE) else 'tiny'
        anchor = 'middle'
        if x < 160:
            anchor = 'start'
            x = x - 6
        if x > 820:
            anchor = 'end'
            x = x + 6
        b.append(text(x, axis_y - h - 12, lab, cls, anchor,
                      ' fill="%s"' % colour if colour in (RED, ORANGE) else ''))
    b.append(text(70, 322, 'Each step along this line is ten times bigger than the one before. The P300 sits a hundred thousand times '
                  'below the electrode&#8217;s own voltage &#8212; which is why every channel is a subtraction.', 'tiny'))
    return svg(W, H, 'how small is five microvolts?', '\n'.join(b))


# --------------------------------------------------------------------------
# 3. which signals get through which door
# --------------------------------------------------------------------------
def fig_door_frequency():
    W, H = 960, 420
    b = []
    # ---- left: how much gets through, against speed
    px, py, pw, ph = 30, 56, 450, 330
    b.append(panel(px, py, pw, ph, 'how much of a signal gets through'))
    ox, oy, aw, ah = px + 64, py + 262, 340, 176
    b.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#94a3b8"/>' % (ox, oy, ox + aw, oy))
    b.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#94a3b8"/>' % (ox, oy, ox, oy - ah))
    flo, fhi = -1.0, 2.0

    def FX(f):
        return ox + (math.log10(f) - flo) / (fhi - flo) * aw
    for f, lab in [(0.1, '0.1'), (1, '1'), (10, '10'), (100, '100 Hz')]:
        b.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#c9d3de"/>' % (FX(f), oy, FX(f), oy + 5))
        b.append(text(FX(f), oy + 19, lab, 'tiny', 'middle'))
    b.append(text(ox + aw / 2, oy + 38, 'how fast the signal wiggles &#8212; cycles per second', 'tiny', 'middle'))
    for frac, lab in [(0, '0'), (0.5, 'half'), (1.0, 'all')]:
        b.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#c9d3de"/>' % (ox - 5, oy - frac * ah, ox, oy - frac * ah))
        b.append(text(ox - 10, oy - frac * ah + 4, lab, 'tiny', 'end'))
    # the P300 band
    b.append('<rect x="%g" y="%g" width="%g" height="%g" fill="#eef4ff" stroke="%s" stroke-dasharray="3 3"/>'
             % (FX(0.5), oy - ah, FX(10) - FX(0.5), ah, '#b9cdf0'))
    b.append(text((FX(0.5) + FX(10)) / 2, oy - 14, 'where the P300 lives', 'tiny', 'middle'))
    fs = np.logspace(flo, fhi, 200)
    xs = [FX(f) for f in fs]
    b.append(trace(xs, [oy - ah * 0.985 for _ in fs], BLUE, 2.2))
    gold = fs / np.sqrt(fs ** 2 + 1.0 ** 2)
    b.append(trace(xs, [oy - ah * g for g in gold], ORANGE, 2.2))
    b.append(text(FX(0.105), oy - ah * 0.985 - 10, 'silver&#8211;silver chloride &#8212; revolving door', 'tiny', 'start',
                  ' fill="%s"' % BLUE))
    b.append('<path d="M%g %g L%g %g" stroke="#e2b98a" stroke-width="1"/>'
             % (FX(0.16), oy - ah * 0.36, FX(0.3), oy - ah * 0.287))
    b.append(text(FX(0.105), oy - ah * 0.40, 'gold &#8212; glass door', 'tiny', 'start', ' fill="%s"' % ORANGE))
    b.append(text(FX(11), oy - ah * 0.86, 'alpha, 10 Hz:', 'tiny'))
    b.append(text(FX(11), oy - ah * 0.86 + 13, 'both fine', 'tiny'))
    # ---- right: the same P300 through both
    px2, pw2 = 502, 428
    b.append(panel(px2, py, pw2, ph, 'the same P300, through both electrodes'))
    t = np.linspace(0, 1.4, 700)
    dt = t[1] - t[0]
    sig = bump(t)
    gold_out = highpass(sig, dt, 1.0)
    bx, bw = px2 + 30, pw2 - 60
    xs = bx + (t / t[-1]) * bw
    for i, (y0, data, colour, name, note) in enumerate([
            (py + 112, sig, BLUE, 'through Ag/AgCl', 'the bump arrives with its shape intact'),
            (py + 236, gold_out, ORANGE, 'through gold', 'the slow part is lost: it droops and undershoots')]):
        b.append(frame(bx - 10, y0 - 62, bw + 20, 96))
        b.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#dbe3ec"/>' % (bx - 10, y0, bx + bw + 10, y0))
        b.append(trace(xs, y0 - 52 * data, colour, 2.0))
        if i == 1:
            b.append(trace(xs, y0 - 52 * sig, GREY, 1.2, dash='4 4'))
        b.append(text(bx - 4, y0 - 48, name, 'lbl', 'start', ' fill="%s"' % colour))
        b.append(text(bx - 4, y0 + 52, note, 'tiny'))
    b.append(text(bx - 4, py + 306, 'Grey dashed: what was actually there. A P300 is a slow shape, so an', 'tiny'))
    b.append(text(bx - 4, py + 319, 'electrode that blocks slow changes distorts exactly the thing you want.', 'tiny'))
    return svg(W, H, 'why the door type matters', '\n'.join(b))


# --------------------------------------------------------------------------
# 4. impedance: low, and matched
# --------------------------------------------------------------------------
def fig_impedance():
    W, H = 960, 430
    b = []
    px, py, pw, ph = 30, 56, 300, 340
    b.append(panel(px, py, pw, ph, 'almost no signal is lost&#8230;'))
    g = []
    g.append(text(16, 62, 'The electrode and the amplifier input sit', 'tiny'))
    g.append(text(16, 75, 'one behind the other, and they share the', 'tiny'))
    g.append(text(16, 88, 'voltage between them in proportion.', 'tiny'))
    g.append('<circle cx="42" cy="150" r="20" fill="#e8f0fe" stroke="%s"/>' % BLUE)
    g.append(text(42, 154, 'head', 'tiny', 'middle'))
    g.append('<path d="M62 150 L92 150" stroke="#64748b" stroke-width="1.6" fill="none"/>')
    g.append('<rect x="92" y="136" width="86" height="28" rx="5" fill="#fff" stroke="#64748b"/>')
    g.append(text(135, 154, 'electrode 20 k&#937;', 'tiny', 'middle'))
    g.append('<path d="M178 150 L212 150" stroke="#64748b" stroke-width="1.6" fill="none"/>')
    g.append('<rect x="212" y="120" width="60" height="60" rx="5" fill="#fff" stroke="#64748b"/>')
    g.append(text(242, 144, 'amplifier', 'tiny', 'middle'))
    g.append(text(242, 158, 'input', 'tiny', 'middle'))
    g.append(text(242, 172, '100 M&#937;', 'tiny', 'middle'))
    g.append('<path d="M212 196 L272 196" stroke="#94a3b8" stroke-width="1.2" fill="none"/>')
    g.append(frame(16, 216, 268, 60, '#f6f8fa'))
    g.append(text(30, 240, '20 k&#937; against 100 M&#937; keeps 99.98 % of', 'tiny'))
    g.append(text(30, 253, 'the signal. Losing signal is <tspan font-weight="700">not</tspan> why you', 'tiny'))
    g.append(text(30, 266, 'chase low impedance.', 'tiny'))
    g.append(text(16, 300, 'You chase it because a bigger resistance', 'tiny'))
    g.append(text(16, 313, 'hisses more &#8212; and because of this:', 'tiny'))
    b.append('<g transform="translate(%d,%d)">%s</g>' % (px, py, '\n'.join(g)))

    # right: matched vs mismatched
    t = np.linspace(0, 0.3, 600)
    hum = np.sin(2 * math.pi * 50 * t)
    eeg = 0.55 * bump(t, 0.16, 0.022) - 0.2 * bump(t, 0.08, 0.02)
    cases = [(352, 'matched &#8212; 5 k&#937; and 5 k&#937;', 1.0, 1.0, 'the hum is identical on both inputs,',
              'so subtracting removes it completely', GREEN),
             (656, 'mismatched &#8212; 5 k&#937; and 200 k&#937;', 1.0, 0.55, 'the hum arrives at different sizes,',
              'so some of it survives the subtraction', RED)]
    for (cx, title, ga, gb, note1, note2, verdict) in cases:
        cw = 274
        b.append(panel(cx, py, cw, ph, title))
        bx, bw = cx + 24, cw - 48
        xs = bx + (t / t[-1]) * bw
        rows = [(py + 96, ga * hum + eeg, 'electrode', BLUE),
                (py + 176, gb * hum, 'reference', BLUE),
                (py + 276, (ga - gb) * hum + eeg, 'what is recorded (the difference)', verdict)]
        for (y0, data, name, colour) in rows:
            b.append(text(bx, y0 - 40, name, 'tiny'))
            b.append(frame(bx, y0 - 34, bw, 60))
            b.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#e6ecf3"/>' % (bx, y0 - 4, bx + bw, y0 - 4))
            b.append(trace(xs, y0 - 4 - 22 * data, colour, 1.4))
        b.append(text(bx, py + 306, note1, 'tiny'))
        b.append(text(bx, py + 319, note2, 'tiny'))
    return svg(W, H, 'impedance: why low, and why matched', '\n'.join(b))


# --------------------------------------------------------------------------
# 5. what trouble looks like
# --------------------------------------------------------------------------
def fig_artifacts():
    rng = np.random.RandomState(7)
    t = np.linspace(0, 4, 1200)

    def eeg(seed, amp=1.0):
        r = np.random.RandomState(seed)
        y = np.zeros_like(t)
        for f, a in [(3.1, 0.5), (6.3, 0.35), (9.8, 0.55), (13.5, 0.2), (21.0, 0.12)]:
            y += a * np.sin(2 * math.pi * f * t + r.uniform(0, 6.28))
        return amp * y / 1.7

    good = eeg(1)
    pop = eeg(2) * 0.8 + 2.6 * np.exp(-np.maximum(t - 1.6, 0) / 0.55) * (t > 1.6)
    drift = eeg(3) * 0.8 + 1.7 * np.sin(2 * math.pi * 0.16 * t + 0.6)
    humline = eeg(4) * 0.7 + 1.1 * np.sin(2 * math.pi * 50 * t)
    muscle = eeg(5) * 0.7 + 2.1 * np.exp(-0.5 * ((t - 2.0) / 0.35) ** 2) * np.sin(2 * math.pi * 88 * t)
    blink = eeg(6) * 0.7 - 2.6 * np.exp(-0.5 * ((t - 1.3) / 0.11) ** 2) - 2.2 * np.exp(-0.5 * ((t - 2.9) / 0.11) ** 2)
    bridge = eeg(7)
    flat = 0.06 * rng.randn(len(t))

    cells = [('healthy EEG', good, None, 'irregular, a few tens of microvolts, no two seconds alike', GREEN),
             ('electrode pop', pop, None, 'a sudden step, then a slow slide back &#8212; the electrode moved', RED),
             ('slow drift', drift, None, 'wandering over seconds; drying gel or sweat', ORANGE),
             ('mains hum', humline, None, 'a dense, perfectly regular buzz; a loose reference or mismatched impedances', ORANGE),
             ('muscle', muscle, None, 'a fast, spiky burst &#8212; a clenched jaw, not brain', ORANGE),
             ('eye blink', blink, None, 'large, smooth dips over the front of the head', ORANGE),
             ('bridged pair', bridge, bridge * 0.97 + 0.08, 'two channels almost identical &#8212; gel has spread between them', RED),
             ('dead channel', flat, None, 'no signal at all &#8212; unplugged, or the amplifier is not running', RED)]
    W, H = 960, 520
    b = []
    cw, ch = 217, 196
    for i, (name, data, second, note, colour) in enumerate(cells):
        col, row = i % 4, i // 4
        x = 30 + col * (cw + 15)
        y = 56 + row * (ch + 22)
        b.append(panel(x, y, cw, ch))
        b.append(text(x + 14, y + 24, name, 'lbl', 'start', ' fill="%s"' % colour))
        bx, bw, by = x + 14, cw - 28, y + 96
        b.append(frame(bx, by - 58, bw, 84))
        xs = bx + (t / t[-1]) * bw
        if second is not None:
            b.append(trace(xs, by - 16 - 11 * np.clip(data, -3, 3), BLUE, 1.2))
            b.append(trace(xs, by - 2 + 11 * np.clip(second, -3, 3) * 0 - 11 * np.clip(second, -3, 3) + 14, ORANGE, 1.2))
        else:
            b.append(trace(xs, by - 16 - 13 * np.clip(data, -3.2, 3.2), BLUE, 1.2))
        words = note.split(' ')
        lines, cur = [], ''
        for w in words:
            if len(cur) + len(w) + 1 > 34:
                lines.append(cur)
                cur = w
            else:
                cur = (cur + ' ' + w).strip()
        lines.append(cur)
        for j, line in enumerate(lines[:3]):
            b.append(text(x + 14, y + 138 + j * 13, line, 'tiny'))
    return svg(W, H, 'what trouble looks like on the screen', '\n'.join(b))


# --------------------------------------------------------------------------
# 6. from a wave to numbers
# --------------------------------------------------------------------------
def fig_sampling():
    W, H = 960, 330
    t = np.linspace(0, 1, 800)
    wave = (0.9 * np.sin(2 * math.pi * 3.2 * t) + 0.45 * np.sin(2 * math.pi * 8.5 * t + 1.1)
            + 0.25 * np.sin(2 * math.pi * 1.4 * t + 0.4))
    b = []
    px, py, ph = 30, 56, 240
    pw = 300
    b.append(panel(px, py, pw, ph, '1 &#183; a voltage that never stops changing'))
    bx, bw, by = px + 22, pw - 44, py + 122
    xs = bx + t * bw
    b.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#e6ecf3"/>' % (bx, by, bx + bw, by))
    b.append(trace(xs, by - 32 * wave, BLUE, 2.0))
    b.append(text(px + 16, py + 208, 'What comes out of the amplifier is a', 'tiny'))
    b.append(text(px + 16, py + 221, 'smooth voltage, changing all the time.', 'tiny'))

    px2 = 352
    b.append(panel(px2, py, pw, ph, '2 &#183; measured, over and over'))
    bx2 = px2 + 22
    xs2 = bx2 + t * bw
    b.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#e6ecf3"/>' % (bx2, by, bx2 + bw, by))
    b.append(trace(xs2, by - 32 * wave, '#c7d5e6', 1.4))
    ts = np.linspace(0, 1, 26)
    ws = np.interp(ts, t, wave)
    for tt, ww in zip(ts, ws):
        x = bx2 + tt * bw
        b.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="1.1"/>' % (x, by, x, by - 32 * ww, BLUE))
        b.append('<circle cx="%g" cy="%g" r="2.6" fill="%s"/>' % (x, by - 32 * ww, BLUE))
    b.append(text(px2 + 16, py + 208, '512 times a second the converter reads', 'tiny'))
    b.append(text(px2 + 16, py + 221, 'the voltage and writes down a number.', 'tiny'))

    px3 = 674
    pw3 = 256
    b.append(panel(px3, py, pw3, ph, '3 &#183; a stream of numbers'))
    vals = ['  2.41', ' -3.88', '  7.02', ' 11.64', '  4.19', ' -6.50', '-12.07']
    for i, v in enumerate(vals):
        b.append('<text x="%g" y="%g" class="mono">%s &#181;V</text>' % (px3 + 24, py + 72 + i * 19, v))
    b.append(arrow(px3 + 150, py + 126, px3 + 210, py + 126, GREY, 1.4, marker='ag'))
    b.append(text(px3 + 180, py + 114, 'to LSL', 'tiny', 'middle'))
    b.append(text(px3 + 16, py + 208, '24 bits &#8212; about 16 million steps &#8212; so a', 'tiny'))
    b.append(text(px3 + 16, py + 221, 'single microvolt is still several steps.', 'tiny'))
    return svg(W, H, 'from a wave to numbers', '\n'.join(b))



# --------------------------------------------------------------------------
# 7. capping up, step by step
# --------------------------------------------------------------------------
def fig_capping():
    W, H = 960, 330
    b = []
    pw, ph, py = 172, 250, 56
    xs = [30, 215, 400, 585, 770]
    titles = ['1 &#183; find Cz', '2 &#183; seat the cap', '3 &#183; part and abrade',
              '4 &#183; gel, then stop', '5 &#183; check impedance']
    caps = [['Measure from the bridge of the', 'nose to the bump at the back of', 'the skull. Half way is Cz.'],
            ['Line the cap&#8217;s middle hole up', 'with that mark and pull it down', 'evenly, front to back.'],
            ['Part the hair through the hole', 'with a blunt needle and rub', 'gently until the skin pinks.'],
            ['Fill until the number settles.', 'More gel does not help &#8212; it', 'bridges to the next electrode.'],
            ['Low and similar to each other.', 'Write them down, and check', 'again after half an hour.']]
    for i, x in enumerate(xs):
        b.append(panel(x, py, pw, ph, titles[i]))
        g = []
        if i == 0:
            g.append('<path d="M40 112 a44 44 0 1 1 88 0 a44 44 0 1 1 -88 0" fill="#f6e7db" stroke="#d9c7b8"/>')
            g.append('<path d="M40 112 q-9 6 -1 13" fill="none" stroke="#d9c7b8" stroke-width="2"/>')
            g.append('<path d="M40 112 L128 112" stroke="%s" stroke-width="1.4" stroke-dasharray="4 3"/>' % BLUE)
            g.append('<circle cx="84" cy="68" r="6" fill="#dbe7fb" stroke="%s"/>' % BLUE)
            g.append(text(84, 58, 'Cz', 'tiny', 'middle'))
            g.append('<path d="M84 106 L84 76" stroke="%s" stroke-width="1.2" stroke-dasharray="3 3"/>' % BLUE)
            g.append('<path d="M40 106 L40 118 M128 106 L128 118" stroke="%s" stroke-width="1.4"/>' % BLUE)
            g.append(text(84, 172, 'half way along the dashed line', 'tiny', 'middle'))
        elif i == 1:
            g.append('<circle cx="84" cy="104" r="46" fill="#eef3f9" stroke="#b9c6d6"/>')
            g.append('<path d="M84 58 l-7 -11 l14 0 z" fill="#b9c6d6"/>')
            for (dx, dy) in [(0, 0), (-24, -14), (24, -14), (-24, 14), (24, 14), (0, -28), (0, 28), (-44, 0), (44, 0)]:
                r = 6 if (dx or dy) else 8
                fill = '#dbe7fb' if not (dx or dy) else '#fff'
                g.append('<circle cx="%g" cy="%g" r="%g" fill="%s" stroke="#90a4bd"/>' % (84 + dx, 104 + dy, r, fill))
            g.append(text(84, 108, 'Cz', 'tiny', 'middle'))
            g.append(text(84, 168, 'seen from above', 'tiny', 'middle'))
        elif i == 2:
            g.append('<circle cx="84" cy="106" r="42" fill="#fff" stroke="#90a4bd"/>')
            g.append('<path d="M52 128 q14 -22 32 -10 q20 12 32 -12" stroke="#c7b39c" stroke-width="2" fill="none"/>')
            g.append('<path d="M50 140 q18 -26 34 -12 q18 14 34 -14" stroke="#c7b39c" stroke-width="2" fill="none"/>')
            g.append('<path d="M120 62 L92 96" stroke="#64748b" stroke-width="3"/>')
            g.append('<circle cx="90" cy="99" r="4" fill="#f7d7d7" stroke="#d98a8a"/>')
            g.append(text(84, 168, 'through the hole in the cap', 'tiny', 'middle'))
        elif i == 3:
            g.append('<rect x="56" y="52" width="26" height="44" rx="4" fill="#fff" stroke="#64748b"/>')
            g.append('<rect x="58" y="70" width="22" height="26" fill="#dbe7fb"/>')
            g.append('<path d="M69 96 L69 112" stroke="#64748b" stroke-width="3"/>')
            g.append('<path d="M46 118 a24 14 0 0 0 48 0 z" fill="#dbe7fb" stroke="%s"/>' % BLUE)
            g.append('<path d="M42 118 L98 118" stroke="#90a4bd" stroke-width="2"/>')
            g.append(text(72, 172, 'enough to fill the cup', 'tiny', 'middle'))
            g.append('<path d="M126 88 L142 104 M142 88 L126 104" stroke="%s" stroke-width="2"/>' % RED)
            g.append(text(134, 124, 'not so much', 'tiny', 'middle'))
            g.append(text(134, 137, 'it spreads', 'tiny', 'middle'))
        else:
            names = ['Fz', 'Cz', 'Pz', 'Oz', 'P3', 'P4', 'REF', 'GND']
            vals = ['3', '2', '4', '6', '3', '41', '2', '3']
            cols = [GREEN, GREEN, GREEN, GREEN, GREEN, ORANGE, GREEN, GREEN]
            for j, (nm, v, c) in enumerate(zip(names, vals, cols)):
                cx, cy = 26 + (j % 2) * 74, 58 + (j // 2) * 26
                g.append('<rect x="%g" y="%g" width="66" height="20" rx="4" fill="%s" stroke="%s" opacity="0.92"/>'
                         % (cx, cy, '#eefaf1' if c == GREEN else '#fdf3e6', c))
                g.append(text(cx + 8, cy + 14, nm, 'tiny'))
                g.append('<text x="%g" y="%g" class="tiny" text-anchor="end">%s k&#937;</text>' % (cx + 60, cy + 14, v))
            g.append(text(84, 178, 'one is far worse &#8212; redo it', 'tiny', 'middle'))
        b.append('<g transform="translate(%d,%d)">%s</g>' % (x, py, '\n'.join(g)))
        for j, line in enumerate(caps[i]):
            b.append(text(x + 14, py + 196 + j * 13, line, 'tiny'))
    return svg(W, H, 'capping up, step by step', '\n'.join(b))


FIGS = {'dipole': fig_dipole, 'scale-ladder': fig_scale, 'door-frequency': fig_door_frequency,
        'impedance': fig_impedance, 'artifacts': fig_artifacts, 'sampling': fig_sampling,
        'capping': fig_capping}

if __name__ == '__main__':
    import sys
    names = sys.argv[1:] or sorted(FIGS)
    for name in names:
        data = FIGS[name]()
        io.open(OUT + name + '.svg', 'w', encoding='utf-8').write(data)
        print('wrote %s.svg (%d bytes)' % (name, len(data)))
