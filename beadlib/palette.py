# -*- coding: utf-8 -*-
"""Standard bead palette handling: MARD 221, CIELAB / CIEDE2000, clustering."""
from __future__ import annotations

import colorsys
import json
import math
import os
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_PALETTE = os.path.join(ROOT, 'references', 'palette-mard221.json')


# ---------------------------------------------------------------------------
# Colour maths
# ---------------------------------------------------------------------------
def srgb_to_lab(rgb):
    r, g, b = [v / 255.0 for v in rgb]
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = f(r), f(g), f(b)
    X = r * .4124 + g * .3576 + b * .1805
    Y = r * .2126 + g * .7152 + b * .0722
    Z = r * .0193 + g * .1192 + b * .9505
    Xn, Yn, Zn = .95047, 1.0, 1.08883
    g_ = lambda t: t ** (1 / 3) if t > .008856 else (7.787 * t + 16 / 116)
    fx, fy, fz = g_(X / Xn), g_(Y / Yn), g_(Z / Zn)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def ciede2000(lab1, lab2):
    """CIEDE2000 colour difference (Sharma et al. formulation)."""
    L1, a1, b1 = lab1
    L2, a2, b2 = lab2
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cbar = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cbar ** 7 / (Cbar ** 7 + 25 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360
    h2p = math.degrees(math.atan2(b2, a2p)) % 360
    dLp, dCp = L2 - L1, C2p - C1p
    dhp = 0.0
    if C1p * C2p != 0:
        dh = h2p - h1p
        if dh > 180:
            dh -= 360
        elif dh < -180:
            dh += 360
        dhp = dh
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp / 2))
    Lbar, Cbarp = (L1 + L2) / 2, (C1p + C2p) / 2
    hsum = h1p + h2p
    if C1p * C2p == 0:
        hbar = hsum
    elif abs(h1p - h2p) <= 180:
        hbar = hsum / 2
    elif hsum < 360:
        hbar = (hsum + 360) / 2
    else:
        hbar = (hsum - 360) / 2
    T = (1 - 0.17 * math.cos(math.radians(hbar - 30))
         + 0.24 * math.cos(math.radians(2 * hbar))
         + 0.32 * math.cos(math.radians(3 * hbar + 6))
         - 0.20 * math.cos(math.radians(4 * hbar - 63)))
    dtheta = 30 * math.exp(-(((hbar - 275) / 25) ** 2))
    RC = 2 * math.sqrt(Cbarp ** 7 / (Cbarp ** 7 + 25 ** 7))
    SL = 1 + 0.015 * (Lbar - 50) ** 2 / math.sqrt(20 + (Lbar - 50) ** 2)
    SC = 1 + 0.045 * Cbarp
    SH = 1 + 0.015 * Cbarp * T
    RT = -math.sin(math.radians(2 * dtheta)) * RC
    return math.sqrt((dLp / SL) ** 2 + (dCp / SC) ** 2 + (dHp / SH) ** 2
                     + RT * (dCp / SC) * (dHp / SH))


def hex_to_rgb(hexc):
    h = hexc.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return '#%02X%02X%02X' % tuple(int(round(v)) for v in rgb)


def luminance(rgb):
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = [f(v / 255) for v in rgb]
    return .2126 * r + .7152 * g + .0722 * b


