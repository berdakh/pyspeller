---
title: Sensors, materials and amplifiers
description: How a piece of metal on your scalp turns brain activity into a number — the electrochemistry, the materials, and why every channel is a subtraction.
kicker: 02 · Orientation
---

A student asked the question this page exists to answer: *how does the
electricity actually get from the brain into the computer?* The answer runs
through electrochemistry, metallurgy and amplifier design, and knowing it is
what separates someone who can run a session from someone who can fix one.

## 1. From neurons to a puddle of gel

A single neuron produces far too little current to measure from outside the
head. What EEG sees is the summed **post-synaptic potentials** of tens of
thousands of pyramidal cells in the cortex — cells that are lined up
perpendicular to the cortical surface, so their tiny currents add rather than
cancel. Each patch acts like a small current source and sink: an **electric
dipole**.

Current from those dipoles spreads through everything between the cortex and
the electrode — cerebrospinal fluid, skull, scalp. This is **volume
conduction**, and two facts about it shape everything else:

- **The skull is a poor conductor**, so the pattern is smeared over
  centimetres. Scalp EEG cannot see a single gyrus; it sees a region.
- **What arrives is tiny**: 10–100 µV of ongoing EEG, and the P300 you are
  hunting is about 5 µV. Mains hum in an unshielded room can be far larger, and
  a blink is 10–20 times larger.

In the tissue and in the gel, the current is carried by **ions** — Na⁺, K⁺,
Cl⁻ moving. In the wire to the amplifier it is carried by **electrons**. The
electrode is the place where one becomes the other.

## 2. The electrode is a chemical reaction

<figure>
<img src="assets/img/electrode-interface.svg" alt="Cross-section of an electrode on the scalp with a magnified view of the electrical double layer and the silver–silver chloride reaction">
<figcaption>Left: what the electrode sits on. Right: the interface where ionic current becomes electronic current.</figcaption>
</figure>

Put a metal in an electrolyte and charge immediately rearranges at the
boundary: metal ions dissolve or deposit until an equilibrium is reached. The
result is an **electrical double layer** — a nanometre-thin sandwich of charge
— and a voltage across it, the **half-cell potential**. Every metal–electrolyte
pair has its own: silver–silver chloride sits at about **+0.22 V** relative to
the standard hydrogen electrode.

That is *a thousand times larger* than the EEG. It does not swamp the recording
for one reason: each channel is the **difference** between two electrodes, and
if both are the same material in the same electrolyte, their half-cell
potentials nearly cancel. "Nearly" is what you spend your session fighting —
the residue is the slow drift you see when an electrode dries out.

### Polarizable and non-polarizable

This is the single most useful idea about electrode materials.

**Non-polarizable (reversible)** — charge crosses the interface freely, through
a reversible chemical reaction. For silver–silver chloride:

```
Ag + Cl⁻  ⇌  AgCl + e⁻
```

Current in either direction just runs the reaction one way or the other. The
interface behaves like a **resistor**: it passes low frequencies and DC, its
potential is stable, and moving the electrode slightly does not produce a large
voltage step.

**Polarizable** — no charge crosses; it accumulates on both sides like a
**capacitor**. Gold, platinum and stainless steel are close to this. A capacitor
blocks DC and passes high frequencies, so these electrodes are fine for alpha
and beta rhythms but drift at very low frequencies, and any mechanical
disturbance changes the capacitance and produces an artefact.

Real electrodes are somewhere between the two: a resistance and a capacitance in
parallel, in series with the resistance of the gel and the skin.

<div class="note">
<span class="block-title">Why this matters for a P300 speller</span>
Your signal lives between roughly 0.5 and 10 Hz — the low end, where polarizable
electrodes drift and non-polarizable ones do not. That is why silver–silver
chloride is the default for ERP work, and why an ERP lab will put up with the
gel.
</div>

## 3. The materials, and why each is used

