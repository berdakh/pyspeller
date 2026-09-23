# Lecture slides

A 75-minute lecture on the technical side of pyspeller: the client–server
architecture, the stimulus and analysis clients, and how a letter is decoded.
It assumes no prior knowledge of BCI beyond one slide of background, and it is
meant to be given alongside a live run of the simulator.

| File | What it is |
| --- | --- |
| `pyspeller-lecture.pptx` | the deck, with speaker notes on every slide |
| `pyspeller-lecture.pdf` | the same slides for projecting without PowerPoint (no notes) |
| `build_slides.js` | the generator that produces the `.pptx` |
| `render_figures.py` | redraws the five SVG diagrams the deck uses as PNG |

## Contents

1. **Introduction** — background on the P300 and the row/column matrix; outline
   and learning objectives.
2. **System architecture** — design requirements, the buffer and its clients,
   the protocol, and sample-indexed event timing.
3. **System components** — the packages, the three data sources, stimulus
   presentation, phases and control events.
4. **Signal processing** — epoch extraction, preprocessing, shrinkage LDA,
   evaluation, evidence accumulation, and accuracy against repetitions.
5. **Implementation notes** — data storage, the user interface, testing.
6. **Demonstration and extensions** — a live run, then project topics.

The speaker notes carry a suggested time for each slide (they add up to 75
minutes), what to put on the board, and questions to ask the class. Slide 3's
notes list which slides to compress if the lecture runs late.

## Rebuilding

```sh
npm install pptxgenjs
node build_slides.js
```

The figures come from `../assets/img` — the same diagrams and screenshots as
the tutorial — so a change there flows into the deck on the next build. The
five SVG-only diagrams are kept as PNG in `figures/`; regenerate them with
`python3 render_figures.py` if you edit the SVGs.

To refresh the PDF:

```sh
soffice --headless --convert-to pdf pyspeller-lecture.pptx
```
