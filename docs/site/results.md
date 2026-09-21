---
title: Reading the results
description: What the training window is telling you, what the numbers mean, and how to get at the data afterwards.
kicker: 07 · Going deeper
---

## The training window

<figure>
<img class="shadow" src="assets/img/training-view.png" alt="Training result window with AUC headline, ERP panel, discriminability map and confusion matrix">
<figcaption>Four views of the same calibration data. buffer_bci draws the equivalent plots in MATLAB after <code>train_erp_clsfr</code>; this is the same report for the python speller.</figcaption>
</figure>

### The headline: AUC

**AUC** — the area under the ROC curve — is the probability that a randomly
chosen target flash gets a higher score than a randomly chosen non-target one.

| Value | Meaning |
| --- | --- |
| 0.5 | the classifier cannot tell them apart at all |
| 0.65 | weak but real; usable with many repetitions |
| 0.75–0.85 | a good P300 session |
| above 0.9 | excellent — or you are looking at the simulator being generous |

It is **cross-validated**: the data is split into five parts, and each part is
scored by a classifier trained on the other four. That matters. A classifier
scored on the data it was fitted to will look far better than it is —
especially here, where there are more features (channels × time points) than
epochs.

Accuracy, the number beside it, is the same idea in a blunter form: the
proportion of single flashes put in the right class. It looks low (0.70 is
normal) because two flashes in twelve are targets; AUC is the number to trust.

### The class averages

The target trace should have a positive bump 250–400 ms after the flash, largest
at Cz and Pz. If both traces lie on top of each other, the participant was not
attending, the cue was not visible, or the flashes are not reaching the
classifier — check the event log.

These are drawn **after pre-processing**, so they are referenced, filtered and
downsampled: the amplitudes are smaller than the raw ERP you saw in
[the paradigm page](paradigm.html), because the common average reference removes
what every channel shares.

### Where the classes differ

The heat map is the AUC of each channel and time point *on its own*. It answers
a different question from the classifier: not "can we decide?" but "where is
there anything to decide with?"

A healthy map has a warm patch over the centro-parietal channels between about
250 and 450 ms. A uniformly pale map means no signal — no amount of classifier
tuning will save that session.

### The confusion matrix

Read it a row at a time: of the flashes that really were targets, how many did
the classifier call targets? A P300 classifier typically misses a lot of single
targets (rows like 43 % correct) and still spells perfectly, because twelve
repetitions are averaged before a decision. This is why single-flash accuracy is
a poor guide and letter accuracy is what you report.

## What is written to disk

With `--save` (or `pyspeller save`), a session directory looks like this:

```
~/output/<experiment>/<subject>/<date>/<time>/raw_buffer/
├── header          binary: channel count, sample rate, sample type, labels
├── header.txt      the same in ascii, readable
├── samples         the raw EEG, channels fastest
├── events          every flash, cue, prediction and correction
├── calibration_epochs.npz   the cut, labelled epochs
├── classifier.pkl           the trained classifier
└── training_summary.json    the numbers behind the window above
```

The first four files are the **FieldTrip offline-buffer format**, which is what
buffer_bci writes too — so these recordings open in its MATLAB tools
(`matlab/offline/read_buffer_offline_data.m`) and can be replayed into a live
buffer with `matlab/dataAcq/buffer_fileproxy.m`, as if the participant were
still in the chair.

## Getting at it in python

```
from pyspeller.acquisition.saver import load_session, load_epochs

header, samples, events = load_session(
    '~/output/speller/S01/260921/1503/raw_buffer')

print(header)                 # channels, rate, how many samples
print(samples.shape)          # (n_samples, n_channels), microvolts

spelled = [e.value for e in events if e.type == 'classifier.prediction']
cues    = [e.value for e in events if e.type == 'simulation.target']

epochs, labels, meta = load_epochs('.../calibration_epochs.npz')
print(epochs.shape)           # (n_epochs, n_channels, n_samples)
target = epochs[labels == 1].mean(axis=0)
```

Everything the online system did, you can now redo offline — with a different
filter, a different classifier, a different epoch length — on exactly the data
the participant produced.

## The notebook

[`docs/pyspeller_tutorial.ipynb`](https://github.com/berdakh/pyspeller/blob/main/docs/pyspeller_tutorial.ipynb)
runs a whole session from python and plots everything on this page: the raw
traces, the class averages, the classifier's weights, the decoded letters, and
how to load a recording back. It runs against the simulator in about 25 seconds:

```
pip install matplotlib jupyter
jupyter notebook docs/pyspeller_tutorial.ipynb
```

<div class="do">
<span class="block-title">The measurement that matters</span>
Letter accuracy — how many cued letters came out right — is what you report for
a session, together with the number of repetitions it took and the resulting
letters per minute. AUC explains <em>why</em> the accuracy is what it is; it is
not a result on its own.
</div>