| Material | Behaviour | Where you meet it | Trade-off |
| --- | --- | --- | --- |
| **Sintered Ag/AgCl** (silver and silver chloride powder pressed into a pellet) | Non-polarizable | Research caps, ERP labs, the reference standard | Best low-frequency stability; the AgCl is throughout the pellet, so it survives cleaning. Most expensive |
| **Chloridized silver** (a thin AgCl layer grown on silver) | Non-polarizable while the layer lasts | Cheaper caps, home-made electrodes | Same physics, but the layer wears off with scrubbing and has to be re-chloridized |
| **Gold** (usually gold-plated silver or copper) | Largely polarizable | Clinical cups, dry pin electrodes, long-term monitoring | Inert, biocompatible, easy to clean, no allergy issues. Drifts below ~1 Hz; fine for oscillations, weaker for slow ERPs |
| **Platinum / platinum–iridium** | Polarizable, very inert | Implanted and intracranial electrodes, some research surface electrodes | Chemically superb and MRI-compatible-ish; expensive, and polarizes |
| **Tin (Sn)** | Between the two | Older and budget caps | Cheap and workable; noisier and driftier than Ag/AgCl |
| **Stainless steel** | Polarizable | Dry electrodes, rugged field systems | Tough and cheap; poor at low frequencies, more 1/f noise |
| **Conductive polymer / carbon / silver-loaded rubber** | Varies | MRI-compatible caps, textile electrodes | Chosen for safety inside a scanner (no induced heating), not for signal quality |
| **Sponge / saline ("water-based")** | Ag/AgCl behind a saline sponge | Fast-setup caps | No gel to wash out; dries out over an hour and drifts as it does |

<div class="warn">
<span class="block-title">Do not mix metals</span>
Two different metals in the same electrolyte form a battery: their half-cell
potentials differ by tens or hundreds of millivolts, and that difference sits
across your amplifier's input and drifts with temperature. Use one material for
the whole montage — <em>including</em> the reference and ground.
</div>

## 4. The sensors themselves

<figure>
<img src="assets/img/electrode-types.svg" alt="Six electrode types drawn in cross-section: wet cup, gold cup, active electrode, dry pins, capacitive, and subdermal needle">
<figcaption>The families you will meet. For a teaching BCI lab it is nearly always one of the first four.</figcaption>
</figure>

**Wet cup or ring electrodes.** A small Ag/AgCl cup held in a cap, filled with
conductive gel through a hole in the top. The workhorse: lowest noise, lowest
drift, and the reason ERP labs smell faintly of electrolyte.

**Gold cups.** Glued to the scalp with conductive paste in clinical EEG, or
mounted in caps. Durable and easy to clean; a little more drift.

**Active electrodes.** A wet or dry electrode with a tiny amplifier *on the
electrode itself*. The weak, high-impedance signal is buffered before it travels
down a metre of cable, so cable movement and mains pickup matter far less and
the skin can be prepared less aggressively. g.tec's g.LADYbird electrodes work
this way; so do the active systems from other manufacturers.

**Dry electrodes.** Gold-plated pins or fingers that push through the hair to
touch the scalp, with no gel at all — g.tec's g.SAHARA is the example you are
most likely to meet on a g.Nautilus. Setup drops from twenty minutes to two. The
price is impedance in the tens or hundreds of kΩ, more drift, and much greater
sensitivity to movement. They work for a P300 speller; they work *better* after
the participant has stopped fidgeting.

**Capacitive / contactless electrodes.** A metal plate separated from the skin
by an insulator — even hair or a thin fabric. No chemistry at all: the skin and
the plate are the two plates of a capacitor. They demand extremely high input
impedance and careful shielding, and are still mostly a research topic.

**Subdermal needles** exist for intensive care and intra-operative monitoring.
They are not for student BCI work, and you should not be the person inserting
them.

## 5. Skin, gel and impedance

The metal is rarely the problem. The **stratum corneum** — the outer layer of
dead, dry skin cells — is where nearly all the resistance lives. That is what
the preparation ritual is about:

