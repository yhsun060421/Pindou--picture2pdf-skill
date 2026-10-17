# -*- coding: utf-8 -*-
"""End-to-end pipeline: image -> preprocess -> grid -> palette -> SVG/PDF."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

import fitz
from PIL import Image

from .interactive_pdf import build_interactive_pdf, find_chrome
from .palette import MardPalette, select_palette
from .preprocess import api_from_env, preprocess
from .quantize import build_cells, grid_size
from .render_svg import load_style, render_svg


def _print_html(html, out_pdf, page_w, page_h, chrome, workdir, name):
    hp = os.path.join(workdir, f'{name}.html')
    open(hp, 'w', encoding='utf-8').write(html)
    url = 'file:///' + os.path.abspath(hp).replace('\\', '/')
    subprocess.run([chrome, '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
                    f'--print-to-pdf={os.path.abspath(out_pdf)}', url],
                   check=True, timeout=600,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    d = fitz.open(out_pdf)
    if len(d) != 1:
        raise RuntimeError(f'{name}: expected 1 page, got {len(d)}')
    d.close()


def _page_size(svg_w, svg_h, max_mm=300, margin_mm=6):
    """Page size whose *content box* matches the drawing aspect exactly."""
    content = max_mm - 2 * margin_mm
    if svg_w >= svg_h:
        cw, ch = content, content * svg_h / svg_w
    else:
        cw, ch = content * svg_w / svg_h, content
    ratio = svg_h / svg_w
    extra = 1.5  # mm slack so Chromium never spills to a second page
    return (cw + 2 * margin_mm + extra,
            ch + 2 * margin_mm + extra + ratio * extra + 1.0)


def _single_pdf(svg, layout, out_pdf, chrome, workdir):
    pw, ph = _page_size(layout['svg_w'], layout['svg_h'])
    head = (f'<!doctype html><html><head><meta charset="utf-8"><style>\n'
            f'@page {{ size:{pw:.2f}mm {ph:.2f}mm; margin:6mm; }}\n'
            'html,body { margin:0; padding:0; background:#fff; }\n'
            'svg { display:block; width:100%; height:auto; }\n'
            '</style></head><body>')
    _print_html(head + svg + '</body></html>', out_pdf, pw, ph, chrome, workdir, 'print')


def _preview(pdf_path, out_png):
    d = fitz.open(pdf_path)
    pix = d[0].get_pixmap(dpi=150)
    pix.save(out_png)
    d.close()


def validate_outputs(svg, pdf_single, pdf_interactive, palette, cols, rows):
    errors = []
    svg_cells = len(re.findall(r'<g class="cell c-[A-Z]"', svg))
    if svg_cells != cols * rows:
        errors.append(f'SVG cells {svg_cells} != {cols * rows}')
    if cols % 5 or rows % 5:
        errors.append('grid is not a multiple of 5')
    total = sum(p['count'] for p in palette)
    if total != cols * rows:
        errors.append(f'palette count sum {total} != {cols * rows}')
    letters = {p['letter'] for p in palette}
    codes = set(re.findall(r'<g class="cell c-([A-Z])"', svg))
    if codes - letters:
        errors.append(f'unknown cell codes: {codes - letters}')
    try:
        d = fitz.open(pdf_interactive)
        if len(d) != 1 + len(palette):
            errors.append(f'interactive pages {len(d)} != {1 + len(palette)}')
        if len(d[0].get_links()) != len(palette):
            errors.append(f'page 1 links {len(d[0].get_links())} != {len(palette)}')
        if len(d) > 1 and len(d[1].get_links()) != len(palette) + 1:
            errors.append(f'highlight links {len(d[1].get_links())} != {len(palette) + 1}')
        d.close()
    except Exception as e:
        errors.append(f'interactive PDF check failed: {e}')
    try:
        d = fitz.open(pdf_single)
        if len(d) != 1:
            errors.append(f'single PDF pages {len(d)} != 1')
        d.close()
    except Exception as e:
        errors.append(f'single PDF check failed: {e}')
    return errors


def run(args):
    os.makedirs(args.out, exist_ok=True)
    work = args.out
    chrome = find_chrome(args.chrome)
    style = load_style()

    # 1. preprocessing
    src = os.path.abspath(args.input)
    pre = os.path.join(work, 'preprocessed.png')
    api = api_from_env()
    if args.base_url:
        api['base_url'] = args.base_url
    if args.api_key:
        api['api_key'] = args.api_key
    if args.model:
        api['model'] = args.model
    if args.api_style:
        api['style'] = args.api_style
    used_mode = preprocess(src, pre, mode=args.mode, api=api, keep_bg=args.keep_bg)
    print(f'[1/6] preprocess: {used_mode} -> {pre}')

    # 2. grid
    img = Image.open(pre).convert('RGBA')
    w, h = img.size
    if args.cols and args.rows:
        cols, rows = args.cols, args.rows
        if cols % 5 or rows % 5:
            raise SystemExit('--cols/--rows must be multiples of 5')
    else:
        cols, rows = grid_size(w, h, max_cells=args.max_cells, min_cells=args.min_cells)
    cells, cols, rows = build_cells(img, cols, rows,
                                    alpha_threshold=args.alpha_threshold,
                                    pad_cells=args.pad_cells)
    print(f'[2/6] grid: {cols} x {rows} = {cols * rows} cells')

    # 3. palette
    nonbg = [cell['rgb'] for row in cells for cell in row if not cell['bg']]
    if not nonbg:
        raise SystemExit('No subject pixels found. Check preprocessing / alpha threshold.')
    mard = MardPalette()
    fixed = [c.strip() for c in args.fixed_palette.split(',')] if args.fixed_palette else None
    entries, flat = select_palette(nonbg, k=args.colors, min_delta=args.min_delta,
                                   fixed_codes=fixed, seed=args.seed)
    # background entry last
    bg_count = sum(1 for row in cells for cell in row if cell['bg'])
    bg_index = None
    if bg_count:
        white = mard.nearest((255, 255, 255))[0]
        bg_index = len(entries)
        entries.append({
            'mard': white['code'], 'hex': '#FFFFFF', 'rgb': (255, 255, 255),
            'name': '白色', 'count': bg_count, 'letter': chr(ord('A') + bg_index),
            'is_bg': True,
        })
    for i, e in enumerate(entries):
        e['letter'] = chr(ord('A') + i)
    if len(entries) > 20:
        raise SystemExit('Too many colours (max 20). Lower --colors.')

    # assign to full grid
    assign = []
    it = iter(flat)
    for row in cells:
        ar = []
        for cell in row:
            ar.append(bg_index if cell['bg'] else next(it))
        assign.append(ar)

    print('[3/6] palette: ' + ', '.join(f"{e['letter']}={e['mard']}({e['count']})" for e in entries))

    # 4. SVG
    total = cols * rows
    title = args.title or '拼豆图纸'
    subtitle = (f'1 格 = 1 颗豆　·　5 × 5 格 = 1 个大格　·　'
                f'全图 {cols // 5} × {rows // 5} 个大格（{cols} × {rows} 格，共 {total:,} 颗）')
    svg, layout = render_svg(cells, assign, entries,
                             {'title': title, 'subtitle': subtitle}, style)
    svg_path = os.path.join(work, 'pattern.svg')
    open(svg_path, 'w', encoding='utf-8').write(svg)
    print(f'[4/6] SVG: {svg_path}')

    # 5. PDFs
    single_pdf = os.path.join(work, 'pattern.pdf')
    _single_pdf(svg, layout, single_pdf, chrome, work)
    inter_pdf = os.path.join(work, 'pattern-interactive.pdf')
    metrics = build_interactive_pdf(svg, layout, entries, inter_pdf, chrome=chrome,
                                    workdir=work, fade_ratio=args.fade_ratio)
    print(f'[5/6] PDFs: {single_pdf}, {inter_pdf} ({metrics["pages"]} pages)')

    # 6. report + preview
    preview = os.path.join(work, 'preview.png')
    _preview(inter_pdf, preview)
    errors = validate_outputs(svg, single_pdf, inter_pdf, entries, cols, rows)
    report = {
        'input': src,
        'preprocess_mode': used_mode,
        'grid': {'cols': cols, 'rows': rows, 'big_cols': cols // 5,
                 'big_rows': rows // 5, 'total_cells': total},
        'palette': [{k: v for k, v in e.items() if k != 'rgb'} for e in entries],
        'totals': {'cells': total, 'non_bg': len(nonbg), 'colors': len(entries)},
        'pdf': metrics,
        'validation': {'ok': not errors, 'errors': errors},
        'outputs': {'svg': svg_path, 'pdf': single_pdf, 'interactive_pdf': inter_pdf,
                    'preview': preview},
    }
    json.dump(report, open(os.path.join(work, 'report.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)
    with open(os.path.join(work, 'report.md'), 'w', encoding='utf-8') as f:
        f.write(f"# {title}\n\n")
        f.write(f"- 网格：{cols} × {rows}（{cols//5} × {rows//5} 个大格）\n")
        f.write(f"- 总豆数：{total:,}（非背景 {len(nonbg):,}）\n")
        f.write(f"- 颜色数：{len(entries)}\n\n")
        f.write('| 代号 | 名称 | MARD | HEX | 数量 |\n|---|---|---|---|---|\n')
        for e in entries:
            f.write(f"| {e['letter']} | {e['name']} | {e['mard']} | {e['hex']} | {e['count']:,} |\n")
        f.write('\n## 校验\n\n')
        f.write('✅ 全部通过\n' if not errors else '\n'.join('- ❌ ' + x for x in errors))
    print(f'[6/6] report: {report["validation"]["ok"] and "OK" or "FAILED"}')

    if errors:
        for e in errors:
            print('  - ' + e)
        sys.exit(1)
    print('done:', work)
    return report


def build_parser():
    p = argparse.ArgumentParser(description='Image -> standard-colour bead pattern + interactive PDF')
    p.add_argument('--input', required=True, help='input image')
    p.add_argument('--out', required=True, help='output directory')
    p.add_argument('--title', default='拼豆图纸', help='chart title')
    p.add_argument('--mode', default='auto', choices=['auto', 'chibi', 'cutout', 'none'],
                   help='preprocessing mode (auto = cutout; chibi for people)')
    p.add_argument('--colors', type=int, default=12, help='max number of bead colours')
    p.add_argument('--max-cells', type=int, default=60, help='longest side in cells (multiple of 5)')
    p.add_argument('--min-cells', type=int, default=10)
    p.add_argument('--cols', type=int, help='explicit columns (multiple of 5)')
    p.add_argument('--rows', type=int, help='explicit rows (multiple of 5)')
    p.add_argument('--pad-cells', type=int, default=0, help='transparent margin in cells')
    p.add_argument('--alpha-threshold', type=int, default=64)
    p.add_argument('--min-delta', type=float, default=6.0, help='min CIEDE2000 between colours')
    p.add_argument('--fixed-palette', help='comma-separated MARD codes, e.g. H7,G8,G7,H1')
    p.add_argument('--fade-ratio', type=float, default=0.13)
    p.add_argument('--seed', type=int, default=7)
    p.add_argument('--keep-bg', action='store_true', help='do not remove white background in mode=none')
    p.add_argument('--chrome', help='Chromium executable (or BEAD_CHROME)')
    p.add_argument('--base-url', help='image API base URL (or BEAD_IMG_BASE_URL)')
    p.add_argument('--api-key', help='image API key (or BEAD_IMG_API_KEY)')
    p.add_argument('--model', help='image model (or BEAD_IMG_MODEL)')
    p.add_argument('--api-style', choices=['openai', 'chat'], help='image API style')
    return p


if __name__ == '__main__':
    run(build_parser().parse_args())
