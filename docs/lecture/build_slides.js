/*
 * Builds the lecture deck (pyspeller-lecture.pptx), including the speaker notes.
 *
 *   npm install pptxgenjs
 *   node build_slides.js
 *
 * Screenshots and plots come from ../assets/img (the tutorial figures).  The
 * five diagrams that exist only as SVG are used here as PNG, in figures/;
 * regenerate them with `python3 render_figures.py` after editing the SVGs.
 */
const path = require('path');
const pptxgen = require('pptxgenjs');
const IMG = path.join(__dirname, '..', 'assets', 'img') + path.sep;
const GEN = path.join(__dirname, 'figures') + path.sep;
const OUT = __dirname + path.sep;

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';            // 13.333 x 7.5
pres.author = 'pyspeller';
pres.title = 'pyspeller: inside a working P300 speller';

const W = 13.333, H = 7.5;
const DARK = '141B34', PRIMARY = '2F3E9E', ACCENT = '00A884', AMBER = 'C77700';
const TINT = 'EEF1F9', LINE = 'D7DEEC', MUTED = '5A6478', BODY = '1F2430', WHITE = 'FFFFFF';
const TF = 'Cambria', BF = 'Calibri', MF = 'Courier New';

let n = 0;
function shadow() { return { type: 'outer', color: '8894B0', blur: 8, offset: 2, angle: 90, opacity: 0.22 }; }

function footer(slide, dark) {
  n += 1;
  slide.addText(String(n), {
    x: W - 1.0, y: H - 0.55, w: 0.5, h: 0.3, isTextBox: true, margin: 0,
    fontSize: 10, fontFace: BF, color: dark ? '8E97B5' : MUTED, align: 'right',
  });
  slide.addText('pyspeller', {
    x: 0.6, y: H - 0.55, w: 3, h: 0.3, isTextBox: true, margin: 0,
    fontSize: 10, fontFace: BF, color: dark ? '8E97B5' : MUTED,
  });
}

function content(title, kicker) {
  const slide = pres.addSlide();
  slide.background = { color: WHITE };
  if (kicker) {
    slide.addText(kicker.toUpperCase(), {
      x: 0.6, y: 0.36, w: 11, h: 0.28, isTextBox: true, margin: 0,
      fontSize: 11, bold: true, charSpacing: 2, fontFace: BF, color: ACCENT,
    });
  }
  slide.addText(title, {
    x: 0.6, y: 0.64, w: 12.1, h: 0.75, isTextBox: true, margin: 0,
    fontSize: 32, bold: true, fontFace: TF, color: DARK,
  });
  footer(slide, false);
  return slide;
}

function card(slide, x, y, w, h, fill) {
  slide.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.08, fill: { color: fill || TINT },
    line: { color: LINE, width: 0.75 }, shadow: shadow(),
  });
}

function step(slide, num, x, y, w, head, text, colour) {
  const c = colour || ACCENT;
  slide.addShape(pres.ShapeType.ellipse, {
    x, y, w: 0.42, h: 0.42, fill: { color: c }, line: { color: c, width: 0 },
  });
  slide.addText(String(num), {
    x, y: y + 0.03, w: 0.42, h: 0.36, isTextBox: true, margin: 0,
    fontSize: 14, bold: true, fontFace: BF, color: WHITE, align: 'center',
  });
  slide.addText(head, {
    x: x + 0.58, y: y - 0.02, w: w - 0.58, h: 0.32, isTextBox: true, margin: 0,
    fontSize: 16, bold: true, fontFace: BF, color: DARK,
  });
  if (text) {
    slide.addText(text, {
      x: x + 0.58, y: y + 0.3, w: w - 0.58, h: 0.72, isTextBox: true, margin: 0,
      fontSize: 13.5, fontFace: BF, color: MUTED, lineSpacingMultiple: 1.05,
    });
  }
}

function mono(slide, x, y, w, h, lines, size) {
  slide.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.06, fill: { color: '10162E' },
    line: { color: '10162E', width: 0 }, shadow: shadow(),
  });
  slide.addText(lines.map((l, i) => ({
    text: l.text !== undefined ? l.text : l,
    options: {
      breakLine: i < lines.length - 1,
      color: l.color || 'D6DEF5', bold: !!l.bold,
    },
  })), {
    x: x + 0.22, y: y + 0.16, w: w - 0.44, h: h - 0.32, isTextBox: true, margin: 0,
    fontSize: size || 12.5, fontFace: MF, lineSpacingMultiple: 1.18, valign: 'top',
  });
}

function bullets(slide, x, y, w, h, items, size) {
  slide.addText(items.map((t, i) => ({
    text: t, options: { bullet: { indent: 16 }, breakLine: i < items.length - 1, paraSpaceAfter: 8 },
  })), {
    x, y, w, h, isTextBox: true, margin: 0,
    fontSize: size || 15, fontFace: BF, color: BODY, lineSpacingMultiple: 1.05,
  });
}

function caption(slide, x, y, w, text) {
  slide.addText(text, {
    x, y, w, h: 0.4, isTextBox: true, margin: 0,
    fontSize: 11, italic: true, fontFace: BF, color: MUTED,
  });
}

function stat(slide, x, y, w, value, label, colour) {
  slide.addText(value, {
    x, y, w, h: 0.75, isTextBox: true, margin: 0,
    fontSize: 40, bold: true, fontFace: TF, color: colour || PRIMARY, align: 'center',
  });
  slide.addText(label, {
    x, y: y + 0.72, w, h: 0.5, isTextBox: true, margin: 0,
    fontSize: 12, fontFace: BF, color: MUTED, align: 'center',
  });
}

/* ------------------------------------------------------------------ 1 */
{
  const s = pres.addSlide();
  s.background = { color: DARK };
  s.addText('LECTURE', {
    x: 0.8, y: 1.5, w: 7, h: 0.3, isTextBox: true, margin: 0,
    fontSize: 12, bold: true, charSpacing: 2.5, fontFace: BF, color: ACCENT,
  });
  s.addText('pyspeller', {
    x: 0.8, y: 1.95, w: 7, h: 1.1, isTextBox: true, margin: 0,
    fontSize: 54, bold: true, fontFace: TF, color: WHITE,
  });
  s.addText('A P300 speller system: software architecture and signal processing', {
    x: 0.8, y: 3.1, w: 6.2, h: 1.2, isTextBox: true, margin: 0,
    fontSize: 17, fontFace: BF, color: 'C3CBE4', lineSpacingMultiple: 1.15,
  });
  s.addShape(pres.ShapeType.line, { x: 0.8, y: 4.45, w: 1.6, h: 0, line: { color: ACCENT, width: 2 } });
  s.addText('Implementation: 4,550 lines of Python, 145 tests, numpy only', {
    x: 0.8, y: 4.7, w: 6.2, h: 0.4, isTextBox: true, margin: 0,
    fontSize: 13, fontFace: BF, color: '8E97B5',
  });
  s.addText([
    { text: 'github.com/berdakh/pyspeller', options: { breakLine: true } },
    { text: 'berdakh.github.io/pyspeller', options: {} },
  ], {
    x: 0.8, y: 5.2, w: 6.2, h: 0.8, isTextBox: true, margin: 0,
    fontSize: 13, bold: true, fontFace: MF, color: ACCENT, lineSpacingMultiple: 1.2,
  });
  s.addImage({ path: IMG + 'panel-and-speller.png', x: 7.45, y: 1.85, w: 5.1, h: 2.79 });
  footer(s, true);
  s.addNotes(
    'TIMING: 2 minutes.\n\n'
    + 'Open by framing the goal of the lecture: today is not about neuroscience, it is about how a working BCI is put '
    + 'together as a piece of software. By the end they should be able to open this repository and know what every '
    + 'directory is for.\n\n'
    + 'Say plainly: this is a complete system — data acquisition, stimulus presentation, machine learning, a GUI, '
    + 'saving to disk — in about four and a half thousand lines of Python that they can read in an afternoon. '
    + 'It contains no deep learning, which is a point worth returning to when the classifier is discussed.\n\n'
    + 'On the right is what the user sees: the control panel and the speller grid. Tell them we will end with a live '
    + 'demo of exactly this.');
}

/* ------------------------------------------------------------------ 2 */
{
  const s = content('Background', 'introduction');
  card(s, 0.6, 1.6, 6.0, 4.55);
  step(s, 1, 0.95, 1.95, 5.3, 'A rare event you are attending to',
    'produces a positive deflection in the EEG about 300 ms later, called the P300.');
  step(s, 2, 0.95, 3.15, 5.3, 'The grid flashes rows and columns',
    'Two of the twelve flashes contain the attended letter; the other ten do not.');
  step(s, 3, 0.95, 4.45, 5.3, 'The letter is the intersection',
    'The row and the column with the largest response identify one symbol.');
  s.addImage({ path: IMG + 'erp.png', x: 7.0, y: 1.75, w: 5.7, h: 2.28 });
  caption(s, 7.0, 4.1, 5.7, 'Target flashes (blue) against non-target flashes (grey), averaged over a session.');
  card(s, 7.0, 4.62, 5.7, 1.5, 'FCF3E3');
  s.addText('Note', {
    x: 7.3, y: 4.78, w: 5.1, h: 0.3, isTextBox: true, margin: 0,
    fontSize: 14, bold: true, fontFace: BF, color: AMBER,
  });
  s.addText('A single flash gives a very unreliable measurement. The rest of the system is concerned with making the decision reliable.', {
    x: 7.3, y: 5.12, w: 5.1, h: 0.9, isTextBox: true, margin: 0,
    fontSize: 13.5, fontFace: BF, color: BODY, lineSpacingMultiple: 1.05,
  });
  s.addNotes(
    'TIMING: 3 minutes. This is the whole of the neuroscience — resist questions that pull you deeper, promise to '
    + 'come back at the end.\n\n'
    + 'Walk the three steps. Emphasise that the P300 is an attention response, not a "thought reading" signal: the '
    + 'participant does nothing but count the flashes of the letter they want.\n\n'
    + 'Point at the ERP plot: the blue curve is the average of all flashes that contained the attended letter, the '
    + 'grey one is everything else. Ask the class: how big is the difference? (About 5 microvolts.) And how big is '
    + 'the background EEG? (Ten to a hundred microvolts.) So a single flash tells you almost nothing — the curve '
    + 'they are looking at is an average of several hundred.\n\n'
    + 'That is the engineering problem in one sentence, and it sets up the rest of the lecture: everything from here '
    + 'is about accumulating evidence and not corrupting it.');
}

