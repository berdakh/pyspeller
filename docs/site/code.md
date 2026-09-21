---
title: Under the hood
description: Every module in a paragraph, the pipeline in code, and the five changes you are most likely to want to make.
kicker: 09 · Going deeper
---

The whole framework is about 3 000 lines of python with one dependency. You can
read it in an afternoon, and you should: it is the best way to understand what a
BCI actually does.

## The map

```
pyspeller/
├── buffer/
│   ├── protocol.py     the FieldTrip wire format: headers, events, samples
│   ├── server.py       the data/event server: a sample ring and an event list
│   └── client.py       everything else uses this to talk to it
├── acquisition/
│   ├── simulator.py    a fake participant: 1/f EEG, alpha, blinks, and a P300
│   ├── lsl_bridge.py   a real amplifier, over Lab Streaming Layer
│   ├── lsl_outlet.py   the reverse, for testing the LSL path
│   └── saver.py        writes samples and events to disk as they arrive
├── signalproc/
│   ├── preproc.py      detrend, reference, band-pass, downsample, outliers
│   ├── epochs.py       turns events plus samples into labelled epochs
│   └── classifier.py   shrinkage LDA, cross-validation, discriminability
├── speller/
│   ├── matrix.py       the grid, the flash sequences, the row/column decoding
│   ├── stimulus.py     the experiment itself: cue, flash, pause, stop
│   ├── sigproc.py      the online client: gather, train, score, decide
│   ├── render.py       how the matrix is drawn (tk, terminal, headless)
│   ├── text.py         what a decoded symbol does to the typed text
│   └── messages.py     the on-screen wording, per language
├── gui/
│   ├── launcher.py     the start screen
│   ├── control_panel.py the operator's window
│   └── training_view.py what training found
├── clock.py            experiment time, and how to compress it
├── config.py           every parameter of the experiment, in one dataclass
├── experiment.py       all the clients in one process (used by the tests)
└── cli.py              python -m pyspeller <command>
```

## The pipeline, in code

This is the entire signal path, with the file each step lives in:

```
raw epoch                         [channels x samples], 600 ms after a flash
  → preproc.detrend               remove drift within the epoch
  → preproc.car                   common average reference
  → preproc.spectral_filter       trapezoidal band-pass, 0.5–10 Hz
  → preproc.subsample             down to 16 Hz: ~10 points per channel
  → flatten                       one feature vector per epoch
  → ShrinkageLDA.decision_function   one number per flash
  → average per row / per column  speller/sigproc.py
  → matrix.decode                 best row × best column = the letter
```

Two design choices are worth understanding, because they are where most ERP
pipelines differ:

- **Shrinkage.** With 8 channels × 10 time points there are 80 features and
  perhaps 600 epochs. The covariance matrix of 80 features estimated from 600
  samples is noisy, so it is shrunk towards a scaled identity
  (`regularisation=0.5`). Without it, cross-validated AUC collapses.
- **A trapezoidal filter in the frequency domain** rather than an IIR filter:
  zero phase distortion, no dependency on scipy, and the same four-corner
  specification (`0.1 0.5 10 12`) that buffer_bci's MATLAB code uses.

## Changes you are likely to want

### A new symbol layout

`config.py` holds them as tuples of rows. Add yours, register it, and give it
words that it can spell:

```
SYMBOLS_MINE = (('A', 'B', 'C'),
                ('D', 'E', 'F'))
LAYOUTS['mine'] = SYMBOLS_MINE
DEFAULT_WORDS['mine'] = (tuple('ABCDEF'), tuple('FACE'))
```

`python -m pyspeller demo --layout mine` now works. The flash sequence, the
decoding and the display all derive from the shape of the tuple.

### A new language for the instructions

`speller/messages.py` is one dictionary per language, with the same keys.
Copy `ENGLISH`, translate the values, add it to `LANGUAGES`, and select it with
`--language`. A test checks that every language defines every key.

### A different classifier

`signalproc/classifier.py` defines `ShrinkageLDA` with `fit` and
`decision_function`, and `ERPClassifier` wraps it with the pre-processing.
Anything with those two methods can be dropped in — logistic regression, a
support vector machine, a shrinkage-free LDA for comparison. The exercises ask
you to do exactly that.

### A different amplifier

If it has an LSL connector, nothing changes: `pyspeller lsl --name ...`. If it
does not, write a client that reads your device and calls `put_data` — that is
what `simulator.py` and `lsl_bridge.py` both do, in about 40 lines each.

### Your own online analysis

Write a client. Connect, read events, take the samples you want, publish your
own events. Fifteen lines is enough to log every prediction to a CSV, or to make
a second display that shows something you care about:

```
from pyspeller.buffer import BufferClient

client = BufferClient('localhost', 1972).connect()
client.wait_for_header()
client.reset_event_cursor()
while True:
    for event in client.new_events(timeout_ms=1000):
        if event.type == 'classifier.prediction':
            print('the speller chose', event.value)
```

## The tests are documentation too

`tests/` is 142 tests and the most precise description of how the system
behaves. If you want to know what happens when a block is stopped mid-flash, or
how an epoch is cut, or what the buffer does when its ring wraps, the test that
pins that behaviour down is easier to read than the code.

```
python -m unittest discover -s tests -v
```

Every change you make should leave that green, and every behaviour you add
should get a test. That is how this codebase stays small enough to read.
