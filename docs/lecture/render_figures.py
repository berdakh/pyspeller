# -*- coding: utf-8 -*-
"""Render the SVG diagrams the slide deck needs as PNG.

PowerPoint handles SVG unevenly across versions, so the four diagrams the deck
takes from ../assets/img are kept here as PNG at twice their nominal size.
Run this after editing one of those SVGs, then rebuild the deck:

    python3 render_figures.py
    node build_slides.js

It uses Playwright's Chromium purely as a renderer; any other SVG-to-PNG tool
(rsvg-convert, Inkscape, cairosvg) produces an equivalent file.
"""
import os
import re

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'assets', 'img')
OUT = os.path.join(HERE, 'figures')
FIGURES = ('architecture', 'gtec-chain', 'matrix-decode', 'session-timeline',
           'sampling')


def main():
    with sync_playwright() as play:
        browser = play.chromium.launch(args=['--no-sandbox'])
        for name in FIGURES:
            path = os.path.join(SRC, name + '.svg')
            box = re.search(r'viewBox="0 0 (\d+) (\d+)"', open(path).read())
            width, height = int(box.group(1)), int(box.group(2))
            page = browser.new_page(viewport={'width': width, 'height': height},
                                    device_scale_factor=2)
            page.goto('file://' + os.path.abspath(path))
            page.wait_for_timeout(150)
            page.screenshot(path=os.path.join(OUT, name + '.png'))
            page.close()
            print('wrote figures/%s.png (%d x %d)' % (name, width * 2, height * 2))
        browser.close()


if __name__ == '__main__':
    main()