/* ------------------------------------------------------------------ 3 */
{
  const s = content('Outline', 'introduction');
  const items = [
    ['1', 'System architecture', 'Design requirements, the buffer, the protocol, timing'],
    ['2', 'System components', 'Acquisition, stimulus presentation, phase control'],
    ['3', 'Signal processing', 'Epochs, preprocessing, classification, decoding'],
    ['4', 'Implementation notes', 'Data storage, user interface, testing'],
    ['5', 'Demonstration and extensions', 'A recorded run, and possible project work'],
  ];
  items.forEach((it, i) => {
    const y = 1.65 + i * 1.02;
    card(s, 0.6, y, 8.4, 0.88, i === 4 ? 'E7F6F1' : TINT);
    s.addShape(pres.ShapeType.ellipse, { x: 0.85, y: y + 0.21, w: 0.46, h: 0.46, fill: { color: i === 4 ? ACCENT : PRIMARY } });
    s.addText(it[0], { x: 0.85, y: y + 0.25, w: 0.46, h: 0.38, isTextBox: true, margin: 0, fontSize: 15, bold: true, fontFace: BF, color: WHITE, align: 'center' });
    s.addText(it[1], { x: 1.5, y: y + 0.13, w: 6.9, h: 0.32, isTextBox: true, margin: 0, fontSize: 17, bold: true, fontFace: BF, color: DARK });
    s.addText(it[2], { x: 1.5, y: y + 0.47, w: 6.9, h: 0.32, isTextBox: true, margin: 0, fontSize: 13, fontFace: BF, color: MUTED });
  });
  card(s, 9.35, 1.65, 3.35, 4.24, DARK);
  s.addText('Learning objectives', {
    x: 9.6, y: 1.9, w: 2.85, h: 0.6, isTextBox: true, margin: 0,
    fontSize: 15, bold: true, fontFace: BF, color: ACCENT,
  });
  s.addText([
    { text: 'After this lecture you should be able to:', options: { breakLine: true, color: 'B9C2DC' } },
    { text: ' ', options: { breakLine: true } },
    { text: '1. describe the client–server structure;', options: { breakLine: true } },
    { text: '2. explain how events and EEG samples are aligned in time;', options: { breakLine: true } },
    { text: '3. follow the path from samples to a letter;', options: { breakLine: true } },
    { text: '4. modify and test part of the system.', options: {} },
  ], {
    x: 9.6, y: 2.4, w: 2.85, h: 3.3, isTextBox: true, margin: 0,
    fontSize: 12.5, fontFace: BF, color: WHITE, lineSpacingMultiple: 1.14,
  });
  s.addNotes(
    'TIMING: 1 minute.\n\n'
    + 'Give them the shape of the hour so they know when to ask questions — architecture first, then the two halves '
    + 'of the loop, then practice, then the demo.\n\n'
    + 'The two questions on the right are the thread. Tell them you will ask both again at the end, and that if they '
    + 'can answer them they have understood the system. Write them on the board if you have one — they are worth '
    + 'keeping visible for the whole lecture.\n\n'
    + 'Housekeeping: tell them the full tutorial site covers everything on these slides in more depth, so they do not '
    + 'need to transcribe code.\n\n'
    + 'IF YOU RUN LATE: the slides to compress, in order, are 21 (the GUI), 6 (what the buffer buys you), 20 (what '
    + 'lands on disk) and 9 (the repository map). Never cut slide 8 (sample-indexed time), slide 14 (preprocessing) '
    + 'or slide 17 (evidence accumulation) — they carry the lecture.');
}

/* ------------------------------------------------------------------ 4 */
{
  const s = content('Design requirements', 'system architecture');
  const boxes = [
    ['Accurate timing', 'A 5 µV response 300 ms after a flash can only be measured if the time of the flash is known to within a few milliseconds.', PRIMARY],
    ['Concurrent tasks', 'Stimulus presentation, data acquisition, classification and the user interface must run without blocking each other.', PRIMARY],
    ['Hardware independence', 'The same experiment must run with a g.tec amplifier, another device, a recording or a simulator.', ACCENT],
    ['Offline reproducibility', 'A recorded session must be re-analysable later, without the participant and without the hardware.', ACCENT],
  ];
  boxes.forEach((b, i) => {
    const x = 0.6 + (i % 2) * 6.35, y = 1.62 + Math.floor(i / 2) * 2.35;
    card(s, x, y, 6.0, 2.05);
    s.addShape(pres.ShapeType.ellipse, { x: x + 0.35, y: y + 0.35, w: 0.44, h: 0.44, fill: { color: b[2] } });
    s.addText(String(i + 1), { x: x + 0.35, y: y + 0.39, w: 0.44, h: 0.36, isTextBox: true, margin: 0, fontSize: 14, bold: true, fontFace: BF, color: WHITE, align: 'center' });
    s.addText(b[0], { x: x + 0.95, y: y + 0.33, w: 4.8, h: 0.4, isTextBox: true, margin: 0, fontSize: 18, bold: true, fontFace: BF, color: DARK });
    s.addText(b[1], { x: x + 0.95, y: y + 0.82, w: 4.75, h: 1.0, isTextBox: true, margin: 0, fontSize: 13.5, fontFace: BF, color: MUTED, lineSpacingMultiple: 1.08 });
  });
  s.addText('One program can satisfy two or three of these; the architecture that follows satisfies all four.', {
    x: 0.6, y: 6.45, w: 12.1, h: 0.4, isTextBox: true, margin: 0,
    fontSize: 15, italic: true, fontFace: BF, color: PRIMARY, align: 'center',
  });
  s.addNotes(
    'TIMING: 3 minutes.\n\n'
    + 'This slide is the justification for everything that follows, so do not rush it. Ask the class first: if you had '
    + 'to write this yourself, what would you write? Most will say one big loop — read EEG, flash, classify. Let that '
    + 'answer stand, then break it with these four constraints.\n\n'
    + 'Constraint 1: the whole method depends on knowing flash times precisely. A 20 ms error is 20 ms of smear on a '
    + 'response that is only a couple of hundred milliseconds wide.\n\n'
    + 'Constraint 2: in one loop, a slow classifier delays the next flash — the experiment distorts itself.\n\n'
    + 'Constraint 3: student labs change hardware constantly. The experiment code must not.\n\n'
    + 'Constraint 4: if the only place the data ever existed was in memory, a crash costs you a participant — and with '
    + 'a human subject you cannot just re-run it.\n\n'
    + 'Land the closing line: the architecture is not over-engineering, it is the cheapest way to satisfy all four.');
}

/* ------------------------------------------------------------------ 5 */
{
  const s = content('Architecture: buffer and clients', 'system architecture');
  s.addImage({ path: GEN + 'architecture.png', x: 0.75, y: 1.5, w: 8.2, h: 3.92 });
  caption(s, 0.75, 5.5, 8.2, 'The FieldTrip buffer: a TCP server holding a ring of recent samples and a list of events. All other programs are clients of it.');
  card(s, 9.35, 1.5, 3.35, 4.6);
  s.addText('Design rules', {
    x: 9.6, y: 1.72, w: 2.85, h: 0.35, isTextBox: true, margin: 0,
    fontSize: 16, bold: true, fontFace: BF, color: PRIMARY,
  });
  bullets(s, 9.6, 2.15, 2.9, 3.7, [
    'Samples are appended, never modified',
    'Events are timestamped by sample index',
    'Any client may read any range at any time',
    'Clients communicate only through the buffer',
  ], 13.5);
  s.addNotes(
    'TIMING: 4 minutes.\n\n'
    + 'Walk the diagram left to right: an acquisition client pushes samples; the stimulus client pushes events saying '
    + 'what was flashed and when; the signal-processing client reads both and pushes its prediction back as another '
    + 'event; the GUI watches and sends commands. The buffer itself is dumb — it stores and serves, it does not know '
    + 'what a P300 is.\n\n'
    + 'Stress the last bullet: no client has a reference to any other. You can kill the signal processor mid-session, '
    + 'restart it, and it picks up from the buffer. Students find this hard to believe until they see the demo.\n\n'
    + 'Mention the lineage: this is the FieldTrip buffer, the same design as the MATLAB buffer_bci framework this '
    + 'project reimplements. That is deliberate — the protocol is a published standard, so a MATLAB client and a '
    + 'Python client can share one buffer.\n\n'
    + 'ASK: which of the four constraints does this satisfy, and which does it not yet? (It gives independence and '
    + 'replaceability; timing is next.)');
}

