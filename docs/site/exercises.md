---
title: Exercises
description: Seven pieces of work that take you from "it runs" to "I can run an experiment and defend the result".
kicker: 09 · Going deeper
---

Do them in order. The first four need no hardware. Each says what to hand in;
keep everything in one short report with the figures inline.

<div class="note">
<span class="block-title">How to measure anything here</span>
Every result below comes from <code>python -m pyspeller demo</code> or from the
notebook, both of which print the numbers you need. Use <code>--speed 20</code>
so a run takes seconds, and <strong>repeat every measurement at least three
times</strong> — a single run of a noisy experiment tells you very little.
</div>

## 1 · Get it running

Install, run the tests, and run one simulated session end to end through the
graphical interface: calibrate, train, feedback.

**Hand in:** a screenshot of the training window and one of the speller with a
word typed in it, plus the AUC you got.

## 2 · Repetitions against accuracy

How many repetitions does a letter need? Run the demo at 2, 4, 6, 8, 10, 12 and
15 repetitions, three times each, and plot letter accuracy against repetitions.

```
python -m pyspeller demo --speed 20 --n-repetitions 6
```

Then compute **letters per minute** at each point: one letter takes
`repetitions × groups × 0.15 s` plus about 2 s of cue and pause. Where is the
best trade-off for a participant who wants to write a sentence?

**Hand in:** the two curves (accuracy and letters per minute against
repetitions) and a sentence recommending a setting, with your reason.

## 3 · How much signal do you need?

`--erp-amplitude` sets the size of the simulated P300 in microvolts and
`--noise-amplitude` the background EEG. Vary the ratio between them and record
the cross-validated AUC and the letter accuracy.

```
python -m pyspeller demo --speed 20 --erp-amplitude 3 --noise-amplitude 10
```

**Hand in:** a table or plot of AUC against the signal-to-noise ratio, and the
smallest P300 that still spelled correctly at 12 repetitions. Relate it to the
real amplitudes you saw in [the paradigm page](paradigm.html).

## 4 · Does the pre-processing earn its keep?

In `pyspeller/config.py`, `spatial_filter` is `'car'` and `freq_band` is
`(0.1, 0.5, 10.0, 12.0)`. Re-run the calibration from the notebook and compare
cross-validated AUC with:

- the common average reference turned off (`spatial_filter='none'`),
- a wider band (say `(0.1, 0.5, 30.0, 35.0)`),
- a much lower analysis rate (`analysis_fsample=4`).

**Hand in:** four AUC numbers with an explanation of each change. One of them
will surprise you — say which, and why it happens. (Hint: what does a common
average reference actually remove, and where does the simulator put its noise?)

## 5 · A bad electrode

Simulate what happens when an electrode comes loose. Load a saved calibration
with `load_epochs`, multiply one channel by 50, and retrain.

- What does cross-validated AUC do?
- Does `preproc.find_bad_channels` catch it?
- What happens if you corrupt three of the eight channels?

**Hand in:** the numbers, and a recommendation for how many bad channels a
session can tolerate before you should stop and re-gel.

## 6 · A real recording

With the amplifier: run a full session on a willing volunteer, following
[Running a real session](session.html). Record it with `--save`.

**Hand in:** impedances, the AUC, the letters spelled and how many were right,
the training window screenshot, and your notes on what went wrong and what you
would do differently. A session with a poor AUC and a good explanation is worth
more marks than a good one you cannot account for.

## 7 · Make it yours

Pick one and do it properly, with a test that proves it works:

- **A new layout** — your own symbol set (a different alphabet, an icon-based
  communication board, a numeric keypad), registered in `config.py`.
- **A different classifier** — swap `ShrinkageLDA` for logistic regression or
  an SVM and compare cross-validated AUC on the same saved calibration data.
- **Dynamic stopping** — stop flashing as soon as one row and one column are
  clearly ahead, instead of always doing N repetitions. Measure the letters per
  minute you gain and the accuracy you lose.
- **A new client** — anything that watches the buffer: a second display, a
  logger, an online artefact detector that warns the operator when a channel
  goes bad.

**Hand in:** the diff, the passing test, and a paragraph on what you measured.

<div class="do">
<span class="block-title">What a good report looks like</span>
Numbers with the conditions that produced them, figures with axes and units,
and honest reporting of what did not work. "AUC dropped to 0.58 when I widened
the band and I do not know why" is a better sentence than a table of results
with no commentary.
</div>
