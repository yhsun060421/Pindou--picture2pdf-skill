#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate an output folder produced by the pipeline."""
import argparse
import json
import os
import re
import sys

import fitz


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    errs = []
    report_path = os.path.join(a.out, 'report.json')
    if not os.path.exists(report_path):
        print('missing report.json')
        sys.exit(1)
    rep = json.load(open(report_path, encoding='utf-8'))
    grid = rep.get('grid', {})
    cols, rows = grid.get('cols', 0), grid.get('rows', 0)
    palette = rep.get('palette', [])
    svg_path = rep['outputs']['svg']
    svg = open(svg_path, encoding='utf-8').read()
    n = len(re.findall(r'<g class="cell c-[A-Z]"', svg))
    if n != cols * rows:
        errs.append(f'SVG cells {n} != {cols*rows}')
    if cols % 5 or rows % 5:
        errs.append('grid not multiple of 5')
    if sum(p['count'] for p in palette) != cols * rows:
        errs.append('palette counts do not sum to grid')
    for p in palette:
        if not re.fullmatch(r'[A-T]', p['letter']):
            errs.append(f"bad letter {p.get('letter')}")
        if not re.fullmatch(r'#[0-9A-Fa-f]{6}', p['hex']):
            errs.append(f"bad hex {p.get('hex')}")
    ip = rep['outputs']['interactive_pdf']
    d = fitz.open(ip)
    npages = len(d)
    if npages != 1 + len(palette):
        errs.append(f'interactive pages {npages} != {1+len(palette)}')
    if len(d[0].get_links()) != len(palette):
        errs.append(f'page 1 links {len(d[0].get_links())} != {len(palette)}')
    if npages > 1 and len(d[1].get_links()) != len(palette) + 1:
        errs.append(f'page 2 links {len(d[1].get_links())} != {len(palette)+1}')
    d.close()
    for key in ['svg', 'pdf', 'interactive_pdf', 'preview']:
        if not os.path.exists(rep['outputs'][key]):
            errs.append(f'missing {key}: {rep["outputs"][key]}')
    if errs:
        print('FAILED')
        for e in errs:
            print(' -', e)
        sys.exit(1)
    print(f'OK: {cols}x{rows}, {len(palette)} colours, {npages}-page interactive PDF')


if __name__ == '__main__':
    main()