/* ------------------------------------------------------------------ 6 */
{
  const s = content('Advantages and costs of this design', 'system architecture');
  const wins = [
    ['Interchangeable data sources', 'Simulator, LSL device or recorded file: the experiment code is unchanged.'],
    ['Language independence', 'The MATLAB buffer_bci client and this Python one speak the same protocol.'],
    ['Record and replay', 'Every sample and event is already in one place, in order.'],
    ['Fault isolation', 'If the classifier fails, stimulus presentation continues; the client can be restarted.'],
    ['Several readers, one stream', 'The interface, the analysis and the recorder read the same data concurrently.'],
  ];
  wins.forEach((w, i) => {
    const y = 1.62 + i * 0.98;
    step(s, i + 1, 0.7, y, 7.4, w[0], w[1], i % 2 ? PRIMARY : ACCENT);
  });
  card(s, 8.55, 1.62, 4.15, 4.35, DARK);
  s.addText('Costs', {
    x: 8.85, y: 1.85, w: 3.5, h: 0.35, isTextBox: true, margin: 0,
    fontSize: 16, bold: true, fontFace: BF, color: AMBER,
  });
  s.addText([
    { text: 'Four processes must be started instead of one.', options: { breakLine: true } },
    { text: 'The data exist in a second copy in memory.', options: { breakLine: true } },
    { text: 'The protocol has to be implemented and maintained.', options: { breakLine: true } },
    { text: ' ', options: { breakLine: true } },
    { text: 'These costs are usually accepted when the hardware changes, when clients may fail, or when sessions must be recoverable.', options: { color: ACCENT } },
  ], {
    x: 8.85, y: 2.3, w: 3.55, h: 3.4, isTextBox: true, margin: 0,
    fontSize: 13.5, fontFace: BF, color: 'C3CBE4', lineSpacingMultiple: 1.15,
  });
  s.addNotes(
    'TIMING: 2 minutes.\n\n'
    + 'Go quickly through the five wins — they are mostly self-evident once the diagram has landed. Spend your time '
    + 'on two of them:\n\n'
    + '"Swap the data source" is what lets the whole class develop without an amplifier: the simulator produces a '
    + 'realistic ERP and the system cannot tell the difference. That is how the test suite runs in CI.\n\n'
    + '"Crash isolation" is worth demonstrating live later — kill the sigproc process during the demo and restart it.\n\n'
    + 'Be honest about the price. Good engineering teaching means naming the cost, not pretending it is free. Ask the '
    + 'class when they would NOT do this: a single-purpose script for one recording session, run once, is fine as a '
    + 'monolith.');
}

/* ------------------------------------------------------------------ 7 */
{
  const s = content('The buffer protocol', 'system architecture');
  mono(s, 0.6, 1.55, 6.1, 2.35, [
    { text: 'request:  [version | command | size] + payload', color: ACCENT },
    { text: '           uint16    uint16    uint32', color: '8E97B5' },
    '',
    { text: 'PUT_HDR  0x101   declare channels + rate' },
    { text: 'PUT_DAT  0x102   append samples' },
    { text: 'PUT_EVT  0x103   append an event' },
    { text: 'GET_DAT  0x202   read a sample range' },
    { text: 'WAIT_DAT 0x402   block until new data arrives' },
  ], 12.5);
  card(s, 0.6, 4.1, 6.1, 2.05);
  s.addText('Summary', {
    x: 0.9, y: 4.28, w: 5.5, h: 0.32, isTextBox: true, margin: 0,
    fontSize: 15, bold: true, fontFace: BF, color: PRIMARY,
  });
  s.addText('An eight-byte header, a payload and a reply. In this implementation the client is about 300 lines and the server about 250.', {
    x: 0.9, y: 4.66, w: 5.5, h: 1.2, isTextBox: true, margin: 0,
    fontSize: 13.5, fontFace: BF, color: BODY, lineSpacingMultiple: 1.1,
  });
  card(s, 7.05, 1.55, 5.65, 4.6);
  s.addText('Blocking reads: WAIT_DAT', {
    x: 7.35, y: 1.78, w: 5.0, h: 0.35, isTextBox: true, margin: 0,
    fontSize: 16, bold: true, fontFace: BF, color: DARK,
  });
  bullets(s, 7.35, 2.25, 5.0, 3.6, [
    'A client requests: return when sample 4 096 exists, or after 500 ms, whichever occurs first.',
    'This avoids polling loops and fixed sleep intervals.',
    'It is how the signal processor stays synchronised with an amplifier it never addresses directly.',
    'The stimulus client uses the same call to wait for a prediction.',
  ], 14);
  s.addNotes(
    'TIMING: 2 minutes.\n\n'
    + 'The point of this slide is to remove the mystique. Networking protocols sound intimidating; this one is a '
    + 'two-field header and a length. Show them the numbers: 0x101 to put a header, 0x202 to get data.\n\n'
    + 'Endianness is worth a sentence: the server detects the client\'s byte order from the version field, which is '
    + 'how a MATLAB client on one machine and a Python client on another interoperate.\n\n'
    + 'Spend the time on WAIT_DAT. Ask: how would you write the signal processor without it? Most answers involve a '
    + 'sleep-and-poll loop; walk them through why that is either wasteful (polling every millisecond) or laggy '
    + '(polling every 100 ms). WAIT_DAT gives you an event-driven client over a plain TCP socket.\n\n'
    + 'If they ask about latency: on localhost this is tens of microseconds, far below anything that matters here.');
}

/* ------------------------------------------------------------------ 8 */
{
  const s = content('Timing: events carry sample indices', 'system architecture');
  s.addImage({ path: GEN + 'sampling.png', x: 0.7, y: 1.5, w: 7.6, h: 2.61 });
  card(s, 0.7, 4.3, 7.6, 1.85, 'E7F6F1');
  s.addText('An event is timestamped with the number of samples already stored when it arrived, not with a clock reading.', {
    x: 1.0, y: 4.5, w: 7.0, h: 0.6, isTextBox: true, margin: 0,
    fontSize: 15, bold: true, fontFace: BF, color: DARK, lineSpacingMultiple: 1.05,
  });
  s.addText('Extracting the epoch after a flash is therefore array indexing, samples n to n+77, and not a calculation involving clocks.', {
    x: 1.0, y: 5.2, w: 7.0, h: 0.8, isTextBox: true, margin: 0,
    fontSize: 14, fontFace: BF, color: BODY, lineSpacingMultiple: 1.05,
  });
  mono(s, 8.65, 1.5, 4.05, 4.65, [
    { text: '# 128 Hz, 600 ms epochs', color: '8E97B5' },
    { text: 'fsample    = 128' },
    { text: 'trlen_ms   = 600' },
    { text: 'trlen      = 77 samples', color: ACCENT },
    '',
    { text: 'event: stimulus.rowFlash', color: '8E97B5' },
    { text: '  value  = 3' },
    { text: '  sample = 4096', color: ACCENT },
    '',
    { text: 'epoch = data[4096:4173]' },
    { text: '        shape (8, 77)', color: ACCENT },
    '',
    { text: '# no clocks were consulted', color: '8E97B5' },
  ], 12.5);
  s.addNotes(
    'TIMING: 4 minutes. This is the central technical idea of the lecture; allow time for it.\n\n'
    + 'Start with the naive approach: record the wall-clock time of each flash, record the wall-clock time the EEG '
    + 'arrived, subtract. Ask what can go wrong. Answers you are looking for: the amplifier buffers samples and '
    + 'delivers them in blocks, the operating system delays your process, two machines have two clocks, USB latency '
    + 'varies.\n\n'
    + 'Then give them the trick: when an event arrives at the buffer, the buffer knows exactly how many samples it '
    + 'has already stored. It stamps the event with that number. Both the flash and the EEG are now expressed in the '
    + 'same unit — samples — and that unit came from the amplifier\'s own crystal, not from any computer clock.\n\n'
    + 'Work the arithmetic on the board with them: 600 ms at 128 Hz is 76.8, rounded to 77 samples. An 8-channel '
    + 'epoch is an 8 by 77 array. Every epoch in the entire system is exactly this shape.\n\n'
    + 'This is also why the code puts the flash event into the buffer in the same request as the draw call — one '
    + 'request, one stamp. Mention that the remaining error is screen refresh, a few milliseconds, and that a photodiode '
    + 'is how you measure it if you need to.');
}

