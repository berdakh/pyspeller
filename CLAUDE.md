# Working in this repository

## Writing style

This applies to everything written for people: slides, tutorial pages, the
manual, READMEs, commit messages and docstrings.

**Titles and headings are plain and descriptive.** A heading names its subject
as a noun phrase: `Background`, `Outline`, `Data acquisition`, `Accuracy versus
number of repetitions`. Never a rhetorical question, a teaser, a slogan, or a
clever turn of phrase — not `The only neuroscience you need today`, not `Where
we are going`, not `144 weak numbers become one letter`.

**The body is declarative and neutral.** State what something is, what it does
and what it costs. No marketing verbs (*buys you*, *payoff*, *the biggest win*,
*worth it*), no superlatives, no exhortation, no exclamation marks. Where
something is a trade-off, give both sides plainly: the advantages, then the
costs.

**Prefer numbers and names to adjectives.** "12 repetitions of 12 groups, 150 ms
apart, about 22 seconds per letter" rather than "quite slow". Quote the actual
parameter names from the code.

**Define a term before using it.** Anything a beginner would not know — ion,
dipole, impedance, common-mode, AUC, shrinkage — is explained in plain words at
its first appearance, and only then used freely. Analogies are welcome in
tutorial prose; on slides, keep them short.

**Spelling is British** (randomised, minimise, analyse, metre), and the
technical vocabulary follows the code.

## Slides

- Labelled boxes carry neutral labels: *Note*, *Summary*, *Definition*,
  *Example*, *Costs*, *Class imbalance*. Not *The catch*, not *The price*.
- An outline slide lists the sections; it carries no timings. Learning
  objectives belong next to it, phrased as "after this lecture you should be
  able to…".
- Every slide has a figure, a table, a code block or a structured list — not
  plain paragraphs, and not a title with bullets alone.
- Figure captions are one plain sentence saying what is shown.
- Speaker notes are written for the lecturer: a suggested duration, what to say,
  what to ask the class, what to put on the board, and what to skip if time runs
  short. Notes may be more conversational than the slides.
- The deck is built by `docs/lecture/build_slides.js`; edit that, not the
  `.pptx`.

## Code and commits

- `signalproc/` is numpy only — no scipy, sklearn or deep learning frameworks —
  so that every step can be read and modified by a student.
- Tests use the simulator and compressed experiment time; a new feature comes
  with a test that needs no hardware.
- Commit messages describe what changed and why, in the same plain register:
  no sales language, no emoji.
