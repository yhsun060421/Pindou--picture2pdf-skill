# -*- coding: utf-8 -*-
"""Vector bead-pattern SVG renderer (same visual template as the sample)."""
from __future__ import annotations

import html
import json
import os

from .palette import luminance

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STYLE_PATH = os.path.join(ROOT, 'templates', 'style.json')

FONT = ("Arial, 'Helvetica Neue', 'PingFang SC', 'Hiragino Sans GB', "
        "'Microsoft YaHei', 'Noto Sans CJK SC', 'Source Han Sans SC', sans-serif")


def load_style():
    with open(STYLE_PATH, encoding='utf-8') as f:
        return json.load(f)


def render_svg(cells, assign, palette, meta, style=None):
    """Render the chart.  Returns (svg_string, layout_dict)."""
    style = style or load_style()
    CW = style['cell_size']
    GX, GY = style['grid_origin']
    LEG_W = style['legend_width']
    LEG_GAP = style['legend_gap']
    STEP = style['legend_row_step']
    BLUE = style['blue']
    rows, cols = len(cells), len(cells[0])
    K = len(palette)

    grid_w, grid_h = cols * CW, rows * CW
    leg_x = GX + grid_w + LEG_GAP
    leg_y = GY
    row_y0 = leg_y + 150
    legend_needed = 150 + K * STEP + 470
    svg_w = leg_x + LEG_W + 40
    svg_h = GY + max(grid_h, legend_needed) + 110
    leg_h = legend_needed

    title = html.escape(meta.get('title', '拼豆图纸'))
    subtitle = html.escape(meta.get('subtitle', ''))
    title_fs = 44 if len(title) <= 18 else 34

    out = []
    add = out.append
    add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" '
        f'viewBox="0 0 {svg_w} {svg_h}" font-family="{FONT}">')
    add(f'<title>{title}</title>')
    add(f'<desc>矢量拼豆图纸：{cols}×{rows} 格，5×5 格为一个大格，格内标注颜色代号。</desc>')
    add(f'<rect width="{svg_w}" height="{svg_h}" fill="#FFFFFF"/>')
    add(f'<text x="50" y="72" font-size="{title_fs}" font-weight="700" fill="#12324A">{title}</text>')
    add(f'<text x="50" y="116" font-size="21" fill="#5A6B78">{subtitle}</text>')

    # cells
    for r in range(rows):
        for c in range(cols):
            idx = assign[r][c]
            p = palette[idx]
            x, y = GX + c * CW, GY + r * CW
            if p.get('is_bg'):
                tfill = '#8A949B'
            else:
                tfill = '#FFFFFF' if luminance(p['rgb']) < 0.25 else '#1A1A1A'
            add(f'<g class="cell c-{p["letter"]}"><rect x="{x}" y="{y}" width="{CW}" '
                f'height="{CW}" fill="{p["hex"]}"/>'
                f'<text class="code" x="{x + CW / 2:.1f}" y="{y + CW / 2 + 6.4:.1f}" '
                f'font-size="18" font-weight="700" text-anchor="middle" fill="{tfill}">'
                f'{p["letter"]}</text></g>')

    # minor + major grid
    add('<g stroke="#000000" stroke-opacity="0.13" stroke-width="0.7" shape-rendering="crispEdges">')
    for i in range(1, cols):
        x = GX + i * CW
        add(f'<line x1="{x}" y1="{GY}" x2="{x}" y2="{GY + grid_h}"/>')
    for j in range(1, rows):
        y = GY + j * CW
        add(f'<line x1="{GX}" y1="{y}" x2="{GX + grid_w}" y2="{y}"/>')
    add('</g>')
    add(f'<g stroke="{BLUE}" stroke-width="4.5" shape-rendering="crispEdges">')
    for i in range(0, cols + 1, 5):
        x = GX + i * CW
        add(f'<line x1="{x}" y1="{GY}" x2="{x}" y2="{GY + grid_h}"/>')
    for j in range(0, rows + 1, 5):
        y = GY + j * CW
        add(f'<line x1="{GX}" y1="{y}" x2="{GX + grid_w}" y2="{y}"/>')
    add('</g>')

    # axes
    add('<g text-anchor="middle">')
    for b in range(cols // 5):
        cx = GX + (b * 5 + 2.5) * CW
        add(f'<text x="{cx}" y="{GY - 48}" font-size="27" font-weight="700" fill="{BLUE}">{b + 1}</text>')
        for s in range(5):
            sx = GX + (b * 5 + s + 0.5) * CW
            add(f'<text x="{sx}" y="{GY - 16}" font-size="13" fill="#7A8894">{s + 1}</text>')
    for b in range(rows // 5):
        cy = GY + (b * 5 + 2.5) * CW
        add(f'<text x="{GX - 78}" y="{cy + 9}" font-size="27" font-weight="700" fill="{BLUE}">{b + 1}</text>')
        for s in range(5):
            sy = GY + (b * 5 + s + 0.5) * CW
            add(f'<text x="{GX - 32}" y="{sy + 4.6}" font-size="13" fill="#7A8894">{s + 1}</text>')
    add('</g>')

    # legend panel
    add(f'<rect x="{leg_x}" y="{leg_y}" width="{LEG_W}" height="{leg_h}" rx="16" '
        f'fill="#F7FBFD" stroke="{BLUE}" stroke-width="2.5"/>')
    add(f'<text x="{leg_x + LEG_W / 2}" y="{leg_y + 54}" font-size="30" font-weight="700" '
        f'text-anchor="middle" fill="#12324A">颜色对照表</text>')
    add(f'<text x="{leg_x + LEG_W / 2}" y="{leg_y + 84}" font-size="14" text-anchor="middle" '
        f'fill="#7A8894">标准拼豆配色 · MARD 221 色号体系</text>')
    add(f'<line x1="{leg_x + 30}" y1="{leg_y + 104}" x2="{leg_x + LEG_W - 30}" '
        f'y2="{leg_y + 104}" stroke="#CFE2ED" stroke-width="1.2"/>')

    legend_rows = []
    for i, p in enumerate(palette):
        cy = row_y0 + i * STEP
        add(f'<g class="legend-row" data-code="{p["letter"]}">')
        add(f'<rect x="{leg_x + 14}" y="{cy - 26}" width="{LEG_W - 28}" height="52" '
            f'rx="10" fill="transparent"/>')
        add(f'<circle cx="{leg_x + 48}" cy="{cy}" r="19" fill="{p["hex"]}" '
            f'stroke="#9FB3C0" stroke-width="1.2"/>')
        add(f'<text x="{leg_x + 80}" y="{cy + 7}" font-size="19" font-weight="700" '
            f'fill="#12324A">{p["letter"]}</text>')
        add(f'<text x="{leg_x + 112}" y="{cy - 2}" font-size="17" font-weight="600" '
            f'fill="#243B4A">{html.escape(p["name"])}</text>')
        add(f'<text x="{leg_x + 112}" y="{cy + 20}" font-size="12" fill="#7A8894">'
            f'MARD {p["mard"]} · {p["hex"].upper()}</text>')
        add(f'<text x="{leg_x + LEG_W - 34}" y="{cy + 6}" font-size="15" text-anchor="end" '
            f'fill="#5A6B78">{p["count"]:,} 颗</text>')
        add('</g>')
        if i < K - 1:
            add(f'<line x1="{leg_x + 34}" y1="{cy + 31}" x2="{leg_x + LEG_W - 34}" '
                f'y2="{cy + 31}" stroke="#E6EFF4" stroke-width="1"/>')
        legend_rows.append((leg_x + 14, cy - 26, leg_x + LEG_W - 14, cy + 26))

    sy = row_y0 + K * STEP + 6
    add(f'<line x1="{leg_x + 30}" y1="{sy + 18}" x2="{leg_x + LEG_W - 30}" '
        f'y2="{sy + 18}" stroke="#CFE2ED" stroke-width="1.2"/>')
    total = cols * rows
    nonbg = sum(1 for row in cells for cell in row if not cell['bg'])
    add(f'<text x="{leg_x + 34}" y="{sy + 56}" font-size="19" font-weight="700" '
        f'fill="#12324A">总豆数 {total:,} 颗</text>')
    add(f'<text x="{leg_x + 34}" y="{sy + 84}" font-size="14" fill="#5A6B78">'
        f'非白 {nonbg:,} 颗　·　背景/白色 {total - nonbg:,} 颗</text>')
    notes = [
        '· 1 个像素点 = 1 颗拼豆（1 小格）',
        f'· 5 × 5 小格 = 1 个大格，共 {cols // 5} × {rows // 5} 大格',
        '· 白色/背景格可整板摆满，也可留空',
        '· 色号按 MARD 221 标准色卡匹配',
        '· 屏幕显示与实物豆存在轻微色差，以实物为准',
    ]
    for i, t in enumerate(notes):
        add(f'<text x="{leg_x + 34}" y="{sy + 120 + i * 30}" font-size="14" '
            f'fill="#5A6B78">{html.escape(t)}</text>')

    # mini 5x5
    mx, my, ms = leg_x + 34, sy + 300, 18
    add(f'<text x="{mx}" y="{my - 14}" font-size="14" fill="#7A8894">1 个大格 = 5 × 5 小格</text>')
    for j in range(5):
        for i in range(5):
            add(f'<circle cx="{mx + 10 + i * ms + ms / 2}" cy="{my + 10 + j * ms + ms / 2}" '
                f'r="6.4" fill="{"#FFFFFF" if (i + j) % 2 else "#DCEAF3"}" '
                f'stroke="#B9CAD6" stroke-width="0.8"/>')
    add(f'<rect x="{mx + 10}" y="{my + 10}" width="{5 * ms}" height="{5 * ms}" fill="none" '
        f'stroke="{BLUE}" stroke-width="2.6"/>')

    add('</svg>')
    layout = {
        'svg_w': svg_w, 'svg_h': svg_h,
        'grid_x': GX, 'grid_y': GY, 'cell': CW,
        'cols': cols, 'rows': rows,
        'legend_x': leg_x, 'legend_y': leg_y, 'legend_w': LEG_W,
        'legend_rows': legend_rows,
        'back_btn': (leg_x + 15, 28, leg_x + LEG_W - 15, 106),
        'title': title, 'subtitle': subtitle,
        'bottom_hint_y': svg_h - 27,
    }
    return '\n'.join(out), layout