/* ------------------------------------------------------------------ 9 */
{
  const s = content('Software components', 'system components');
  const rows = [
    ['buffer/', 'protocol, server, client', 'protocol implementation', '~750'],
    ['acquisition/', 'simulator, lsl_bridge, saver', 'data sources and recording', '~700'],
    ['speller/', 'matrix, stimulus, render, sigproc', 'the experiment', '~1.1k'],
    ['signalproc/', 'preproc, epochs, classifier', 'numerical methods', '~600'],
    ['gui/', 'launcher, control_panel, training_view', 'user interface only', '~800'],
  ];
  rows.forEach((r, i) => {
    const y = 1.6 + i * 0.88;
    card(s, 0.6, y, 8.5, 0.78, i % 2 ? WHITE : TINT);
    s.addText(r[0], { x: 0.85, y: y + 0.24, w: 1.75, h: 0.32, isTextBox: true, margin: 0, fontSize: 14.5, bold: true, fontFace: MF, color: PRIMARY });
    s.addText(r[1], { x: 2.65, y: y + 0.24, w: 3.3, h: 0.32, isTextBox: true, margin: 0, fontSize: 13, fontFace: MF, color: BODY });
    s.addText(r[2], { x: 6.05, y: y + 0.24, w: 2.3, h: 0.32, isTextBox: true, margin: 0, fontSize: 12.5, italic: true, fontFace: BF, color: MUTED });
    s.addText(r[3], { x: 8.35, y: y + 0.24, w: 0.6, h: 0.32, isTextBox: true, margin: 0, fontSize: 12.5, fontFace: MF, color: MUTED, align: 'right' });
  });
  stat(s, 9.4, 1.75, 1.55, '4.5k', 'lines of Python');
  stat(s, 11.1, 1.75, 1.55, '145', 'tests', ACCENT);
  stat(s, 9.4, 3.35, 1.55, '5', 'packages');
  stat(s, 11.1, 3.35, 1.55, '3', 'dependencies', ACCENT);
  card(s, 9.4, 4.95, 3.25, 1.2, TINT);
  s.addText('numpy; tkinter for the interface and pylsl for an amplifier connection.', {
    x: 9.6, y: 5.12, w: 2.9, h: 0.9, isTextBox: true, margin: 0,
    fontSize: 12.5, fontFace: BF, color: MUTED, lineSpacingMultiple: 1.05,
  });
  s.addNotes(
    'TIMING: 2 minutes.\n\n'
    + 'This is the map they should keep. Each directory corresponds to one box in the architecture diagram, which is '
    + 'not an accident — if you cannot point at the directory that implements a box, the architecture is a lie.\n\n'
    + 'Highlight that signalproc/ is numpy only: no scipy, no sklearn, no torch. The filters, the LDA, the '
    + 'cross-validation are all written out. That is a deliberate teaching choice — they can read every line of the '
    + 'maths and change it.\n\n'
    + 'Mention the test count now and come back to it at the end: 145 tests for 4,500 lines means the ratio of test '
    + 'code to source is about 40 %, which is normal for code you intend other people to modify.\n\n'
    + 'Tell them the assignment-relevant part: they will be adding files under speller/ and signalproc/, not touching '
    + 'buffer/.');
}

/* ------------------------------------------------------------------ 10 */
{
  const s = content('Data acquisition', 'system components');
  s.addImage({ path: GEN + 'gtec-chain.png', x: 0.7, y: 1.5, w: 7.9, h: 2.98 });
  caption(s, 0.7, 4.55, 7.9, 'Signal path with a g.tec amplifier: cap, amplifier, vendor driver, LSL, bridge, buffer.');
  const opts = [
    ['Simulator', 'Generates EEG with an event-related response, mains interference, blinks and drift. Deterministic, no hardware required.', ACCENT],
    ['LSL bridge', 'Subscribes to a Lab Streaming Layer EEG stream and copies samples into the buffer. This is the path used with g.tec amplifiers.', PRIMARY],
    ['Recorded session', 'Replays a stored recording sample by sample at the original rate.', PRIMARY],
  ];
  opts.forEach((o, i) => {
    const y = 5.05 + i * 0.0;
  });
  card(s, 8.95, 1.5, 3.75, 4.65);
  s.addText('Three sources', {
    x: 9.2, y: 1.7, w: 3.2, h: 0.32, isTextBox: true, margin: 0,
    fontSize: 16, bold: true, fontFace: BF, color: DARK,
  });
  opts.forEach((o, i) => {
    const y = 2.2 + i * 1.32;
    s.addText(o[0], { x: 9.2, y, w: 3.25, h: 0.3, isTextBox: true, margin: 0, fontSize: 14, bold: true, fontFace: BF, color: o[2] });
    s.addText(o[1], { x: 9.2, y: y + 0.32, w: 3.25, h: 0.95, isTextBox: true, margin: 0, fontSize: 12.5, fontFace: BF, color: MUTED, lineSpacingMultiple: 1.05 });
  });
  s.addText('All three use the same PUT_HDR and PUT_DAT calls, so the remaining components are independent of the data source.', {
    x: 0.7, y: 5.25, w: 7.9, h: 0.9, isTextBox: true, margin: 0,
    fontSize: 15, italic: true, fontFace: BF, color: PRIMARY, lineSpacingMultiple: 1.05,
  });
  s.addNotes(
    'TIMING: 3 minutes.\n\n'
    + 'Walk the g.tec chain box by box, because this is what they will actually plug in: the cap goes into the '
    + 'amplifier, the vendor driver (g.NEEDaccess) talks to the device, the vendor LSL connector publishes a stream '
    + 'on the network, and our bridge subscribes to it and copies samples into the buffer.\n\n'
    + 'Explain why we do not talk to the amplifier directly: every vendor has a different SDK, and LSL is the common '
    + 'denominator that most research amplifiers already speak. One bridge, any amplifier.\n\n'
    + 'The simulator deserves a real moment. It is not a random-noise generator: it produces a P300 of a chosen '
    + 'amplitude at a chosen latency on target flashes, plus common-mode noise, blinks and drift. That means you can '
    + 'develop the entire analysis pipeline, and run the test suite in CI, with no hardware and no participant.\n\n'
    + 'ASK: what would you have to change in the speller code to move from the simulator to a g.tec amplifier? '
    + '(Answer: one command-line flag. Nothing inside the experiment.)');
}

/* ------------------------------------------------------------------ 11 */
{
  const s = content('Stimulus presentation', 'system components');
  s.addImage({ path: GEN + 'matrix-decode.png', x: 0.65, y: 1.5, w: 7.4, h: 3.54 });
  caption(s, 0.65, 5.12, 7.4, 'Twelve groups cover thirty-six symbols: each symbol is the intersection of one row and one column.');
  const nums = [
    ['12', 'groups (6 rows + 6 cols)'],
    ['12', 'repetitions per letter'],
    ['144', 'flashes per letter'],
    ['150 ms', 'between flash onsets'],
    ['100 ms', 'a group stays lit'],
    ['≈ 22 s', 'to spell one letter'],
  ];
  nums.forEach((v, i) => {
    const x = 8.45 + (i % 2) * 2.2, y = 1.55 + Math.floor(i / 2) * 1.35;
    card(s, x, y, 2.05, 1.18, TINT);
    s.addText(v[0], { x: x + 0.1, y: y + 0.13, w: 1.85, h: 0.45, isTextBox: true, margin: 0, fontSize: 22, bold: true, fontFace: TF, color: PRIMARY, align: 'center' });
    s.addText(v[1], { x: x + 0.1, y: y + 0.6, w: 1.85, h: 0.5, isTextBox: true, margin: 0, fontSize: 11, fontFace: BF, color: MUTED, align: 'center' });
  });
  card(s, 8.45, 5.55, 4.25, 0.85, 'FCF3E3');
  s.addText('Note: the order is randomised, with at least three flashes between repetitions of one group.', {
    x: 8.65, y: 5.7, w: 3.85, h: 0.6, isTextBox: true, margin: 0,
    fontSize: 12, fontFace: BF, color: BODY, lineSpacingMultiple: 1.04,
  });
  s.addNotes(
    'TIMING: 4 minutes.\n\n'
    + 'First the combinatorics: 36 symbols would need 36 flashes each if you flashed them one at a time. Rows and '
    + 'columns need only 12, because each symbol is a unique intersection. Ask the class what the cost is — the '
    + 'answer is that you now need two decisions instead of one, and both must be right.\n\n'
    + 'Then the timing numbers. 12 repetitions of 12 groups is 144 flashes at 150 ms, which is about 22 seconds per '
    + 'letter. Say that out loud and let it land: this is slow. Real users tolerate it because the alternative may '
    + 'be no communication at all — and later we will see how to make it faster.\n\n'
    + 'The minimum gap matters more than it looks. If the same row flashes twice in a row, the second P300 lands on '
    + 'top of the first one and neither is clean. The same logic explains why you avoid flashing a row immediately '
    + 'after the column that crosses it — that is the "adjacency problem" in the literature.\n\n'
    + 'Point out that all these numbers live in one dataclass, config.py, so the whole experiment is re-tunable '
    + 'without touching the logic.');
}

/* ------------------------------------------------------------------ 12 */
{
  const s = content('Experiment phases and control events', 'system components');
  s.addImage({ path: GEN + 'session-timeline.png', x: 0.65, y: 1.45, w: 7.5, h: 3.33 });
  caption(s, 0.65, 4.85, 7.5, 'A session is a sequence of phases, each announced as an event.');
  mono(s, 8.5, 1.45, 4.2, 4.6, [
    { text: 'startPhase.cmd', color: ACCENT },
    { text: '  calibrate | train | feedback' },
    '',
    { text: 'speller.ready', color: ACCENT },
    { text: '  "I have the command"' },
    '',
    { text: 'stimulus.rowFlash 3', color: ACCENT },
    { text: 'stimulus.colFlash 5' },
    { text: 'stimulus.tgtFlash 1', color: ACCENT },
    { text: '  the training label' },
    '',
    { text: 'classifier.prediction R', color: ACCENT },
    { text: 'speller.control  pause', color: ACCENT },
  ], 12);
  s.addText('The clients share no memory and call no functions in each other. The list above is the complete interface between them.', {
    x: 0.65, y: 5.45, w: 7.5, h: 0.75, isTextBox: true, margin: 0,
    fontSize: 14.5, italic: true, fontFace: BF, color: PRIMARY, lineSpacingMultiple: 1.05,
  });
  s.addNotes(
    'TIMING: 3 minutes.\n\n'
    + 'Two things to teach here. First the session structure: calibrate with known letters, train a classifier on '
    + 'that data, then run feedback or free spelling. Same as any supervised learning workflow — label, fit, predict '
    + '— but with a human in the loop.\n\n'
    + 'Second, and more interesting: how do four independent processes agree on what is happening? They do not call '
    + 'each other. The GUI writes startPhase.cmd into the buffer; the stimulus and signal-processing clients are both '
    + 'watching for it and react. That is a publish–subscribe system built out of a shared log.\n\n'
    + 'The speller.ready event is worth explaining because it is a real bug fix, not a design flourish: without it, '
    + 'the GUI could send a phase command and the stimulus client could still be finishing the previous block, and '
    + 'tests raced. The handshake makes the transition observable.\n\n'
    + 'Note stimulus.tgtFlash: during calibration only, the stimulus client also writes down whether the flash '
    + 'contained the cued letter. That is the training label, produced by the process that knows the ground truth.\n\n'
    + 'ASK: what happens if the signal processor is not running when a phase starts? (Nothing breaks; the events sit '
    + 'in the buffer, and a client that starts later can read them.)');
}

