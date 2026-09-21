---
title: Your first experiment
description: A whole session against the simulated participant — calibrate, train, spell — and what every screen is telling you.
kicker: 05 · Getting running
---

Start it:

```
python -m pyspeller run
```

## The launcher

<figure>
<img class="shadow" src="assets/img/launcher.png" alt="The launcher window with source, participant, matrix, language and repetitions">
<figcaption>Everything a session needs, before anything starts. With a real amplifier you would press <em>scan for amplifiers</em> and pick it from the list; today, leave the source on <em>simulated subject</em>.</figcaption>
</figure>

| Field | What it does |
| --- | --- |
| Source | Where the EEG comes from: the simulator, or a g.tec amplifier over LSL |
| Participant / experiment | Names the folder your recording goes into |
| Matrix | Which grid of symbols to spell from — the alphabet with editing keys, the classic grid, Kazakh, Russian, or a small 3×3 for demos |
| Language on screen | What the participant reads. Follows the matrix unless you change it |
| Repetitions per letter | How many times each row and column flashes. More = slower and more accurate |
| Record to disk | Writes the raw EEG and every event into `~/output/…` |

Press **Start session**. Two windows open: the **control panel** for you, and
the **speller** for the participant. In a real session you drag the speller onto
their monitor and maximise it.

## The control panel

<figure>
<img class="shadow" src="assets/img/panel-and-speller.png" alt="Control panel with buttons, live traces, signal quality bars, event log, and the speller matrix mid-flash">
<figcaption>Left to right: the phase buttons, the live EEG, the per-channel signal level, the event stream, and the speller itself with a row lit up and the typed text at the top.</figcaption>
</figure>

- **the traces** are the last five seconds of every channel. With the simulator
  you will see 1/f noise, an alpha rhythm, and the occasional simulated blink.
- **signal quality** is the level of each channel in microvolts. Green is
  healthy; orange and red mean a channel much louder than the others.
- **the event log** is the session's narrative — every cue, every sequence end,
  every prediction. Flashes are left out or it would scroll past too fast.
- **typed:** is what has been spelled so far, the same text the participant sees.

## Calibrate

Press **Calibrate**. The speller cues five letters (B, R, A, I, N) and flashes
rows and columns for each of them. With `--speed` at its default this is real
time, about two minutes; the simulated participant "attends" to the cued letter,
so the data is labelled.

Watch the event log: `simulation.target B`, then a burst of flashing, then
`stimulus.sequence end`, five times over, then `stimulus.training end`.

<div class="note">
<span class="block-title">You are not stuck with a block once it starts</span>
<b>⏸ pause</b> holds the flashing and resumes where it left off. <b>■ stop</b>
abandons the block. And pressing any other phase button — Calibrate while
practice is running, say — interrupts what is running and starts the new one.
Nothing gets wedged.
</div>

## Train

Press **Train classifier**. It takes a second, and a window opens.

<figure>
<img class="shadow" src="assets/img/training-view.png" alt="Training result window: AUC headline, ERP panel, discriminability map, confusion matrix">
<figcaption>The result of training, and the single most informative screen in the whole system. <a href="results.html">Reading the results</a> goes through it in detail.</figcaption>
</figure>

For now, one number matters: **cross-validated AUC**. It is the probability that
a randomly chosen target flash scores higher than a randomly chosen non-target
one — 0.5 is a coin toss, 1.0 is perfect. With the simulator you should see
**0.70–0.82**. If you see 0.5, something is broken; if you see 0.99, you are not
running the simulator you think you are.

## Spell

Press **Feedback**. The speller cues B, C, I in turn, flashes for each, and then
shows what the classifier decided — in green in the grid, and appended to the
text field. The panel's `typed:` line follows along.

Then press **Free spelling**: the same thing without a cue. This is the mode a
real user works in — they look at whatever they want and it appears.

<div class="warn">
<span class="block-title">Free spelling with the simulator types nonsense</span>
And it should. Without a cue, the simulated participant has nothing to attend
to, so there is no P300 to find and the classifier picks noise. With a real
participant this is the mode that matters.
</div>

## Correcting a letter

When a letter comes out wrong — and it will — the participant selects **DEL** in
the matrix, exactly like any other key, and the last character disappears. You
can also press **⌫ backspace** on the panel, which does the same from your side
and shows up in the event log as `speller.edit DEL`. `_` types a space.

## Without any windows

Everything above also works headless, which is how you test changes and how the
exercises are scored:

```
python -m pyspeller demo --speed 20
```

`--speed 20` compresses experiment time twenty-fold: the data in the buffer is
identical because everything is indexed by samples, but a four-minute session
takes twelve seconds. Useful flags:

| Flag | Meaning |
| --- | --- |
| `--n-repetitions 8` | fewer flashes per letter — faster, less accurate |
| `--layout kk` | the Kazakh matrix (also `ru`, `6x6`, `3x3`) |
| `--erp-amplitude 4` | a harder participant: a 4 µV P300 instead of 8 |
| `--noise-amplitude 20` | a noisier recording |
| `--save` | record the session to `~/output/…` |

<div class="do">
<span class="block-title">Try this before moving on</span>
Run <code>python -m pyspeller demo --speed 20 --erp-amplitude 4</code> and then
the same with <code>--erp-amplitude 12</code>. Watch what the AUC and the letter
accuracy do. You have just measured how signal strength turns into spelling
performance — which is the whole game with a real participant.
</div>
