# Running a P300 speller session — student manual

A step-by-step guide to recording a session with a g.tec amplifier and the
`pyspeller` software. Read it once end to end before your first session with a
participant; practise the whole procedure on the simulator first (§1).

A full session takes about 45 minutes: 20 for capping up, 3 for calibration,
2 for training, the rest for spelling.

> This is research software. It is not a medical device, makes no diagnosis,
> and must only be used with participants who have given informed consent under
> your lab's ethics approval.

---

## 0. What you need

**Hardware**
- a g.tec amplifier (g.USBamp, g.HIamp or g.Nautilus) with its power supply,
  dongle or USB cable
- an EEG cap of the right size, electrodes, abrasive gel and conductive gel,
  syringes, tape measure, alcohol wipes
- the participant's PC screen (the speller) and your operator screen

**Software**
- the g.tec recording software for your amplifier, and its Lab Streaming Layer
  connector (in g.NEEDaccess; check the manual of your model for the exact app)
- python 3.8+ with `numpy` and `pylsl`:

```bash
pip install numpy pylsl
cd buffer_bci/python/pyspeller
python -m unittest discover -s tests     # everything should pass
```

---

## 1. Practise without a participant

Everything below works against a simulated subject, so rehearse the procedure
before anybody is sitting in the chair:

```bash
python -m pyspeller run --save
```

Press **Calibrate**, wait for it to finish, press **Train classifier**, then
**Feedback**. You will see the letters appear in the speller's text field. This
is exactly the sequence you will run with a real participant — only the source
of the data differs.

---

## 2. Prepare the participant

1. Explain the task and what the cap involves; answer questions before you
   start. Get the consent form signed.
2. Measure the head circumference and choose the cap size. Find Cz: halfway
   between nasion and inion, and halfway between the two ear lobes.
3. Put on the cap, then prepare each electrode site: part the hair, abrade
   gently with gel, fill with conductive gel until the impedance drops.
4. Use at least these sites for a P300 speller: **Fz, Cz, Pz, Oz, P3, P4, PO7,
   PO8**. Reference on an earlobe or mastoid, ground at AFz/FPz. More channels
   do not hurt; the classifier uses whatever the amplifier sends.
5. Check impedances in the g.tec software. Aim below 5 kΩ with gel electrodes
   (dry electrodes such as g.SAHARA read much higher — follow the value your
   lab uses for that headset). Re-gel anything that stays high; a single noisy
   electrode costs you accuracy.
6. Seat the participant about 60 cm from the screen, forearms supported, feet
   on the floor. Ask them to find a position they can hold comfortably for
   twenty minutes.

---

## 3. Start the amplifier stream

1. Start the g.tec recording software and configure the amplifier:
   - sample rate 256 or 512 Hz
   - device band-pass around 0.1–30 Hz and the notch at your mains frequency
     (50 Hz in Europe, 60 Hz in the Americas)
2. Start the Lab Streaming Layer connector so the amplifier is published on the
   network, and start streaming.
3. On the analysis PC, check that the stream is visible:

```bash
python -m pyspeller lsl --list
# g.USBamp-UB-2016.03.06   type=EEG   channels=16  rate=256 Hz  host=lab-pc
```

If nothing is listed: the connector is not streaming, or the two machines are
on different networks (LSL discovery does not cross subnets or most VPNs). The
simplest fix is to run both on the same machine or the same lab switch.

---

## 4. Start the software

The easy way — one command, everything in one process:

```bash
python -m pyspeller run --lsl --lsl-name "g.USBamp-UB-2016.03.06" --save \
       --subject S01 --experiment speller
```

Two windows open: the **control panel** on your screen and the **speller** on
the participant's screen. Drag the speller window onto their monitor and
maximise it, so the grid is as large as possible and nothing else is visible.

The explicit way — one component per terminal, which is what you want when the
amplifier and the analysis run on different machines (add `--host` to point the
clients at the machine running the buffer):

```bash
python -m pyspeller buffer                                   # 1. the server
python -m pyspeller lsl --name "g.USBamp-UB-2016.03.06"      # 2. the amplifier
python -m pyspeller save --subject S01 --experiment speller  # 3. recording
python -m pyspeller sigproc --save-dir ~/output/speller/S01  # 4. analysis*
python -m pyspeller speller                                  # 5. the display
python -m pyspeller gui                                      # 6. your panel
```

Start them in that order. Each one waits for the buffer, so nothing breaks if
you are a few seconds late with one of them.

\* the raw recording goes to its own timestamped directory (step 9); the
`--save-dir` given to `sigproc` is where the calibration epochs and the trained
classifier are written.

---

## 5. Check the signal before you record anything

Look at the scope in the control panel for a minute — this is the step students
skip and regret:

| what you ask for | what you should see |
| --- | --- |
| sit still, eyes open | wandering traces of roughly 10–30 µV rms, all channels similar |
| blink a few times | a large, slow deflection, biggest at Fz |
| clench the jaw | a burst of fast, spiky activity — it should stop when they relax |
| close the eyes for 10 s | alpha, a visible ~10 Hz rhythm, strongest at Oz/Pz |

The `signal quality` bars show the rms per channel. A channel that sits far
above the others, or flat at zero, is a bad contact: re-gel it before
continuing. A mains hum on every channel usually means the reference or ground
is loose, or a power supply is too close to the cap.