/* ------------------------------------------------------------------ 13 */
{
  const s = content('Epoch extraction', 'signal processing');
  const steps = [
    ['Wait for a flash event', 'Block until the event exists, using WAIT_DAT.'],
    ['Wait 600 ms more', 'The epoch is not complete until the samples after the flash have arrived.'],
    ['Slice', 'data[n : n+77] → an 8 × 77 array.'],
    ['Attach the label', 'stimulus.tgtFlash gives 1 for a target flash and 0 otherwise.'],
  ];
  steps.forEach((st, i) => {
    step(s, i + 1, 0.65, 1.6 + i * 1.12, 6.4, st[0], st[1]);
  });
  card(s, 7.35, 1.6, 5.35, 2.5, DARK);
  s.addText('One calibration word, five letters', {
    x: 7.65, y: 1.82, w: 4.7, h: 0.32, isTextBox: true, margin: 0,
    fontSize: 15, bold: true, fontFace: BF, color: ACCENT,
  });
  s.addText([
    { text: '5 letters x 144 flashes = 720 epochs', options: { breakLine: true } },
    { text: '120 targets  ·  600 non-targets', options: { breakLine: true } },
    { text: 'imbalance 1 : 5 - by construction', options: { breakLine: true, color: AMBER } },
    { text: ' ', options: { breakLine: true } },
    { text: 'Every epoch: 8 channels × 77 samples', options: { color: ACCENT } },
  ], {
    x: 7.65, y: 2.3, w: 4.7, h: 1.6, isTextBox: true, margin: 0,
    fontSize: 14, fontFace: MF, color: 'D6DEF5', lineSpacingMultiple: 1.15,
  });
  card(s, 7.35, 4.35, 5.35, 1.8, 'FCF3E3');
  s.addText('Class imbalance', {
    x: 7.65, y: 4.52, w: 4.7, h: 0.3, isTextBox: true, margin: 0,
    fontSize: 14, bold: true, fontFace: BF, color: AMBER,
  });
  s.addText('A classifier that always predicts "non-target" is correct 83 % of the time and cannot spell. Performance is therefore reported as AUC rather than accuracy.', {
    x: 7.65, y: 4.88, w: 4.7, h: 1.1, isTextBox: true, margin: 0,
    fontSize: 13.5, fontFace: BF, color: BODY, lineSpacingMultiple: 1.05,
  });
  s.addNotes(
    'TIMING: 3 minutes.\n\n'
    + 'State the transition explicitly: from this point the problem is ordinary supervised learning on a labelled '
    + 'dataset, and nothing further is specific to EEG.\n\n'
    + 'Step 2 is the one people get wrong when they write this themselves: the event arrives immediately, but the '
    + 'data you need comes 600 ms later. The gatherer has to wait for samples, not for the event.\n\n'
    + 'Do the arithmetic with them: five letters, 144 flashes each, 720 epochs, of which one in six is a target — two '
    + 'of the twelve groups contain the attended letter.\n\n'
    + 'Then hammer the imbalance point. Ask: what accuracy does a lazy classifier get? They will compute 83 %. Ask '
    + 'whether it can spell anything. It cannot. This motivates AUC, which comes back in a few slides.\n\n'
    + 'If a student asks about more calibration data: yes, more letters is better, and the trade-off is a participant '
    + 'sitting still for longer — typically 5 to 10 letters.');
}

/* ------------------------------------------------------------------ 14 */
{
  const s = content('Preprocessing', 'signal processing');
  const chain = [
    ['Detrend', 'Fit and subtract a straight line from each epoch, removing slow drift.'],
    ['Common average reference', 'Subtract the mean over channels, removing components common to all electrodes: interference, distant muscle activity, reference drift.'],
    ['Band-pass 0.5–10 Hz', 'Trapezoidal filter applied in the frequency domain, giving zero phase distortion of the response.'],
    ['Downsample 128 → 16 Hz', 'The response contains no detail above 10 Hz; 77 samples per epoch become 10.'],
    ['Reject outliers', 'Remove channels and epochs whose power differs strongly from the rest: blinks, electrode pops, poor contact.'],
  ];
  chain.forEach((c, i) => {
    const y = 1.55 + i * 0.94;
    step(s, i + 1, 0.65, y, 8.1, c[0], c[1], i === 4 ? AMBER : PRIMARY);
  });
  card(s, 9.1, 1.55, 3.6, 3.3, DARK);
  s.addText('Shape bookkeeping', {
    x: 9.35, y: 1.75, w: 3.1, h: 0.3, isTextBox: true, margin: 0,
    fontSize: 15, bold: true, fontFace: BF, color: ACCENT,
  });
  s.addText([
    { text: 'in        (8, 77)', options: { breakLine: true } },
    { text: 'filter    (8, 77)', options: { breakLine: true } },
    { text: 'resample  (8, 10)', options: { breakLine: true } },
    { text: 'flatten   80', options: { breakLine: true, color: ACCENT } },
    { text: ' ', options: { breakLine: true } },
    { text: '80 features', options: { color: ACCENT, bold: true, breakLine: true } },
    { text: '720 examples', options: { color: ACCENT, bold: true } },
  ], {
    x: 9.35, y: 2.2, w: 3.1, h: 2.4, isTextBox: true, margin: 0,
    fontSize: 13.5, fontFace: MF, color: 'D6DEF5', lineSpacingMultiple: 1.2,
  });
  card(s, 9.1, 5.05, 3.6, 1.1, 'E7F6F1');
  s.addText('Nine training examples per feature. This ratio is the reason for using a regularised linear model.', {
    x: 9.35, y: 5.22, w: 3.1, h: 0.8, isTextBox: true, margin: 0,
    fontSize: 12.5, fontFace: BF, color: BODY, lineSpacingMultiple: 1.05,
  });
  s.addNotes(
    'TIMING: 5 minutes. This is the densest slide; budget for it.\n\n'
    + 'Take each step and ask "what noise does this remove, and what would happen without it?"\n\n'
    + 'Detrend: without it a slowly drifting baseline looks like a big slow ERP difference.\n\n'
    + 'CAR: the key insight is that brain activity is local and noise is usually global, so subtracting what every '
    + 'channel shares is nearly free. Warn them it is only valid with enough electrodes spread around the head.\n\n'
    + 'Band-pass: emphasise the zero-phase property. A causal filter delays different frequencies by different '
    + 'amounts, which literally changes the shape of the ERP you are trying to classify. Doing it in the frequency '
    + 'domain offline avoids that entirely.\n\n'
    + 'Downsampling: this is the step that makes the machine learning tractable. Ask them why we can throw away 87 % '
    + 'of the samples — because after a 10 Hz low-pass there is nothing left up there to lose.\n\n'
    + 'The shape column on the right is worth copying onto the board. End on the ratio: 80 features, 720 examples. '
    + 'With nine examples per feature, a linear classifier with regularisation is not a compromise, it is the correct '
    + 'choice.');
}

/* ------------------------------------------------------------------ 15 */
{
  const s = content('Classification: linear discriminant analysis', 'signal processing');
  mono(s, 0.6, 1.5, 6.3, 2.2, [
    { text: 'mu1, mu0 = class means', color: '8E97B5' },
    { text: 'S        = pooled covariance' },
    { text: 'S        = (1-l)*S + l*trace(S)/d*I', color: ACCENT },
    { text: 'w        = inv(S) @ (mu1 - mu0)' },
    '',
    { text: 'score(x) = w @ x + b', color: ACCENT },
  ], 13);
  const why = [
    ['Linear model', 'With 80 features and 720 examples, and a response that is an additive voltage difference, non-linear models overfit.'],
    ['Shrinkage', 'An 80 × 80 covariance matrix estimated from 720 epochs is poorly conditioned. It is shrunk toward a diagonal matrix; here λ = 0.6.'],
    ['Implementation', 'Written directly in numpy (about forty lines) so that every step can be read and modified. Training takes milliseconds.'],
  ];
  why.forEach((w, i) => {
    const y = 3.95 + i * 0.78;
    s.addText(w[0], { x: 0.6, y, w: 1.95, h: 0.3, isTextBox: true, margin: 0, fontSize: 14, bold: true, fontFace: BF, color: PRIMARY });
    s.addText(w[1], { x: 2.6, y, w: 4.3, h: 0.72, isTextBox: true, margin: 0, fontSize: 12.5, fontFace: BF, color: MUTED, lineSpacingMultiple: 1.03 });
  });
  card(s, 7.25, 1.5, 5.45, 4.65);
  s.addText('Interpretation of the score', {
    x: 7.55, y: 1.72, w: 4.85, h: 0.32, isTextBox: true, margin: 0,
    fontSize: 16, bold: true, fontFace: BF, color: DARK,
  });
  bullets(s, 7.55, 2.2, 4.85, 3.7, [
    'One value per flash, expressing how target-like that epoch is.',
    'It is not a probability; only the relative ordering of the values is used.',
    'A single value is only slightly better than chance, as expected.',
    'A decision uses 24 values: 12 repetitions of the two groups containing the symbol.',
  ], 14);
  s.addNotes(
    'TIMING: 4 minutes.\n\n'
    + 'Walk the four lines of maths. Class means, pooled covariance, shrink it, invert it, and the weight vector is '
    + 'the direction that best separates the classes. Anyone who has done a statistics course has seen this; the only '
    + 'addition is the shrinkage line.\n\n'
    + 'Explain shrinkage with the dimensionality argument: you are estimating 3,240 covariance entries from 720 '
    + 'samples. The estimate is unreliable and often not invertible. Shrinking toward a scaled identity matrix trades '
    + 'a little bias for a lot of variance reduction. Lambda is a tunable in config.py — tell them to try 0.1 and 0.9 '
    + 'and watch the AUC move.\n\n'
    + 'Expect the question: why not a neural network? Give the honest answer — with 720 examples per subject and 80 '
    + 'features, deep learning does not reliably beat regularised LDA on P300, and the published work that does beat '
    + 'it uses far more data or transfer across subjects. Also, this trains in milliseconds between two phases of the '
    + 'experiment, which matters when a participant is sitting waiting.\n\n'
    + 'Close on the right-hand panel: a single flash score is weak evidence. The system is designed around that fact.');
}

