# pyspeller — buffer_bci as a pure-python framework

A minimal but complete BCI framework written entirely in python, with a working
P300 matrix speller on top of it.  It follows the same client–server
architecture as the rest of buffer_bci — a central buffer that stores data and
events, with independent clients around it — but every part of it, including
the buffer server itself, is python:

```
   g.tec amplifier ──LSL──▶ lsl_bridge.py ─┐
                                           ├─▶  buffer server  ◀─── control panel (gui)
   simulated amplifier ────────────────────┘     (data+events)        │      ▲
                                                   ▲       ▲          │      │
                                    stimulus ──────┘       └───── signal processing
                                    (speller display)              (epochs → classifier)
```

Nothing but `numpy` is required.  `pylsl` is needed only to talk to a real
amplifier, and `tkinter` only for the graphical interface.

![the control panel and the speller](docs/screenshot.png)

## Quick start

```bash
pip install numpy                       # the only hard dependency

# the whole thing in one process: buffer, simulated EEG, speller, gui
python -m pyspeller run

# or without any display: calibrate, train and spell, printing the results
python -m pyspeller demo --speed 10
```

`run` opens the control panel and the speller window.  Press **Calibrate** to
record a labelled block, **Train classifier** to fit the ERP classifier, then
**Feedback** to spell with it.  The panel shows the live signal, per-channel
signal quality, the event stream and the letters as they are decoded.

A typical run of `demo` prints something like:

```
[sigproc] gathered 360 epochs (120 target, 240 non-target)
[sigproc] classifier trained: cross-validated AUC 0.795, accuracy 0.74
spelled: B->B H->H D->D A->A F->F I->I
letter accuracy: 6/6
```

## Running the components separately

In a real experiment each client runs in its own process, often on different
machines (pass `--host`):

```bash
python -m pyspeller buffer                 # 1. the data and event server
python -m pyspeller simulator              # 2. an amplifier ... (or see below)
python -m pyspeller sigproc --model clsfr.pkl   # 3. online signal processing
python -m pyspeller speller                # 4. the stimulus display
python -m pyspeller gui                    # 5. control panel + live signals
```

The control panel publishes `startPhase.cmd` events; the speller and the signal
processing client obey them.  Any other client can do the same, which is how
the tests drive an experiment without a display.

## Using a g.tec amplifier over Lab Streaming Layer

g.tec devices (g.USBamp, g.HIamp, g.Nautilus) are published as an LSL stream by
g.NEEDaccess or the gtec LSL connector.  Start that on the amplifier machine,
then:

```bash
pip install pylsl                      # ships liblsl
python -m pyspeller lsl --list         # what is on the network?
# g.USBamp-UB-2016.03.06   type=EEG   channels=16  rate=256 Hz  host=lab-pc

python -m pyspeller lsl --name g.USBamp-UB-2016.03.06
# or take the only EEG stream on the network:
python -m pyspeller lsl --type EEG
```

The bridge copies samples into the buffer and writes the stream's channel
labels into the buffer header, so the rest of the framework sees the real
montage.  If a marker stream is present it is forwarded as `lsl.marker`
events, timestamp-aligned to the sample index.  To run everything against the
amplifier in one process:

```bash
python -m pyspeller run --lsl --lsl-type EEG
```

Points worth checking with real hardware: the LSL stream must have a nominal
sample rate (the buffer is a regularly sampled store), and the speller's
`--isi` should be a multiple of the amplifier's block size if the device sends
large blocks, otherwise flash timing is quantised to the block.

## What the pipeline does

| stage | where | what |
| --- | --- | --- |
| stimulus | `speller/stimulus.py` | flashes each row and column `n_repetitions` times in random order, never repeating a group within `min_gap` flashes |
| events | buffer | `stimulus.rowFlash` / `stimulus.colFlash` carry the flashed index; during calibration `stimulus.tgtFlash` carries the 1/0 label |
| epoching | `signalproc/epochs.py` | cuts the 600 ms after each flash once those samples have arrived |
| pre-processing | `signalproc/preproc.py` | linear detrend, common average reference, trapezoidal 0.5–10 Hz FFT band-pass, boxcar downsample to 16 Hz, outlier channel/epoch rejection |
| classification | `signalproc/classifier.py` | shrinkage LDA over channels × time, reported with stratified 5-fold cross-validated AUC |
| decoding | `speller/matrix.py` | classifier output is averaged per row and per column; the best row and best column intersect at the predicted letter |
| feedback | buffer | `classifier.prediction` carries the letter; the speller displays it |

Everything is configured from one place, `pyspeller/config.py` (the
counterpart of `configureSpeller.m`): grid layout, timing, filter band,
repetitions, channel montage.

## The simulated subject

`acquisition/simulator.py` is what makes the whole thing runnable without
hardware.  It generates 1/f background EEG with an alpha rhythm, a common-mode
component shared by all electrodes and occasional eye blinks, and it watches
the buffer for flash events: when a flashed group contains the attended symbol
(announced by the stimulus client as `simulation.target`) it adds a P3b —
centro-parietal, peaking near 320 ms, with trial-to-trial amplitude and latency
jitter.  Every flash also evokes a small visual response, so the classifier has
to find the target/non-target difference rather than "flash versus nothing".

`--erp-amplitude` and `--noise-amplitude` set the difficulty in microvolts; the
defaults (8 µV P300, 10 µV background) give single-flash AUCs around 0.75–0.8,
which is what a decent real P300 session looks like.

## Running an experiment faster than real time

Timing comes from a clock object rather than `time.sleep`, and `--speed N`
compresses experiment time by N.  Because the data are indexed by samples, a
run at `--speed 20` produces the same epochs as a real-time run, which is how
the end-to-end test spells six letters in five seconds.  During an accelerated
run the stimulus paces itself on the buffer's sample counter
(`clock.BufferClock`) so that two flashes can never land on the same sample.

## Tests

```bash
python -m unittest discover -s tests           # 62 tests, about 30 s
xvfb-run python -m unittest tests.test_gui     # the tk parts, headless
```

They cover the wire protocol, the server (including ring-buffer wrap-around and
blocking waits), pre-processing, the classifier, epoching, the simulator's ERP,
the LSL bridge (skipped without pylsl), the tk widgets (skipped without a
display), and a full calibrate → train → spell experiment that asserts the
classifier beats chance and that the speller gets the letters right.

`tests/test_interop.py` drives this server with buffer_bci's own
`dataAcq/buffer/python/FieldTrip.py` client, so the pure-python buffer stays
usable from the matlab, java and C sides of the project.

## Layout

```
pyspeller/
  buffer/        protocol.py, server.py, client.py   the fieldtrip buffer, in python
  acquisition/   simulator.py, lsl_bridge.py, lsl_outlet.py
  signalproc/    preproc.py, epochs.py, classifier.py
  speller/       matrix.py, stimulus.py, sigproc.py, render.py
  gui/           control_panel.py
  clock.py, config.py, experiment.py, cli.py
```

## Limitations

* The buffer keeps samples in memory only (a ring buffer); there is no
  save-to-disk client like `dataAcq/buffer/java/BufferSaver`.
* Feedback is epoch-based: a letter is decided after a fixed number of
  repetitions, with no dynamic stopping and no language model.
* The classifier is retrained from scratch per session; there is no online
  adaptation or cross-session transfer.
* The tk renderer is fine for a 3×3 or 6×6 grid at 150 ms ISI, but it is not a
  frame-locked stimulus engine — for sub-frame timing accuracy drive the
  hardware trigger of the amplifier instead.
