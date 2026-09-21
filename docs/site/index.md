---
title: Build a working brain–computer interface
description: A P300 speller you can run this afternoon — on a simulated brain first, then on a real one with a g.tec amplifier.
kicker: Start here
---

By the end of this tutorial you will have typed a word on a screen using nothing
but attention: no keyboard, no mouse, no muscles. You will also know why it
works, what every piece of the software does, and how to run a session with a
real person and a real amplifier.

<figure>
<img class="shadow" src="assets/img/panel-and-speller.png" alt="The control panel on the left and the speller matrix on the right">
<figcaption>What you are building: the operator's panel (left) with the live EEG, and the participant's speller (right) mid-flash, with the letters typed so far in the field at the top.</figcaption>
</figure>

## Ten minutes to your first experiment

No hardware needed. The software comes with a simulated participant whose
brain responds the way a real one does.

```
git clone https://github.com/berdakh/pyspeller
cd pyspeller
pip install numpy
python -m pyspeller run
```

Choose **simulated subject**, press **Start session**, then **Calibrate**,
**Train classifier**, **Feedback** — and watch letters appear. If anything goes
wrong, [Set up your computer](install.html) has the fix.

<div class="note">
<span class="block-title">Why start with a simulator?</span>
Because every mistake you make with a real participant costs twenty minutes of
their time and a wash of their hair. Learn the procedure on the simulator until
it is boring, then do it for real.
</div>

## The path

Work through these in order. The whole thing is a long afternoon; the first two
hours get you running.

<div class="cards">
<a class="card" href="paradigm.html"><span class="card-num">01 · 25 min</span><h3>How a P300 speller works</h3><p>EEG, evoked responses, and why flashing letters lets a computer read your intention.</p></a>
<a class="card" href="sensors.html"><span class="card-num">02 · 30 min</span><h3>Sensors, materials &amp; amplifiers</h3><p>How metal on a scalp picks up brain activity, what gold and silver–silver chloride are for, and why every channel is a subtraction.</p></a>
<a class="card" href="architecture.html"><span class="card-num">03 · 20 min</span><h3>The client–server design</h3><p>One buffer, several small programs. Why this is how real BCI systems are built.</p></a>
<a class="card" href="install.html"><span class="card-num">04 · 15 min</span><h3>Set up your computer</h3><p>Python, the packages, the tests. Windows, macOS and Linux.</p></a>
<a class="card" href="first-run.html"><span class="card-num">05 · 30 min</span><h3>Your first experiment</h3><p>Run a whole session against the simulator and read what comes out.</p></a>
<a class="card" href="gtec.html"><span class="card-num">06 · 45 min</span><h3>The g.tec amplifier</h3><p>Drivers, g.NEEDaccess, Lab Streaming Layer, and getting real EEG into the buffer.</p></a>
<a class="card" href="session.html"><span class="card-num">07 · 45 min</span><h3>Running a real session</h3><p>Consent, the cap, impedances, what to say, and what to do when it goes wrong.</p></a>
<a class="card" href="results.html"><span class="card-num">08 · 25 min</span><h3>Reading the results</h3><p>AUC, the confusion matrix, the ERP plots, and the files on disk.</p></a>
<a class="card" href="code.html"><span class="card-num">09 · 30 min</span><h3>Under the hood</h3><p>Every module in a page, and how to change the parts you care about.</p></a>
<a class="card" href="exercises.html"><span class="card-num">10</span><h3>Exercises</h3><p>Seven pieces of work that prove you can actually run and reason about this.</p></a>
<a class="card" href="reference.html"><span class="card-num">11</span><h3>Troubleshooting &amp; glossary</h3><p>Every error message we know about, and every term defined.</p></a>
</div>

## What you need

| For the simulator | For a real session |
| --- | --- |
| Any computer with python 3.8 or newer | A g.tec amplifier (g.USBamp, g.HIamp or g.Nautilus) |
| `numpy` | An EEG cap, electrodes, gel, syringes |
| A screen | `pylsl`, and g.tec's driver and software on the recording machine |
| 10 minutes | A willing participant, consent, and about an hour |

## Where this comes from

This software is a python rewrite of the ideas in
[buffer_bci](https://github.com/berdakh/buffer_bci), a framework built at the
Donders Institute for teaching and running BCI experiments. buffer_bci is
mostly MATLAB with a C/Java data server; **pyspeller** is the same architecture
with every part written in python, so that you can read all of it in an
afternoon.

The two speak the same protocol on the wire, so a recording made here opens in
buffer_bci's MATLAB analysis tools, and its MATLAB clients can talk to this
server. Where buffer_bci's own tutorial material is worth reading, this site
points at it.

<div class="do">
<span class="block-title">If you only have one hour</span>
Read <a href="paradigm.html">How a P300 speller works</a>, then do
<a href="install.html">Set up your computer</a> and
<a href="first-run.html">Your first experiment</a>. That is enough to run the
simulated experiment and understand what you are seeing.
</div>

<div class="meta" style="margin-top:34px">
This site lives in <code>docs/</code> in the repository: the pages are markdown
in <code>docs/site/</code>, and <code>python docs/build_site.py</code> (needs
<code>pip install markdown</code>) regenerates the html. Corrections are
welcome as pull requests.
</div>