/* ------------------------------------------------------------------ 16 */
{
  const s = content('Evaluating the classifier', 'signal processing');
  s.addImage({ path: IMG + 'training-view.png', x: 0.6, y: 1.5, w: 7.1, h: 4.44 });
  const items = [
    ['AUC', 'Probability that a randomly chosen target epoch scores higher than a randomly chosen non-target epoch.'],
    ['ERP panel', 'Whether the target and non-target averages separate around 300 ms.'],
    ['Discriminability map', 'Which channels and time points carry the discriminating information.'],
    ['Confusion matrix', 'Computed by five-fold stratified cross-validation, not on the training data.'],
  ];
  items.forEach((it, i) => {
    const y = 1.5 + i * 0.95;
    s.addText(it[0], { x: 8.0, y, w: 4.7, h: 0.3, isTextBox: true, margin: 0, fontSize: 15, bold: true, fontFace: BF, color: PRIMARY });
    s.addText(it[1], { x: 8.0, y: y + 0.32, w: 4.7, h: 0.58, isTextBox: true, margin: 0, fontSize: 12.5, fontFace: BF, color: MUTED, lineSpacingMultiple: 1.03 });
  });
  card(s, 8.0, 5.35, 4.7, 1.0, TINT);
  s.addText([
    { text: '0.50 chance  ·  0.60-0.75 usable', options: { breakLine: true } },
    { text: '0.75-0.85 good  ·  0.85+ excellent', options: {} },
  ], {
    x: 8.2, y: 5.52, w: 4.3, h: 0.7, isTextBox: true, margin: 0,
    fontSize: 12.5, fontFace: MF, color: BODY, lineSpacingMultiple: 1.1,
  });
  s.addNotes(
    'TIMING: 3 minutes.\n\n'
    + 'This window appears automatically after training in the real system, and it is the moment where you decide '
    + 'whether to continue or re-cap the participant. Teach them to read it in this order.\n\n'
    + 'AUC first. Define it properly: take one random target epoch and one random non-target epoch; AUC is the '
    + 'probability the target scores higher. 0.5 is a coin flip. Explain why we use it here — it is insensitive to '
    + 'the 1:5 class imbalance, unlike accuracy.\n\n'
    + 'Then the ERP panel as a sanity check: if AUC is high but the ERP shows no bump around 300 ms, be suspicious — '
    + 'you may be classifying an artefact, for instance eye movement correlated with the cue.\n\n'
    + 'The discriminability map is the physiological check: information should concentrate at Cz and Pz, between '
    + 'roughly 250 and 500 ms. If it is all at 0 ms or all frontal, something is wrong.\n\n'
    + 'Stress cross-validation. Ask what would happen if we evaluated on the training data — the answer is a beautiful '
    + 'number and a speller that cannot spell. Five stratified folds, each keeping the class ratio.\n\n'
    + 'If the live demo goes well today, come back to this window and read the real numbers with them.');
}

/* ------------------------------------------------------------------ 17 */
{
  const s = content('Evidence accumulation and decoding', 'signal processing');
  s.addImage({ path: IMG + 'evidence.png', x: 0.6, y: 1.55, w: 7.6, h: 2.49 });
  caption(s, 0.6, 4.1, 7.6, 'Accumulated evidence for each row and column as repetitions proceed.');
  mono(s, 0.6, 4.55, 7.6, 1.6, [
    { text: 'for each flash:  scores[group] += w @ x + b' },
    { text: 'at the end:      mean = scores[group] / counts[group]', color: ACCENT },
    { text: 'best row = argmax over rows, best col = argmax over cols' },
    { text: 'letter   = matrix[best row][best col]', color: ACCENT },
  ], 12.5);
  card(s, 8.5, 1.55, 4.2, 4.6);
  s.addText('Why averaging helps', {
    x: 8.8, y: 1.78, w: 3.6, h: 0.32, isTextBox: true, margin: 0,
    fontSize: 16, bold: true, fontFace: BF, color: DARK,
  });
  bullets(s, 8.8, 2.25, 3.65, 3.7, [
    'Noise is independent between flashes; the response is not.',
    'Summing 12 repetitions increases the signal by 12 and the noise by √12.',
    'The signal-to-noise ratio therefore improves by a factor of about 3.5.',
    'Dividing by the number of flashes keeps groups comparable if a block ends early.',
  ], 13.5);
  s.addNotes(
    'TIMING: 3 minutes.\n\n'
    + 'This slide brings the analysis section together: the classifier is weak for a single flash, and the repetition '
    + 'structure of the paradigm is what makes the decision reliable.\n\n'
    + 'Walk the code block line by line — it is four lines and it is literally what runs. Each flash adds its score '
    + 'to whichever row or column was lit. At the end you have 12 totals: six rows, six columns. Take the best of '
    + 'each and intersect.\n\n'
    + 'Then do the square-root-of-n argument on the board, because this is the most transferable idea in the lecture '
    + 'and applies far beyond BCI. Signal adds coherently — N times. Noise adds incoherently — root N times. So the '
    + 'ratio improves as root N. Twelve repetitions gives about 3.5 times better SNR than one.\n\n'
    + 'Ask the obvious follow-up: why not 100 repetitions? Because the user is waiting, and because attention decays. '
    + 'That is exactly the trade-off on the next slide.\n\n'
    + 'Also point out the division by count: if a block is interrupted, some groups may have been flashed once more '
    + 'than others, and comparing raw sums would then be biased.');
}

/* ------------------------------------------------------------------ 18 */
{
  const s = content('Accuracy versus number of repetitions', 'signal processing');
  s.addImage({ path: IMG + 'accuracy-vs-repetitions.png', x: 0.6, y: 1.55, w: 7.2, h: 3.46 });
  caption(s, 0.6, 5.1, 7.2, 'Letter accuracy as a function of the number of repetitions, from a recorded session.');
  card(s, 8.1, 1.55, 4.6, 2.25, TINT);
  s.addText('Spelling rate', {
    x: 8.35, y: 1.72, w: 4.1, h: 0.3, isTextBox: true, margin: 0,
    fontSize: 15, bold: true, fontFace: BF, color: PRIMARY,
  });
  s.addText([
    { text: '12 reps -> 22 s/letter -> ~2.7 letters/min', options: { breakLine: true } },
    { text: ' 6 reps -> 11 s/letter -> ~5.5 letters/min', options: { breakLine: true } },
    { text: ' ', options: { breakLine: true } },
    { text: 'but only if accuracy holds up', options: { color: AMBER } },
  ], {
    x: 8.35, y: 2.15, w: 4.1, h: 1.5, isTextBox: true, margin: 0,
    fontSize: 13, fontFace: MF, color: BODY, lineSpacingMultiple: 1.18,
  });
  card(s, 8.1, 4.0, 4.6, 2.15, 'E7F6F1');
  s.addText('Dynamic stopping', {
    x: 8.35, y: 4.18, w: 4.1, h: 0.3, isTextBox: true, margin: 0,
    fontSize: 15, bold: true, fontFace: BF, color: ACCENT,
  });
  s.addText('Instead of a fixed number of repetitions, flashing continues until the difference between the leading group and the others exceeds a threshold. Easy letters then take about 6 seconds and difficult ones longer.', {
    x: 8.35, y: 4.6, w: 4.1, h: 1.4, isTextBox: true, margin: 0,
    fontSize: 13, fontFace: BF, color: BODY, lineSpacingMultiple: 1.05,
  });
  s.addNotes(
    'TIMING: 2 minutes.\n\n'
    + 'Read the curve with them: accuracy climbs steeply for the first few repetitions and then flattens. The '
    + 'interesting region is the knee — that is where you want to operate.\n\n'
    + 'Do the letters-per-minute arithmetic openly. Halving the repetitions doubles the speed, but a wrong letter '
    + 'costs a correction, which costs another letter. There is a real optimum, and it is different for every '
    + 'participant and every session.\n\n'
    + 'Mention information transfer rate (bits per minute) as the standard way to score this in papers, combining '
    + 'speed and accuracy into one number — but say that letter accuracy and letters per minute are what you report '
    + 'to a user.\n\n'
    + 'Then introduce dynamic stopping: about twenty lines in this implementation, and a self-contained project topic. '
    + 'Stopping when the leading group is sufficiently ahead turns a fixed 22 seconds into a variable 6 to 25 seconds '
    + 'at comparable accuracy.');
}