def color_name_zh(rgb):
    """A descriptive Chinese name generated from HSL (not a brand name)."""
    r, g, b = [v / 255 for v in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    hd = h * 360
    if s < 0.10 or (l > 0.90 and s < 0.18):
        if l > 0.94:
            return '白色'
        if l > 0.80:
            return '浅灰'
        if l > 0.62:
            return '银灰'
        if l > 0.42:
            return '中灰'
        if l > 0.22:
            return '深灰'
        return '黑色'
    if 15 <= hd <= 45 and l > 0.72 and s < 0.45:
        return '肤色'
    if 5 <= hd <= 55 and l < 0.58 and s < 0.60:
        base = '棕'
    elif 15 <= hd <= 55 and s < 0.45 and l >= 0.58:
        return '浅棕'
    elif 60 <= hd <= 100 and s < 0.55 and l < 0.55:
        return '橄榄'
    elif hd < 15 or hd >= 345:
        base = '红'
    elif hd < 40:
        base = '橙'
    elif hd < 66:
        base = '黄'
    elif hd < 90:
        base = '黄绿'
    elif hd < 150:
        base = '绿'
    elif hd < 190:
        base = '青'
    elif hd < 250:
        base = '蓝'
    elif hd < 290:
        base = '紫'
    elif hd < 330:
        base = '品红'
    else:
        base = '粉'
    if l < 0.36:
        return '深' + base
    if l > 0.78:
        return '浅' + base
    if s > 0.85 and l > 0.55:
        return '亮' + base
    return base


# ---------------------------------------------------------------------------
# Palette loading
# ---------------------------------------------------------------------------
class MardPalette:
    def __init__(self, path=DEFAULT_PALETTE):
        data = json.load(open(path, encoding='utf-8'))
        self.title = data.get('title', 'MARD 221')
        self.colors = []
        for c in data['colors']:
            rgb = tuple(c['rgb'])
            self.colors.append({
                'code': c['code'], 'hex': c.get('hex') or rgb_to_hex(rgb),
                'rgb': rgb, 'lab': srgb_to_lab(rgb), 'group': c.get('group', ''),
            })

    def nearest(self, rgb, exclude=None):
        lab = srgb_to_lab(rgb)
        best, bd = None, 1e9
        for c in self.colors:
            if exclude and c['code'] in exclude:
                continue
            d = ciede2000(lab, c['lab'])
            if d < bd:
                best, bd = c, d
        return best, bd

    def by_code(self, code):
        for c in self.colors:
            if c['code'] == code:
                return c
        raise KeyError(code)


# ---------------------------------------------------------------------------
# Clustering / palette selection
# ---------------------------------------------------------------------------
def _kmeans(points, weights, k, restarts=3, iters=30, seed=7):
    """Weighted k-means in Lab. Returns (centres, inertia)."""
    pts = np.asarray(points, dtype=float)
    w = np.asarray(weights, dtype=float)
    n = len(pts)
    k = min(k, n)
    rng = np.random.default_rng(seed)
    best_c, best_inertia = None, float('inf')
    for _ in range(restarts):
        # weighted k-means++ initialisation
        centres = [pts[rng.choice(n, p=w / w.sum())]]
        for _ in range(1, k):
            d2 = np.min(((pts[:, None, :] - np.array(centres)[None, :, :]) ** 2).sum(2), axis=1)
            p = d2 * w
            if p.sum() <= 0:
                p = w
            centres.append(pts[rng.choice(n, p=p / p.sum())])
        C = np.array(centres)
        for _ in range(iters):
            dist = ((pts[:, None, :] - C[None, :, :]) ** 2).sum(2)
            lab = dist.argmin(1)
            newC = C.copy()
            for j in range(k):
                m = lab == j
                if m.sum() > 0:
                    newC[j] = (pts[m] * w[m, None]).sum(0) / w[m].sum()
            if np.allclose(newC, C, atol=1e-4):
                C = newC
                break
            C = newC
        dist = ((pts[:, None, :] - C[None, :, :]) ** 2).sum(2)
        inertia = float((dist.min(1) * w).sum())
        if inertia < best_inertia:
            best_c, best_inertia = C, inertia
    return best_c, best_inertia


def select_palette(cell_rgbs, k=12, min_delta=6.0, mard_path=DEFAULT_PALETTE,
                   fixed_codes=None, seed=7):
    """Choose <= k standard MARD colours, then assign every cell to one.

    Returns (entries, assignment) where entries is a list of dicts with
    code/mard/hex/rgb/name/count and assignment is a list of entry indices.
    """
    mard = MardPalette(mard_path)
    if fixed_codes:
        chosen = [mard.by_code(c) for c in fixed_codes]
    else:
        # cluster unique colours (weighted by frequency) for speed
        cnt = Counter(tuple(int(round(v)) for v in c) for c in cell_rgbs)
        uniq = list(cnt.keys())
        weights = [cnt[u] for u in uniq]
        labs = [srgb_to_lab(u) for u in uniq]
        centres, _ = _kmeans(labs, weights, min(k, len(uniq)), seed=seed)
        # map centres to nearest MARD, then enforce distinctness / min delta
        candidates = []
        for c in centres:
            best, bd = None, 1e9
            for mc in mard.colors:
                dd = ciede2000(tuple(float(v) for v in c), mc['lab'])
                if dd < bd:
                    best, bd = mc, dd
            candidates.append([0.0, best, bd])
        for u, wgt in zip(uniq, weights):
            lab = srgb_to_lab(u)
            dists = [sum((a - b) ** 2 for a, b in zip(lab, c)) for c in centres]
            j = int(np.argmin(dists))
            candidates[j][0] += wgt
        candidates.sort(key=lambda x: -x[0])
        chosen = []
        for weight, mc, bd in candidates:
            if mc is None or mc['code'] in [c['code'] for c in chosen]:
                continue
            if any(ciede2000(mc['lab'], c['lab']) < min_delta for c in chosen):
                continue
            chosen.append(mc)
        if not chosen:
            chosen = [mard.nearest(cell_rgbs[0])[0]]

    # assign every cell to the nearest chosen standard colour
    chosen_labs = [c['lab'] for c in chosen]
    counts = Counter()
    assign = []
    for rgb in cell_rgbs:
        lab = srgb_to_lab(rgb)
        ds = [ciede2000(lab, cl) for cl in chosen_labs]
        j = int(np.argmin(ds))
        counts[j] += 1
        assign.append(j)

    # drop unused colours, renumber
    used = sorted(counts.keys(), key=lambda j: (-counts[j], chosen[j]['code']))
    remap = {}
    entries = []
    for newi, oldi in enumerate(used):
        c = chosen[oldi]
        remap[oldi] = newi
        entries.append({
            'mard': c['code'], 'hex': c['hex'], 'rgb': c['rgb'],
            'name': color_name_zh(c['rgb']), 'count': counts[oldi],
        })
    assign = [remap[j] for j in assign]
    for i, e in enumerate(entries):
        e['letter'] = chr(ord('A') + i)
    return entries, assign
