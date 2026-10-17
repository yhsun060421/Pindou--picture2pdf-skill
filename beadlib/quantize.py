# -*- coding: utf-8 -*-
"""Image -> bead grid (one cell = one bead; dimensions are multiples of 5)."""
from __future__ import annotations

import math

import numpy as np
from PIL import Image


def _round5(v):
    return max(5, int(round(v / 5.0)) * 5)


def grid_size(w, h, max_cells=60, min_cells=10):
    """Pick grid dimensions that preserve aspect and are multiples of 5."""
    if w <= 0 or h <= 0:
        raise ValueError('image has no subject')
    if w >= h:
        cols = _round5(max_cells)
        rows = _round5(max_cells * h / w)
    else:
        rows = _round5(max_cells)
        cols = _round5(max_cells * w / h)
    cols = max(_round5(min_cells), min(100, cols))
    rows = max(_round5(min_cells), min(100, rows))
    return cols, rows


def build_cells(img, cols, rows, alpha_threshold=64, pad_cells=0):
    """Area-average an RGBA image into a grid of bead cells."""
    img = img.convert('RGBA')
    w, h = img.size

    # fit the subject into the grid while preserving aspect, centred
    scale = min(cols / w, rows / h)
    nw, nh = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
    resized = img.resize((nw, nh), Image.BOX)
    canvas = Image.new('RGBA', (cols, rows), (255, 255, 255, 0))
    ox, oy = (cols - nw) // 2, (rows - nh) // 2
    canvas.alpha_composite(resized, (ox, oy))

    # Premultiplied alpha prevents dark fringes at transparent edges.
    full = np.asarray(canvas).astype(np.float32)
    full[:, :, :3] *= full[:, :, 3:4] / 255.0
    pimg = Image.fromarray(np.clip(full, 0, 255).astype(np.uint8), 'RGBA')
    small = np.asarray(pimg.resize((cols, rows), Image.BOX)).astype(np.float32)
    sa = small[:, :, 3]
    srgb = np.zeros((rows, cols, 3), np.float32)
    nz = sa > 1
    srgb[nz] = small[nz, :3] * 255.0 / sa[nz, None]

    cells = []
    for r in range(rows):
        row = []
        for c in range(cols):
            alpha = float(sa[r, c])
            bg = alpha < alpha_threshold
            row.append({
                'rgb': (255, 255, 255) if bg else tuple(int(round(v)) for v in srgb[r, c]),
                'alpha': alpha,
                'bg': bg,
            })
        cells.append(row)

    if pad_cells > 0:
        p = int(pad_cells)
        padded = [[{'rgb': (255, 255, 255), 'alpha': 0, 'bg': True}
                   for _ in range(cols + 2 * p)] for _ in range(rows + 2 * p)]
        for r in range(rows):
            for c in range(cols):
                padded[r + p][c + p] = cells[r][c]
        cells = padded
        cols, rows = cols + 2 * p, rows + 2 * p
        # keep multiples of 5
        if cols % 5 or rows % 5:
            raise ValueError('pad_cells must keep the grid a multiple of 5')

    return cells, cols, rows
