#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render preview PNGs / an animated GIF from an interactive PDF."""
import argparse
import os

import fitz
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pdf', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--width', type=int, default=900)
    ap.add_argument('--pages', default='1,2,4,6,8,10',
                    help='comma separated 1-based page numbers for the GIF')
    ap.add_argument('--gif', default=None)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    doc = fitz.open(a.pdf)
    pages = [int(x) for x in a.pages.split(',') if x.strip()]
    frames = []
    for i in sorted(set([1] + pages)):
        if i < 1 or i > len(doc):
            continue
        page = doc[i - 1]
        zoom = a.width / page.rect.width
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        path = os.path.join(a.out, f'preview-{i:02d}.png')
        pix.save(path)
        if i == 1:
            # also a high-res overview
            hi = page.get_pixmap(matrix=fitz.Matrix(a.width * 1.6 / page.rect.width,
                                                    a.width * 1.6 / page.rect.width))
            hi.save(os.path.join(a.out, 'preview-overview.png'))
        frames.append(Image.open(path).convert('RGB'))
    if a.gif and frames:
        frames[0].save(a.gif, save_all=True, append_images=frames[1:],
                       duration=1400, loop=0, optimize=True)
        print('gif:', a.gif)
    print('pngs:', a.out)


if __name__ == '__main__':
    main()