- **Abrasion** with a blunt needle or gel with a mild abrasive removes some of
  that dead layer.
- **Conductive gel** is an electrolyte, usually a chloride salt in a viscous
  base. It provides the Cl⁻ ions the Ag/AgCl reaction needs and fills the gap
  between a rigid cup and an irregular scalp.

**Electrode impedance** is what you measure when you press *impedance check* in
the recording software: the amplifier passes a tiny alternating current through
the electrode and measures the resulting voltage. Typical values:

| Setup | Impedance |
| --- | --- |
| Gel electrode, well prepared | 1–5 kΩ |
| Gel electrode, lazy preparation | 10–50 kΩ |
| Dry pins on clean scalp | 50 kΩ – 1 MΩ |
| Electrode that has come off | open circuit, often shown as ∞ |

Modern amplifiers have input impedances of tens of megaohms to gigaohms, so a
20 kΩ electrode loses almost none of the signal by simple division. **Why do we
still chase low impedances?** Two reasons, and both are about noise rather than
signal:

1. **Thermal noise.** Any resistance generates Johnson noise proportional to
   √R. At 5 kΩ it is negligible next to the EEG; at 1 MΩ it is not.
2. **Mismatch turns common-mode into differential.** Mains hum reaches both
   inputs of the amplifier equally — but only if both paths are equal. If one
   electrode is at 5 kΩ and another at 200 kΩ, the hum arrives with different
   amplitudes, the amplifier sees a genuine difference, and it cannot cancel it.
   **Matched impedances matter as much as low ones.**

Two failure modes to recognise on the scope: **bridging**, where gel spreads
between neighbouring electrodes and makes their traces suspiciously identical,
and **drying**, where impedance climbs over an hour and slow drift creeps in.

## 6. How a number is actually computed

<figure>
<img src="assets/img/differential-amp.svg" alt="Diagram of a head with an electrode, a reference and a ground feeding a differential amplifier, with hum cancelling in the output">
<figcaption>Every EEG channel is the output of a differential amplifier: the signal at one electrode minus the signal at the reference, amplified.</figcaption>
</figure>

A **differential amplifier** (in practice an *instrumentation amplifier*) has two
inputs and amplifies only their difference:

```
output = gain × ( V(+) − V(−) )
```

Whatever is identical on both inputs — the **common-mode** signal — is
suppressed. How well is the **common-mode rejection ratio**, CMRR, quoted in
decibels; a good EEG amplifier is above 100 dB, meaning common-mode signals come
out at least 100 000 times smaller.

This is what makes EEG possible at all. A participant sitting in a room is an
antenna: their whole body floats tens of millivolts of 50 Hz mains hum. That hum
is the same at Pz and at the mastoid, so it cancels. The 5 µV P300 is not the
same at both, so it survives.

After the amplifier, a **24-bit analogue-to-digital converter** samples the
voltage — 256 or 512 times a second in a typical g.tec setup — with an input
range of a few hundred millivolts, wide enough to accommodate electrode offsets
without clipping. The digital numbers that reach pyspeller through Lab Streaming
Layer are already converted to **microvolts**.

## 7. Reference and ground: the question everyone asks

They are different things and they are not interchangeable.

**The reference is one of the two inputs of every channel.** It is a *signal*
electrode, on the participant's head, that every channel is compared against.
There is no "voltage at Pz" — only "Pz minus wherever the reference is". Choose
a quiet, stable site: a mastoid, an earlobe, the nose tip, sometimes Cz.

**The ground is the amplifier's zero.** It gives the participant's body a
defined potential relative to the amplifier's circuitry so the inputs stay
inside their working range, and it carries the bias currents the input stage
needs. It is not part of any channel's arithmetic. In modern amplifiers it is
often **driven**: the measured common-mode is inverted and fed back into the
body (the idea comes from ECG, where it is called the *driven right leg*), which
actively pushes the common-mode toward zero and improves hum rejection well
beyond what CMRR alone gives.