---

## 6. Calibration (about 3 minutes)

Tell the participant, in these words:

> A letter will be shown to you in green. Look at it, and keep looking at that
> spot. Rows and columns will flash quickly. Count silently, to yourself, each
> time the letter you are looking at flashes — start again at one for each new
> letter. Try not to blink while the flashing is going on; blink in the pauses
> between letters.

Press **Calibrate**. The speller cues five letters (B, R, A, I, N by default)
and flashes each one for about 22 seconds. Watch the scope: if the participant
blinks constantly or moves, stop, give them a break, and start again. Bad
calibration data cannot be fixed later.

---

## 7. Train the classifier (a few seconds)

Press **Train classifier**. The signal processing terminal prints, for example:

```
[sigproc] gathered 720 epochs (120 target, 600 non-target)
[sigproc] classifier trained: cross-validated AUC 0.78, accuracy 0.72
```

**AUC** is how well a single flash can be told apart from the rest:

| AUC | what to do |
| --- | --- |
| above 0.75 | good — go on to spelling |
| 0.65–0.75 | usable; consider more repetitions (`--n-repetitions 15`) |
| below 0.65 | do not spell yet: check impedances, ask about attention and tiredness, then record a second calibration block |

If a channel was dropped as bad, it is named in the same output. One dropped
channel is normal; three means something is wrong with the cap.

---

## 8. Spelling

**Feedback** spells a cued word (BCI by default) and scores it: each letter is
decided after the repetitions are done, shown in green in the grid, and added
to the text field above it. Use this to check the system works before letting
the participant spell freely.

**Free spelling** has no cue: the participant looks at whichever letter they
want and it appears in the text field. This is the real task.

**When a letter comes out wrong**, the participant selects `DEL` in the matrix,
exactly like any other key, and the last letter disappears. You can also press
**⌫ backspace** on the control panel, which does the same thing from your side
and shows up in the event log as `speller.edit DEL`. `_` types a space and the
**clear** button empties the line.

One letter takes about 22 seconds at the default of 12 repetitions. Fewer
repetitions are faster and less accurate: `--n-repetitions 8` for a good
participant, 15 for a difficult one. Give a break every 10 minutes.

---

## 9. Ending the session and the data

Press **Quit** (or Ctrl-C in each terminal), then remove the cap and let the
participant wash their hair. Clean the electrodes and the cap straight away —
dried gel ruins electrodes.

The recording is in
`~/output/<experiment>/<subject>/<date>/<time>/raw_buffer/`:

| file | what it is |
| --- | --- |
| `samples`, `header`, `header.txt` | the raw EEG and its description |
| `events` | every flash, cue, prediction and correction, with sample numbers |
| `calibration_epochs.npz` | the cut, labelled calibration epochs |
| `classifier.pkl` | the classifier that was trained on them |

Copy it off the lab machine and write down in your lab book: participant code,
date, cap size, which channels were bad, the AUC, how many letters were spelled
and how many were right.

To look at it afterwards:

```python
from pyspeller.acquisition.saver import load_session, load_epochs

header, samples, events = load_session('~/output/speller/S01/260921/1503/raw_buffer')
predictions = [e.value for e in events if e.type == 'classifier.prediction']

epochs, labels, meta = load_epochs('.../calibration_epochs.npz')
target_erp = epochs[labels == 1].mean(axis=0)     # channels x samples
```

In matlab the same directory is read by
`matlab/offline/read_buffer_offline_data.m`, and can be replayed into a buffer
with `matlab/dataAcq/buffer_fileproxy.m`.

---

## 10. When something goes wrong

| symptom | likely cause and fix |
| --- | --- |
| `no LSL stream matching name=... type='EEG'` | the g.tec connector is not streaming, or it is on another subnet. Run `python -m pyspeller lsl --list` to see what is actually there. |
| `no header appeared in the buffer` | the buffer is running but no amplifier client is feeding it — start the `lsl` bridge (step 4). |
| the scope is flat | the amplifier is streaming zeros: check that the device is on, the cap is plugged in, and that you started acquisition in the g.tec software. |
| all channels look identical and noisy | reference or ground electrode is loose. |
| flashes happen but no letter ever appears | the signal processing client is not running, or no classifier has been trained — press **Train classifier** first. |
| `the 3x3 speller matrix has no 'Q'` | the word you asked to spell is not in the layout you chose; see `--layout`. |
| accuracy is far worse than the AUC suggested | the participant is looking at the grid but not attending, or is counting the wrong letter. Re-explain the task. |
| accuracy dropped during the session | tiredness, drying gel, or the cap shifted. Take a break, re-check impedances, and if needed re-calibrate. |

---

## Session checklist

Print this and tick it off.

- [ ] consent signed, task explained
- [ ] cap on, impedances checked and written down
- [ ] g.tec software streaming, `pyspeller lsl --list` shows the amplifier
- [ ] recording started (`--save`), path noted in the lab book
- [ ] signal checked: blink, jaw, eyes-closed alpha
- [ ] calibration run, no obvious artefacts
- [ ] classifier trained, AUC noted
- [ ] feedback block run and scored
- [ ] free spelling done
- [ ] data copied off the machine, cap and electrodes cleaned