/* ------------------------------------------------------------------ 19 */
{
  const s = content('Processing one letter, step by step', 'signal processing');
  const acts = [
    ['Stimulus client', 'draws the cue, flashes group 7, writes stimulus.rowFlash into the buffer', PRIMARY],
    ['Buffer', 'stamps that event with the current sample count and stores it', DARK],
    ['Acquisition client', 'keeps pushing samples from the amplifier, 128 per second, knowing nothing about flashes', ACCENT],
    ['Signal processor', 'wakes on the event, waits for 77 more samples, slices, filters, scores, adds to the row total', PRIMARY],
    ['Repeat 144 times', 'approximately 22 seconds in total', MUTED],
    ['Signal processor', 'picks the best row and column, writes classifier.prediction R', ACCENT],
    ['Stimulus client', 'was blocked waiting for exactly that event — shows the letter and appends it to the text', PRIMARY],
  ];
  acts.forEach((a, i) => {
    const y = 1.45 + i * 0.705;
    card(s, 0.6, y, 12.1, 0.62, i % 2 ? WHITE : TINT);
    s.addShape(pres.ShapeType.ellipse, { x: 0.8, y: y + 0.16, w: 0.32, h: 0.32, fill: { color: a[2] } });
    s.addText(String(i + 1), { x: 0.8, y: y + 0.19, w: 0.32, h: 0.28, isTextBox: true, margin: 0, fontSize: 11, bold: true, fontFace: BF, color: WHITE, align: 'center' });
    s.addText(a[0], { x: 1.3, y: y + 0.17, w: 2.5, h: 0.3, isTextBox: true, margin: 0, fontSize: 14, bold: true, fontFace: BF, color: DARK });
    s.addText(a[1], { x: 3.9, y: y + 0.17, w: 8.6, h: 0.3, isTextBox: true, margin: 0, fontSize: 13, fontFace: BF, color: MUTED });
  });
  s.addText('The four programs above exchange no function calls; they interact only through the buffer.', {
    x: 0.6, y: 6.4, w: 12.1, h: 0.35, isTextBox: true, margin: 0,
    fontSize: 15, bold: true, italic: true, fontFace: BF, color: PRIMARY, align: 'center',
  });
  s.addNotes(
    'TIMING: 3 minutes.\n\n'
    + 'This is the consolidation slide. Everything in parts 1 to 3 appears here in order, so use it to check '
    + 'understanding rather than to introduce anything new.\n\n'
    + 'Good way to run it: cover the rows and reveal them one at a time, asking the class who acts next. They should '
    + 'be able to predict most of it by now.\n\n'
    + 'Highlight row 3 deliberately: the acquisition client has no idea any of this is happening. It pushes samples '
    + 'whether an experiment is running or not. That decoupling is the architecture doing its job.\n\n'
    + 'Row 7 closes the loop: the stimulus client was blocked on a WAIT for the prediction event, which is the same '
    + 'mechanism from slide 7 used in the other direction.\n\n'
    + 'End on the bottom line and let it sit for a second. Then take questions before moving to the engineering '
    + 'section — this is the natural breakpoint of the lecture.');
}

/* ------------------------------------------------------------------ 20 */
{
  const s = content('Data storage and file formats', 'implementation notes');
  mono(s, 0.6, 1.55, 6.5, 3.5, [
    { text: 'sessions/2026-09-23_1540/', color: ACCENT },
    { text: '  header            channels, rate, dtype' },
    { text: '  header.txt        the same, readable' },
    { text: '  samples           raw EEG, binary' },
    { text: '  events            every event, in order' },
    { text: '  calibration_epochs.npz', color: ACCENT },
    { text: '  clsfr.pkl         the trained model' },
    { text: '  training_summary.json', color: ACCENT },
  ], 12.5);
  const pts = [
    ['FieldTrip offline format', 'The same layout written by buffer_bci, so existing MATLAB tools read these recordings directly.'],
    ['Raw data first', 'Samples and events are written as they arrive; epochs, models and summaries are derived files that can be recomputed.'],
    ['One directory per session', 'A result is reproduced by running the analysis on the same directory again.'],
  ];
  pts.forEach((p, i) => {
    step(s, i + 1, 7.5, 1.55 + i * 1.5, 5.2, p[0], p[1], i === 1 ? PRIMARY : ACCENT);
  });
  card(s, 0.6, 5.3, 6.5, 0.85, 'FCF3E3');
  s.addText('A recorded session is the basis for offline analysis and for reproducing a result; a recording session with a participant cannot be repeated.', {
    x: 0.85, y: 5.48, w: 6.0, h: 0.6, isTextBox: true, margin: 0,
    fontSize: 13.5, italic: true, fontFace: BF, color: BODY,
  });
  s.addNotes(
    'TIMING: 2 minutes.\n\n'
    + 'Show the directory listing and say what each file is for. The important distinction is raw versus derived: '
    + 'samples and events are irreplaceable; epochs, the model and the summary can always be recomputed.\n\n'
    + 'The interoperability point matters for this lab specifically — anyone with MATLAB and buffer_bci can open '
    + 'these recordings, and the repository has a test that proves it by reading a session with the original '
    + 'FieldTrip client code.\n\n'
    + 'Make the research-practice argument: a recorded session is the only thing that makes a result checkable. When '
    + 'they write up an assignment, the session directory is their evidence.\n\n'
    + 'Practical warning for the lab: disk fills quickly with 8 channels at 128 Hz for an hour — have them work out '
    + 'that it is only a few megabytes, and then point out that a 64-channel 512 Hz system is a hundred times more.');
}

/* ------------------------------------------------------------------ 21 */
{
  const s = content('Graphical user interface', 'implementation notes');
  s.addImage({ path: IMG + 'launcher.png', x: 0.7, y: 1.55, w: 3.6, h: 3.09 });
  caption(s, 0.7, 4.72, 3.6, 'The launcher window used to start a session.');
  const pts = [
    ['Implemented in tkinter', 'Part of the standard library, so no additional installation is required.'],
    ['The interface only writes events', 'Pressing "Calibrate" writes startPhase.cmd into the buffer; it performs no other action.'],
    ['Timing is not handled here', 'Stimulus timing is in a separate process, so a slow redraw cannot delay a flash.'],
    ['Threading rule', 'Buffer reads run on a background thread and results are passed to the interface thread through a queue.'],
  ];
  pts.forEach((p, i) => {
    step(s, i + 1, 4.75, 1.6 + i * 1.22, 7.9, p[0], p[1], i === 2 ? AMBER : PRIMARY);
  });
  s.addNotes(
    'TIMING: 2 minutes.\n\n'
    + 'Students consistently underestimate this problem, so make it concrete: if the flashing loop lives in the same '
    + 'thread as the GUI, then dragging a window, opening a menu, or a slow redraw delays a flash by tens of '
    + 'milliseconds — and you have just smeared your ERP.\n\n'
    + 'The fix here is architectural rather than clever: the GUI is a client like any other. It writes a command '
    + 'event and reads status events. It could be replaced by a command line, a web page, or a foot pedal without '
    + 'the experiment noticing.\n\n'
    + 'The threading rule is worth stating as a general lesson they will meet in every language: never touch UI '
    + 'objects from a background thread; put the result on a queue and let the UI thread pick it up.\n\n'
    + 'If time is short, this is the slide to compress — mention the two bold lines and move on to testing.');
}

/* ------------------------------------------------------------------ 22 */
{
  const s = content('Testing and reproducibility', 'implementation notes');
  const pts = [
    ['Simulated participant', 'The simulator produces an event-related response of known amplitude and latency, with interference, blinks and drift.', ACCENT],
    ['Compressible experiment time', 'All delays pass through one clock class with a speed factor, so a 22-second letter can be run in a fraction of a second.', PRIMARY],
    ['Fixed random seeds', 'The same seed produces the same flash sequence and the same result, so a failing test is reproducible.', PRIMARY],
    ['Protocol compatibility test', 'One test drives this server with the original FieldTrip client code, verifying the protocol implementation.', ACCENT],
  ];
  pts.forEach((p, i) => {
    const x = 0.6 + (i % 2) * 6.35, y = 1.55 + Math.floor(i / 2) * 2.3;
    card(s, x, y, 6.0, 2.05);
    step(s, i + 1, x + 0.3, y + 0.35, 5.45, p[0], p[1], p[2]);
  });
  const nums = [['145', 'tests'], ['40 s', 'full run'], ['0', 'devices needed'], ['100×', 'time compression']];
  nums.forEach((v, i) => {
    const x = 0.75 + i * 3.0;
    s.addText(v[0], { x, y: 6.15, w: 1.4, h: 0.5, isTextBox: true, margin: 0, fontSize: 26, bold: true, fontFace: TF, color: PRIMARY, align: 'right' });
    s.addText(v[1], { x: x + 1.5, y: 6.3, w: 1.6, h: 0.35, isTextBox: true, margin: 0, fontSize: 12.5, fontFace: BF, color: MUTED });
  });
  s.addNotes(
    'TIMING: 2 minutes.\n\n'
    + 'Frame the section with the question: how is a program tested when its input is a human brain? This is the part '
    + 'most student projects omit.\n\n'
    + 'The answer is to make everything that is not the brain fake-able. The simulator gives you a subject. The clock '
    + 'abstraction gives you time control — every sleep in the experiment goes through one class, so multiplying by a '
    + 'speed factor compresses the whole session. The seed gives you determinism.\n\n'
    + 'The wire-compatibility test is worth singling out as an engineering habit: we claim to implement the FieldTrip '
    + 'protocol, so there is a test that runs the original client against our server. Claims in a README are not '
    + 'evidence; a test is.\n\n'
    + 'Tie it back to their own work: in the lab assignment, ask them how they would test their change without '
    + 'booking a participant. The answer should always start with the simulator.');
}

