---
title: Running a real session
description: Consent, the cap, the impedances, the words you say, and what to do when it goes wrong — with a participant in the chair.
kicker: 07 · With hardware
---

This page assumes the amplifier is streaming ([the previous page](gtec.html))
and that you have practised the whole procedure on the simulator. There is a
condensed, printable version in
[docs/MANUAL.md](https://github.com/berdakh/pyspeller/blob/main/docs/MANUAL.md)
— take it into the lab.

<div class="stop">
<span class="block-title">Before a human being is involved</span>
Research on people needs ethical approval and informed consent — <em>your</em>
institution's, in writing, before the session. This is research equipment, not a
medical device: it diagnoses nothing and treats nothing, and you must not imply
otherwise to a participant. If they want to stop, the session stops
immediately, without discussion.
</div>

## Timing

| Step | Time |
| --- | --- |
| Consent, explanation, questions | 10 min |
| Cap, electrodes, impedances | 20 min |
| Signal check | 5 min |
| Calibration (5 letters) | 3 min |
| Training | 1 min |
| Feedback and free spelling | 10–20 min |
| Cleaning up | 15 min |

## Preparing the participant

<ol class="steps">
<li><strong>Explain first, touch later.</strong> Show them the cap, the gel, and
the screen. Tell them it is painless, that the gel washes out, that they can
stop at any time, and roughly how long it takes.</li>
<li><strong>Measure and fit the cap.</strong> Measure head circumference and
choose the size. Find <code>Cz</code>: halfway between nasion (bridge of the
nose) and inion (the bump at the back), and halfway between the two ear canals.
The cap's Cz goes there.</li>
<li><strong>Prepare each site.</strong> Part the hair with a blunt syringe tip,
abrade the skin gently, and fill with conductive gel until the impedance drops.
Do not dig — a good contact comes from contact, not pressure.</li>
<li><strong>Use the right channels.</strong> Fz, Cz, Pz, Oz, P3, P4, PO7, PO8 at
minimum, reference on an earlobe or mastoid, ground at AFz or FPz. More channels
are welcome. Prepare the reference and the ground as carefully as any channel —
<a href="sensors.html#8-reference-and-ground-the-question-everyone-asks">they are
in every number you record</a>.</li>
<li><strong>Check impedances in the g.tec software.</strong> Below 5 kΩ with gel
electrodes; dry electrodes read far higher, so use whatever threshold your lab
uses for that headset. Fix anything that stays high before you record.</li>
<li><strong>Seat them properly.</strong> About 60 cm from the screen, forearms
supported, feet flat. Ask them to find a position they can hold for twenty
minutes — comfort now prevents movement artefacts later.</li>
</ol>

## The signal check — five minutes that save an hour

Start the session (`python -m pyspeller run`, source = your amplifier) and watch
the panel's traces before recording anything.

| Ask them to | You should see |
| --- | --- |
| sit still, eyes open | wandering traces of roughly 10–30 µV, all channels similar |
| blink a few times | large slow deflections, biggest at Fz |
| clench the jaw | a burst of fast spiky activity that stops when they relax |
| close their eyes for 10 s | alpha: a visible ~10 Hz rhythm, strongest at Oz and Pz |

If a channel is flat, or far louder than its neighbours, or the whole montage
hums, fix it now: re-gel, check the reference and ground, move power supplies
away from the cap. Seeing alpha appear when they close their eyes is the best
single proof that you are recording brain activity and not an artefact.

## Calibration

Say this, in these words:

> A letter will be shown to you in green. Look at it, and keep looking at that
> spot. Rows and columns will flash quickly. Count silently, to yourself, each
> time the letter you are looking at flashes — start again at one for each new
> letter. Try not to blink while the flashing is going on; blink in the pauses
> between letters.

The counting matters. It is what makes the target flash *relevant* and the P300
appear. A participant who merely stares at the letter gives you a much smaller
response.

Press **Calibrate**. Watch the traces, not the grid. If they blink constantly or
shift in the chair, press **⏸ pause**, sort it out, and resume. If a block is
spoiled, **■ stop** it and start again — bad calibration data cannot be repaired
afterwards.

## Training, and what the number means

Press **Train classifier** and read the AUC:

| AUC | What it means | What to do |
| --- | --- | --- |
| above 0.75 | a good session | go and spell |
| 0.65 – 0.75 | usable | raise repetitions to 15, or record a second calibration block and retrain |
| below 0.65 | not good enough to spell with | check impedances, re-explain the counting task, give them a break, then re-calibrate |

A second calibration block is cheap — three minutes — and often turns a marginal
session into a good one, because the participant now knows what the task feels
like.

## Spelling

**Feedback** spells a known word and scores it: use it to show the participant
(and yourself) that it works. **Free spelling** lets them write what they like;
`DEL` fixes mistakes.

Give a break every ten minutes: attention decays, and with it the P300. A
five-minute rest usually restores accuracy better than any parameter change.

## Ending

Press **Quit**, remove the cap, and let them wash their hair. Clean the
electrodes and the cap immediately — dried gel destroys electrodes and blocks
the holes.

Before you leave the lab, write down: participant code, date, cap size, which
channels were bad, the AUC, how many letters were spelled and how many were
right, and anything unusual (tiredness, interruptions, a loose electrode). In
six months, the recording will be meaningless without those notes.

<div class="do">
<span class="block-title">The session checklist</span>
Consent signed · cap on · impedances checked and written down · amplifier
streaming and visible to <code>pyspeller lsl --list</code> · recording started ·
signal checked (blink, jaw, alpha) · calibration clean · classifier trained and
AUC noted · feedback block scored · free spelling done · data copied off the
machine · cap and electrodes cleaned.
</div>