| | Reference | Ground |
| --- | --- | --- |
| Purpose | the second input of every channel | sets the body's potential, provides bias return |
| Appears in the data? | yes — subtracted from every channel | no |
| Typical position | mastoid, earlobe, nose | AFz, forehead, neck, collarbone |
| If it comes loose | every channel goes noisy at once | everything saturates or hums badly |
| Can you change it afterwards? | yes, arithmetically | no |

<div class="stop">
<span class="block-title">Ground is not "earth"</span>
The ground electrode must never be connected to mains earth. Medical and
research amplifiers isolate the participant from the mains — optically or by
radio — precisely so that no current can flow through a person if something
fails. That is also why you must not connect a participant to a non-isolated,
mains-powered device.
</div>

### Changing the reference after the fact

Because every channel shares one reference, you can compute any other reference
offline with arithmetic alone:

```
recorded:      V_a = A(a) − A(ref)        V_b = A(b) − A(ref)
bipolar:       V_a − V_b = A(a) − A(b)    the reference cancels
average (CAR): V_a − mean(all V)          removes what every channel shares
Laplacian:     V_a − mean(V of neighbours)
```

<figure>
<img src="assets/img/montages.svg" alt="Four heads showing mastoid, linked mastoid, common average and Laplacian references with their formulas">
<figcaption>Four ways of looking at the same recording. None is "correct" — each answers a different question.</figcaption>
</figure>

This speller uses the **common average reference**: `preproc.car` subtracts the
mean across channels from each channel, before filtering. With eight or more
reasonably spread electrodes, that removes reference drift, much of the mains
hum and distant muscle activity, while leaving the centro-parietal P300 intact.
A **Laplacian** would be a poor choice here: it is deliberately local, and it
would subtract away a response that is broad by nature.

<div class="do">
<span class="block-title">Try it on your own recording</span>
Load a saved session (<a href="results.html">Reading the results</a>), compute
the ERP with no re-referencing, with a mastoid channel subtracted, and with a
common average. The P300 changes amplitude and even sign at some electrodes.
Nothing about the brain changed — only what you subtracted.
</div>

## 8. What goes wrong, seen from the sensor side

| On the scope | Usually means |
| --- | --- |
| One channel much larger than its neighbours | that electrode has poor contact, or has come off |
| A sudden step, then a slow return ("electrode pop") | the double layer was disturbed — the electrode moved, or an air bubble in the gel |
| Slow wandering over seconds, worse late in the session | drying gel, or sweat changing the skin's own potential |
| Everything humming at 50 or 60 Hz | reference or ground loose, mismatched impedances, or a power supply too near the cap |
| Two channels suspiciously identical | gel bridging between them |
| All channels dead flat | amplifier not acquiring, or the cap is unplugged |
| Fast, spiky activity over the temples | jaw and neck muscle, not brain |

## 9. What this means when you are capping up

- Prepare the **reference and ground as carefully as any channel** — they are in
  every number you record.
- Use **one electrode material** throughout.
- Aim for **low *and* matched** impedances, and write them down.
- Gel enough to conduct, **not enough to bridge**.
- With dry electrodes, expect higher impedances and give the participant a
  minute to settle before recording.
- Re-check impedances after 30–40 minutes; gel dries.

[Running a real session](session.html) turns this into a procedure, and
[the g.tec page](gtec.html) covers the specific hardware.

## Further reading

- Nunez & Srinivasan, *Electric Fields of the Brain* — the standard reference on
  volume conduction and what the scalp can and cannot see.
- Webster (ed.), *Medical Instrumentation: Application and Design* — the
  electrode–electrolyte interface, half-cell potentials, and amplifier design,
  worked through properly.
- Teplan (2002), *Fundamentals of EEG measurement* — a short, readable overview.
- buffer_bci's [EEG BCI tutorial worksheet](https://github.com/berdakh/buffer_bci/blob/master/tutorial/EEGBCITutorial/EEGBCI_worksheet.md)
  — practical exercises on referencing and artefacts with a cap on a real head.
