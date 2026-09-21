---
title: Troubleshooting & glossary
description: Every error message we know about, every term defined, and where to read further.
kicker: 11 · Going deeper
---

## Troubleshooting

### Installing and starting

| Message | Fix |
| --- | --- |
| `python: command not found` | use `python3`, or reinstall python with *Add to PATH* |
| `No module named pyspeller` | run from inside the cloned folder |
| `No module named tkinter` | Linux: `sudo apt install python3-tk` |
| `no tk display available` | no screen on this machine; use `pyspeller demo` instead |
| `Address already in use` | a buffer is already running: use `--port 1973`, or stop the old one |

### The amplifier

| Message | Fix |
| --- | --- |
| `pylsl is not installed` | `pip install pylsl` |
| `no LSL stream matching name=… type='EEG'` | the connector is not streaming, or not on this network — see [the g.tec page](gtec.html#when-the-stream-is-not-there) |
| `stream has no nominal sample rate` | you picked a marker stream; name the EEG one with `--lsl-name` |
| `no header appeared in the buffer` | no acquisition client is running: start `pyspeller lsl` or `pyspeller simulator` |
| the scope is flat | the amplifier is sending zeros: check it is on, connected, and acquiring in g.tec's own software |
| every channel looks identical and noisy | reference or ground electrode is loose |

### The experiment

| Symptom | Fix |
| --- | --- |
| flashes happen, no letter ever appears | the analysis client is not running, or no classifier is trained — press **Train classifier** |
| `the 3x3 speller matrix has no 'Q'` | the word cannot be spelled in this layout; change `--layout` |
| a button does nothing | look at the panel's status line: if it does not say `ready: sigproc, stimulus`, a client is not up |
| AUC near 0.5 after a careful calibration | attention, impedances, or a cue the participant could not see. Re-explain the counting task and record again |
| good AUC, bad spelling | too few repetitions, or the participant lost the thread mid-letter |
| accuracy fell during the session | tiredness or drying gel. Break, re-check impedances, consider re-calibrating |

## Glossary {#glossary}

**Artefact** — anything in the recording that is not brain activity: blinks,
muscle, movement, mains hum, a loose electrode.

**AUC** — area under the ROC curve. The probability that a randomly chosen
target scores above a randomly chosen non-target. 0.5 is chance, 1.0 perfect.

**BCI** — brain–computer interface. A system that turns a measured brain signal
into a command, without using muscles.

**Buffer** — here, the server that holds recent samples and all events, and that
every client talks to. Also *ring buffer*: storage that keeps the most recent N
samples and overwrites the oldest.

**CAR** — common average reference. Subtracting the average of all channels from
each channel, which removes whatever they all share (reference drift, some
mains hum, distant muscle).

**Calibration** — the block where the participant is told what to attend to, so
the data can be labelled and a classifier trained.

**Cross-validation** — fitting on part of the data and scoring on the rest, so
that the score is not flattered by the fitting.

**Epoch** — the slice of signal following an event; here 600 ms after a flash.

**ERP** — event-related potential. The stereotyped response to an event,
recovered by averaging many repetitions.

**Feedback / free spelling** — spelling with the classifier running: with a cue
(so it can be scored) or without one (the real task).

**Impedance** — how well an electrode is connected, in kilohms. Low is good;
high means gel, abrasion, or a better contact is needed.

**ISI** — inter-stimulus interval, the time from one flash to the next (150 ms
by default).

**LDA** — linear discriminant analysis. A linear classifier that models each
class as a Gaussian with a shared covariance; with *shrinkage* that covariance is
pulled towards a simple one so it can be estimated from few epochs.

**LSL** — Lab Streaming Layer. The library that carries data between recording
programs on a lab network.

**Montage** — which electrodes you record and how they are referenced.

**Oddball** — a stimulus stream where the relevant event is rare. The reliable
way to produce a P300.

**P300** — the positive ERP peaking near 300 ms after a rare, attended event;
the signal this speller is built on.

**Ten–twenty system** — the standard naming and placement of scalp electrodes
(Fz, Cz, Pz, Oz, and so on).

## Further reading

**The framework this grew from**
- [buffer_bci](https://github.com/berdakh/buffer_bci) — the original MATLAB/Java
  framework, with `matlab/matrixSpeller` as the direct ancestor of this speller.
- Its [EEG BCI tutorial worksheet](https://github.com/berdakh/buffer_bci/blob/master/tutorial/EEGBCITutorial/EEGBCI_worksheet.md)
  — a practical lab course on EEG, artefacts, referencing and evoked responses.
  If you can get an afternoon with the cap and no participant, work through it.
- Its [visual speller lecture material](https://github.com/berdakh/buffer_bci/tree/master/tutorial/lect5-visspell).

**The protocols**
- [The FieldTrip realtime buffer](https://www.fieldtriptoolbox.org/development/realtime/)
  — the wire protocol our server speaks.
- [Lab Streaming Layer](https://github.com/sccn/labstreaminglayer) — the library
  and its device connectors.

**The science**
- Farwell & Donchin (1988), *Talking off the top of your head* — the original
  matrix speller.
- Krusienski et al. (2006) — which classifier and which channels for a P300
  speller.
- Guger et al. (2009) — how well a large group of people can actually use one.

**This repository**
- [The code](https://github.com/berdakh/pyspeller)
- [The printable session manual](https://github.com/berdakh/pyspeller/blob/main/docs/MANUAL.md)
- [The tutorial notebook](https://github.com/berdakh/pyspeller/blob/main/docs/pyspeller_tutorial.ipynb)
