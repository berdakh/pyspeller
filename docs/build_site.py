#!/usr/bin/env python3
"""Build the tutorial site: docs/site/*.md  ->  docs/*.html

    pip install markdown
    python docs/build_site.py

The pages are markdown so they can be read and edited on GitHub; this script
wraps them in the shared layout (navigation, previous/next, footer). There is
no Jekyll and no theme: GitHub Pages serves the generated html as it is.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, 'site')

# (file, nav title, section) -- also the order of the site
PAGES = [
    ('index', 'Start here', 'Orientation'),
    ('paradigm', 'How a P300 speller works', 'Orientation'),
    ('sensors', 'Sensors, materials & amplifiers', 'Orientation'),
    ('architecture', 'The client–server design', 'Orientation'),
    ('install', 'Set up your computer', 'Getting running'),
    ('first-run', 'Your first experiment', 'Getting running'),
    ('gtec', 'The g.tec amplifier', 'With hardware'),
    ('session', 'Running a real session', 'With hardware'),
    ('results', 'Reading the results', 'Going deeper'),
    ('code', 'Under the hood', 'Going deeper'),
    ('exercises', 'Exercises', 'Going deeper'),
    ('reference', 'Troubleshooting & glossary', 'Going deeper'),
]

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · pyspeller</title>
<meta name="description" content="{description}">
<link rel="stylesheet" href="assets/css/site.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🧠</text></svg>">
</head>
<body>
<div class="layout">
<aside class="sidebar">
  <a class="brand" href="index.html">py<span>speller</span></a>
  <div class="brand-sub">P300 speller tutorial</div>
  {nav}
  <div class="sidebar-foot">
    <a href="https://github.com/berdakh/pyspeller">the code on GitHub</a><br>
    <a href="https://github.com/berdakh/buffer_bci">buffer_bci, where it came from</a><br>
    <a href="https://github.com/berdakh/pyspeller/blob/main/docs/MANUAL.md">the printable session manual</a><br>
    <a href="https://github.com/berdakh/pyspeller/blob/main/docs/pyspeller_tutorial.ipynb">the tutorial notebook</a>
  </div>
</aside>
<main>
  <div class="page-kicker">{kicker}</div>
  <h1>{title}</h1>
  <p class="lede">{description}</p>
  {body}
  <div class="pager">{pager}</div>
  <p class="meta">Part of <a href="https://github.com/berdakh/pyspeller">pyspeller</a>,
  a pure-python BCI framework built on the ideas of
  <a href="https://github.com/berdakh/buffer_bci">buffer_bci</a>. GPL-3.0.</p>
</main>
</div>
</body>
</html>
"""


def navigation(current):
    out, section = [], None
    for index, (name, title, group) in enumerate(PAGES):
        if group != section:
            if section is not None:
                out.append('</nav></div>')
            out.append('<div class="nav-group"><div class="nav-title">%s</div><nav>' % group)
            section = group
        classes = ' class="current"' if name == current else ''
        number = ('<span class="num">%d</span>' % index) if index else ''
        out.append('<a href="%s.html"%s>%s%s</a>' % (name, classes, number, title))
    out.append('</nav></div>')
    return '\n  '.join(out)


def pager(index):
    parts = []
    if index > 0:
        name, title, _ = PAGES[index - 1]
        parts.append('<a href="%s.html"><span class="dir">previous</span>%s</a>'
                     % (name, title))
    if index < len(PAGES) - 1:
        name, title, _ = PAGES[index + 1]
        parts.append('<a class="next" href="%s.html"><span class="dir">next</span>%s</a>'
                     % (name, title))
    return '\n'.join(parts)


def read_page(name):
    """Front matter (title:, description:) followed by markdown."""
    with open(os.path.join(SOURCE, name + '.md'), encoding='utf-8') as handle:
        text = handle.read()
    meta = {}
    if text.startswith('---'):
        _, front, text = text.split('---', 2)
        for line in front.strip().splitlines():
            key, value = line.split(':', 1)
            meta[key.strip()] = value.strip()
    return meta, text.strip()


def convert(text):
    try:
        import markdown
    except ImportError:
        sys.exit('this needs the markdown package: pip install markdown')
    return markdown.markdown(
        text, extensions=['tables', 'fenced_code', 'attr_list', 'md_in_html', 'toc'])


def main():
    for index, (name, title, group) in enumerate(PAGES):
        meta, text = read_page(name)
        html = TEMPLATE.format(
            title=meta.get('title', title),
            description=meta.get('description', ''),
            kicker=meta.get('kicker', group),
            nav=navigation(name),
            body=convert(text),
            pager=pager(index))
        # keep <svg> and raw html blocks intact: markdown escapes nothing here
        html = re.sub(r'<p>(<(?:figure|div|svg|table)[ >])', r'\1', html)
        html = re.sub(r'(</(?:figure|div|svg|table)>)</p>', r'\1', html)
        target = os.path.join(HERE, name + '.html')
        with open(target, 'w', encoding='utf-8') as handle:
            handle.write(html)
        print('wrote %s' % os.path.relpath(target, HERE))


if __name__ == '__main__':
    main()
