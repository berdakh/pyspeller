---
title: Set up your computer
description: Python, three packages, one clone, one test run. Fifteen minutes on any operating system.
kicker: 04 · Getting running
---

## 1. Python

You need **python 3.8 or newer**. Check what you have:

```
python --version
```

On many Linux and macOS systems the command is `python3` instead.

If that fails or shows something older than 3.8:

- **Windows** — install from [python.org](https://www.python.org/downloads/)
  and tick *Add python.exe to PATH* on the first screen of the installer.
- **macOS** — `brew install python` if you have Homebrew, or the installer from
  python.org.
- **Linux** — `sudo apt install python3 python3-pip python3-tk` on Debian and
  Ubuntu; your distribution's equivalent elsewhere.

<div class="warn">
<span class="block-title">Linux users: don't skip python3-tk</span>
The graphical interface uses <code>tkinter</code>, which ships with python on
Windows and macOS but is a separate package on Linux. Without it, the speller
falls back to a text-only display. Check with
<code>python3 -c "import tkinter"</code> — no output means it is there.
</div>

## 2. A place to work (recommended)

A virtual environment keeps this project's packages away from the rest of your
system. From the folder where you keep your work:

```
python -m venv bci
```

Then activate it — on Windows `bci\Scripts\activate`, on macOS and Linux
`source bci/bin/activate`.

Your prompt now starts with `(bci)`. Everything below happens inside it.

## 3. Get the code

```
git clone https://github.com/berdakh/pyspeller
cd pyspeller
pip install numpy
```

`numpy` is the only thing the framework needs. Two more are worth adding now:

```
pip install pylsl          # to talk to a g.tec amplifier
pip install matplotlib     # for the tutorial notebook's plots
```

<div class="note">
<span class="block-title">No git?</span>
Download the ZIP from the
<a href="https://github.com/berdakh/pyspeller">repository page</a> (green
<em>Code</em> button → <em>Download ZIP</em>) and unpack it. Git is better —
you will be able to pull fixes — but the ZIP works.
</div>

## 4. Prove it works

```
python -m unittest discover -s tests
```

This runs the whole test suite: the network protocol, the buffer, the signal
processing, the classifier, and a complete simulated experiment that calibrates,
trains and spells. It takes about 40 seconds and ends with:

<pre class="out"><code>Ran 142 tests in 40.161s

OK (skipped=26)</code></pre>

Skipped tests are the ones that need something you may not have — a display, or
`pylsl`, or a checkout of buffer_bci. `OK` is what matters.

Then run a whole experiment without any windows:

```
python -m pyspeller demo --speed 10
```

<pre class="out"><code>calibrating on B R A I N ...
[sigproc] gathered 720 epochs (120 target, 600 non-target)
[sigproc] classifier trained: cross-validated AUC 0.773, accuracy 0.72
spelling B C I ...
typed: 'BCI'  (cued: 'BCI')
letter accuracy: 3/3</code></pre>

If you see a number near 0.75 and three letters spelled, your installation is
correct and you understand what the rest of this tutorial will produce.

## When it goes wrong

| Message | Cause and fix |
| --- | --- |
| `python: command not found` | Use `python3`, or re-run the Windows installer with *Add to PATH* ticked |
| `No module named numpy` | `pip install numpy` — and check your virtual environment is active |
| `No module named pyspeller` | Run the commands from inside the cloned `pyspeller` folder |
| `No module named tkinter` | Linux: `sudo apt install python3-tk`. macOS with pyenv: reinstall python with tcl-tk available |
| `no tk display available` in the tests | You are on a machine without a screen (a server, SSH without X). The tests skip those; the rest still run |
| Tests fail with timeouts | A very slow or heavily loaded machine. Run them again on an idle machine before reporting it |
| `pip: command not found` | `python -m pip install ...` instead |

<div class="do">
<span class="block-title">Done when</span>
<code>python -m unittest discover -s tests</code> prints <code>OK</code> and
<code>python -m pyspeller demo --speed 10</code> spells its three letters. Now
go and run the real thing.
</div>
