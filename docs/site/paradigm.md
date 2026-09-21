---
title: How a P300 speller works
description: From microvolts on the scalp to a letter on the screen — the whole idea in one page, with real data.
kicker: 01 · Orientation
---

## EEG in five minutes

Neurons signal with electricity. When many thousands of them in the same patch
of cortex fire in step, the summed field is large enough to be measured at the
scalp — a few **microvolts** (µV), a millionth of a volt, about a hundred
thousand times smaller than an AA battery. That measurement is the
**electroencephalogram**, EEG.

Practical consequences of the size of that number:

- **Everything is noise until proven otherwise.** Mains hum, a loose electrode,
  a blink, a swallow, jaw tension — all of these are much larger than the brain
  signal you want.
- **Where you measure matters.** Electrodes are placed by the international
  **10–20 system**, which names positions by region and side: `Fz` is front
  centre, `Cz` the top of the head, `Pz` behind it, `Oz` at the back, odd
  numbers on the left, even on the right.
- **You always measure a difference.** Each electrode is read against a
  **reference** (often an earlobe or mastoid), with a **ground** somewhere
  neutral. Change the reference and every waveform changes shape.

<figure>
<img src="assets/img/montage.svg" alt="Head seen from above with the ten-twenty electrode positions marked, the P300 montage highlighted">
<figcaption>The ten channels that matter for a speller. If your amplifier has 16 or 32, use them all — but make sure these are among them.</figcaption>
</figure>

## Evoked responses: finding a signal in the noise

An **event-related potential** (ERP) is the brain's stereotyped response to an
event — a flash, a beep, a touch. A single one is invisible: a few µV of
response inside 20 µV of ongoing EEG. But it is *time-locked* to the event and
the noise is not, so if you repeat the event and average the segments that
follow it, the response survives and the noise shrinks with the square root of
the number of repetitions.

That segment — the data from an event to a fixed time after it — is called an
**epoch**. Here every epoch is the 600 ms after a flash.

<figure>
<img src="assets/img/erp.png" alt="Eight channels of averaged EEG, target and non-target traces, with a large positive peak at 300 ms">
<figcaption>Real output from this software: 150 target and 750 non-target epochs from one calibration run, averaged. The green trace is the response to flashes the participant was attending to. The bump at 300 ms is the P300, largest at Cz and Pz.</figcaption>
</figure>

## The P300

Around **300 milliseconds** after a stimulus that is *rare* and *relevant to
what you are doing*, a broad positive wave appears over the centre and back of
the head. It is called the **P300** (positive, 300 ms). It is not produced by
the flash itself — it is produced by the flash *mattering to you*. A flash you
are ignoring produces a much smaller response.

That is the entire trick of this BCI: **you cannot move, but you can choose what
to attend to, and attention is visible in the EEG.**

The classic way to bring the P300 out is the **oddball**: a stream of frequent
events with a rare one mixed in, and a task that forces the participant to
notice the rare one. In a speller, the task is: *silently count each time the
letter you are looking at flashes.*

## The matrix speller

Farwell and Donchin proposed this in 1988 and it is still the standard. Lay the
alphabet out in a grid. Flash whole **rows and columns** in random order. The
participant attends to one letter. Only two of the twelve flashes in a
repetition contain that letter — one row and one column — so those two produce a
P300 and the other ten do not.

<figure>
<img src="assets/img/matrix-decode.svg" alt="A six by six grid with one row and one column highlighted, and bar charts of the score for each row and column">
<figcaption>Score every flash, average the scores per row and per column, and the winning row and column intersect at the letter. Flashing groups rather than single letters is what makes this fast: 12 flashes cover 36 letters.</figcaption>
</figure>

Because one repetition is not enough to be sure, the whole set of rows and
columns is flashed several times — by default **12 repetitions**, 144 flashes,
about 22 seconds per letter — and the scores are averaged.

<figure>
<img src="assets/img/evidence.png" alt="Two panels showing the running average score for each row and each column as repetitions accumulate">
<figcaption>Evidence accumulating while one letter is spelled. Each line is a row (left) or column (right); the green one contains the attended letter. After a few repetitions it separates from the rest and stays there.</figcaption>
</figure>

<figure>
<img src="assets/img/accuracy-vs-repetitions.png" alt="Accuracy rising from chance to one hundred percent as repetitions increase">
<figcaption>The trade-off you will be tuning: more repetitions means more accuracy and slower typing. Measured with this software on ten letters; your participant's curve will differ.</figcaption>
</figure>

## What the computer actually does

<figure>
<img src="assets/img/session-timeline.svg" alt="Timeline of one letter: cue, flashes, events, epochs, prediction">
<figcaption>One letter, from cue to decision. Every flash writes an event; the analysis client cuts a 600 ms epoch after each one and scores it.</figcaption>
</figure>

1. **Calibration.** The participant is told which letter to attend to, so every
   epoch can be labelled *target* or *non-target*. A few letters gives several
   hundred labelled epochs.
2. **Training.** A classifier learns the difference between the two kinds of
   epoch: pre-process (filter, reference, downsample), then a
   [linear discriminant](reference.html#glossary) over channels × time points.
3. **Feedback.** Now unlabelled: every flash is scored, scores are averaged per
   row and column, and the best row and column give the letter.

<figure>
<img src="assets/img/discriminability.png" alt="Heat map of AUC per channel and time point, warm around 300 milliseconds at the parietal channels">
<figcaption>Where the two classes actually differ, measured as <a href="reference.html#glossary">AUC</a> for each channel and time point. This is the picture to look at after training: the warm patch should sit over Cz/Pz around 300 ms. If it is flat, something is wrong with the cap, the task, or the participant's attention.</figcaption>
</figure>

## What makes it work badly

| Cause | What you see | What to do |
| --- | --- | --- |
| Participant not really attending | Flat discriminability map, AUC near 0.5 | Re-explain the counting task; keep blocks short |
| Blinks and movement | Huge slow swings, epochs rejected | Blink in the gaps, not during flashing; support the arms |
| A bad electrode | One channel far louder than the rest | Re-gel it; the software will drop it, but you lose a channel |
| Too few repetitions | Accuracy far below the AUC would suggest | Raise `--n-repetitions` |
| Flashes too fast | P300 to one flash overlaps the next | Keep the inter-stimulus interval at 150 ms or more |
| Target flashed twice in quick succession | Second response is weaker (refractory) | The software already forbids it within 3 flashes |

<div class="note">
<span class="block-title">Not everyone is a P300 speller user</span>
In published work with healthy volunteers, most people reach high accuracy
within a session, but a minority do not — tiredness, medication, and cap fit all
matter. If a participant's AUC stays near 0.6 after a careful calibration, that
is a result, not a failure of your work. Write it down and move on.
</div>