/* ------------------------------------------------------------------ 23 */
{
  const s = content('Demonstration', 'demonstration and extensions');
  mono(s, 0.6, 1.55, 6.4, 2.6, [
    { text: '$ pyspeller run --simulate --speed 4', color: ACCENT },
    '',
    { text: '# or, with the amplifier:' , color: '8E97B5' },
    { text: '$ pyspeller run --lsl' },
    '',
    { text: '# and just the GUI:', color: '8E97B5' },
    { text: '$ pyspeller gui' },
  ], 13);
  const watch = [
    'The cue, followed by 144 flashes for one letter',
    'The training window: AUC, ERP and discriminability map',
    'Feedback: the decoded letter appearing in the text line',
    'Stopping the signal processor during a run and restarting it',
    'Pausing and switching phase while a block is running',
  ];
  card(s, 7.35, 1.55, 5.35, 4.6);
  s.addText('Points to observe', {
    x: 7.65, y: 1.78, w: 4.75, h: 0.32, isTextBox: true, margin: 0,
    fontSize: 16, bold: true, fontFace: BF, color: DARK,
  });
  bullets(s, 7.65, 2.25, 4.75, 3.7, watch, 14);
  card(s, 0.6, 4.4, 6.4, 1.75, 'FCF3E3');
  s.addText('If errors occur', {
    x: 0.85, y: 4.58, w: 5.9, h: 0.3, isTextBox: true, margin: 0,
    fontSize: 14, bold: true, fontFace: BF, color: AMBER,
  });
  s.addText('Use the failure as an exercise: identify which process is responsible and how this can be established. The buffer contains every event that has occurred.', {
    x: 0.85, y: 4.95, w: 5.9, h: 1.1, isTextBox: true, margin: 0,
    fontSize: 13.5, fontFace: BF, color: BODY, lineSpacingMultiple: 1.05,
  });
  s.addNotes(
    'TIMING: 8 minutes. Leave it running while you talk.\n\n'
    + 'Start the simulated run at speed 4 so a letter takes about five seconds rather than twenty-two. Say out loud '
    + 'that you are compressing time and that this is the same mechanism the test suite uses.\n\n'
    + 'Narrate the phases as they happen: cue, flashes, the training window with real numbers, then feedback where '
    + 'the letters appear.\n\n'
    + 'A useful part of the demonstration is to stop a component deliberately: end the signal-processing process during '
    + 'a feedback block and restart it. Stimulus presentation continues and the classifier rejoins, which shows the '
    + 'independence of the clients more directly than the diagram does.\n\n'
    + 'If you have an amplifier and a volunteer, run the LSL path with a real cap; it is worth the setup time. Keep '
    + 'the simulated run as your fallback and have it already started in another window.\n\n'
    + 'Have the repository open in an editor so you can jump to the file behind whatever they ask about.');
}

/* ------------------------------------------------------------------ 24 */
{
  const s = content('Possible extensions and project topics', 'demonstration and extensions');
  const ideas = [
    ['Dynamic stopping', 'Stop the flashing when the leading group is sufficiently ahead. About 20 lines; reduces the time per letter.', ACCENT],
    ['Other selection tasks', 'Simple games such as a grid target task or tic-tac-toe. The decoder is unchanged and the target is known, so trials are labelled.', ACCENT],
    ['A different alphabet', 'The Kazakh 6×8 layout is already implemented: 42 letters, with the interface language following the layout.', PRIMARY],
    ['Artefact handling', 'Detect and reject blinks online rather than discarding epochs afterwards.', PRIMARY],
    ['A different classifier', 'Any model implementing fit and decision_function can be substituted.', PRIMARY],
  ];
  ideas.forEach((it, i) => {
    const y = 1.6 + i * 1.03;
    step(s, i + 1, 0.65, y, 7.9, it[0], it[1], it[2]);
  });
  s.addImage({ path: IMG + 'kazakh-matrix.png', x: 9.0, y: 1.6, w: 3.35, h: 2.88 });
  caption(s, 9.0, 4.55, 3.5, 'The same system with the Kazakh 6×8 layout.');
  card(s, 8.95, 5.05, 3.75, 1.1, 'E7F6F1');
  s.addText('Each of these affects a single module and can be tested with the simulator before any recording.', {
    x: 9.2, y: 5.25, w: 3.3, h: 0.8, isTextBox: true, margin: 0,
    fontSize: 12.5, fontFace: BF, color: BODY, lineSpacingMultiple: 1.05,
  });
  s.addNotes(
    'TIMING: 2 minutes.\n\n'
    + 'These are project suggestions — say which ones you will accept as assignments and roughly what a good '
    + 'submission looks like.\n\n'
    + 'Dynamic stopping is the most self-contained of these: small, measurable, and demonstrable with the simulator '
    + 'alone, without a participant.\n\n'
    + 'For the selection-task topic, note the useful property that the target is known in advance, so every trial is '
    + 'labelled and the task itself produces calibration data.\n\n'
    + 'The Kazakh grid is already implemented — use it to make the point that the matrix is data, not code, so '
    + 'supporting a new language means adding a tuple.\n\n'
    + 'Remind them of the rule for all of these: write the test with the simulator first, then the feature.');
}

/* ------------------------------------------------------------------ 25 */
{
  const s = pres.addSlide();
  s.background = { color: DARK };
  s.addText('CONCLUSION', {
    x: 0.8, y: 0.85, w: 8, h: 0.3, isTextBox: true, margin: 0,
    fontSize: 12, bold: true, charSpacing: 2.5, fontFace: BF, color: ACCENT,
  });
  s.addText('Summary', {
    x: 0.8, y: 1.2, w: 9, h: 0.7, isTextBox: true, margin: 0,
    fontSize: 34, bold: true, fontFace: TF, color: WHITE,
  });
  const takeaways = [
    ['Time is measured in samples', 'Events are indexed by sample number rather than by clock time, which makes stimulus and EEG directly comparable.'],
    ['Components communicate through a shared buffer', 'Samples and events in one store; no direct calls between programs.'],
    ['Repeated weak evidence', 'A single flash is uninformative; 24 scores decide a letter, because signal accumulates faster than noise.'],
    ['The system is testable offline', 'A simulated participant and compressible time allow the whole system to be tested without hardware.'],
  ];
  takeaways.forEach((t, i) => {
    const x = 0.8 + (i % 2) * 6.2, y = 2.25 + Math.floor(i / 2) * 1.65;
    s.addShape(pres.ShapeType.ellipse, { x, y: y + 0.05, w: 0.42, h: 0.42, fill: { color: i % 3 === 0 ? ACCENT : '2F3E9E' } });
    s.addText(String(i + 1), { x, y: y + 0.09, w: 0.42, h: 0.35, isTextBox: true, margin: 0, fontSize: 14, bold: true, fontFace: BF, color: WHITE, align: 'center' });
    s.addText(t[0], { x: x + 0.6, y, w: 5.3, h: 0.35, isTextBox: true, margin: 0, fontSize: 17, bold: true, fontFace: BF, color: WHITE });
    s.addText(t[1], { x: x + 0.6, y: y + 0.42, w: 5.3, h: 0.9, isTextBox: true, margin: 0, fontSize: 13, fontFace: BF, color: 'A8B2CF', lineSpacingMultiple: 1.08 });
  });
  s.addShape(pres.ShapeType.line, { x: 0.8, y: 5.85, w: 11.7, h: 0, line: { color: '2A3358', width: 1 } });
  s.addText([
    { text: 'the code      ', options: { color: '8E97B5' } },
    { text: 'github.com/berdakh/pyspeller', options: { color: ACCENT, bold: true, breakLine: true } },
    { text: 'the tutorial  ', options: { color: '8E97B5' } },
    { text: 'berdakh.github.io/pyspeller', options: { color: ACCENT, bold: true } },
  ], {
    x: 0.8, y: 6.05, w: 7.5, h: 0.7, isTextBox: true, margin: 0,
    fontSize: 13.5, fontFace: MF, lineSpacingMultiple: 1.15, valign: 'top',
  });
  s.addText('Reading before the laboratory session:\nthe tutorial pages on the architecture and the first run.', {
    x: 8.6, y: 6.05, w: 3.9, h: 0.7, isTextBox: true, margin: 0,
    fontSize: 13, italic: true, fontFace: BF, color: 'C3CBE4', align: 'right', lineSpacingMultiple: 1.2,
  });
  footer(s, true);
  s.addNotes(
    'TIMING: 3 minutes.\n\n'
    + 'Close by returning to the learning objectives on slide 3 and asking the class to answer them: the structure of '
    + 'the system, how stimulus and EEG are aligned in time, the path from samples to a letter, and what they would '
    + 'change first.\n\n'
    + 'The four points are general rather than specific to the P300: sample-indexed timing, communication through a '
    + 'shared store, averaging of repeated weak measurements, and simulation of the input for testing. All four recur '
    + 'in robotics and in other real-time systems.\n\n'
    + 'Point them to the tutorial site for everything the lecture skipped: the electrode physics, the g.tec setup, '
    + 'the exercises and the troubleshooting guide.\n\n'
    + 'Set the expectation for the lab: read the first-run page, come with the environment installed, and be ready to '
    + 'run the simulator on their own machine.');
}

pres.writeFile({ fileName: OUT + 'pyspeller-lecture.pptx' }).then(f => console.log('wrote', f));
