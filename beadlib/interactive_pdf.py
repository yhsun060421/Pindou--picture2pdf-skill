# -*- coding: utf-8 -*-
"""Zero-install interactive PDF: overview + one highlight page per colour."""
from __future__ import annotations

import html
import os
import re
import subprocess

import fitz

from .palette import luminance


def blend(hexc, ratio):
    h = hexc.lstrip('#')
    vals = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    return '#%02X%02X%02X' % tuple(round(v * ratio + 255 * (1 - ratio)) for v in vals)


def find_chrome(explicit=None):
    candidates = [explicit, os.environ.get('BEAD_CHROME'),
                  r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                  r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
                  r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
                  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                  '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
                  '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser']
    for c in candidates:
        if c and os.path.exists(c):
            return c
    raise RuntimeError('Chrome/Edge not found. Set BEAD_CHROME to a Chromium executable.')


CELL_RE = re.compile(r'<g class="cell c-([A-Z])">.*?</g>', re.S)
RECT_FILL_RE = re.compile(r'(<rect[^>]*fill=")#[0-9A-Fa-f]{6}"')
TEXT_FILL_RE = re.compile(r'(<text[^>]*fill=")#[0-9A-Fa-f]{6}"')


def build_interactive_pdf(base_svg, layout, palette, out_pdf,
                          chrome=None, workdir='.', fade_ratio=0.13,
                          page_max_mm=300, margin_mm=6):
    """Build the 1 + K page PDF and add internal links. Returns metrics."""
    K = len(palette)
    by_letter = {p['letter']: p for p in palette}
    faded = {p['letter']: blend(p['hex'], fade_ratio) for p in palette}
    FADED_TEXT = '#B9C2C8'

    title = layout['title']
    subtitle = layout['subtitle']
    bx0, by0, bx1, by1 = layout['back_btn']

    # page 1: add a bottom hint
    hint = (f'<text x="50" y="{layout["bottom_hint_y"]}" font-size="20" fill="#1E7FC2">'
            '使用：点按右侧任一颜色 → 跳到该颜色高亮页；在高亮页点右上角【返回总图】回到本页。</text>')
    svg_base = base_svg.replace('</svg>', hint + '\n</svg>')
    sections = ['<section>' + svg_base + '</section>']

    for p in palette:
        L = p['letter']

        def repl(m, target=L):
            block, code = m.group(0), m.group(1)
            if code == target:
                if luminance(by_letter[code]['rgb']) > 0.93:
                    block = block.replace(
                        f'fill="{by_letter[code]["hex"]}"/>',
                        f'fill="#E4F0F8" stroke="#7FB4D6" stroke-width="0.8"/>', 1)
                return block
            block = RECT_FILL_RE.sub(lambda x: x.group(1) + faded[code] + '"', block, count=1)
            block = TEXT_FILL_RE.sub(lambda x: x.group(1) + FADED_TEXT + '"', block, count=1)
            return block

        s = CELL_RE.sub(repl, base_svg)
        # tint the active legend row (scoped to this page section)
        style = (f'<style>.hl-{L} .legend-row[data-code="{L}"] rect{{fill:#E3F1F9}}</style>')
        oe = s.index('>') + 1
        s = s[:oe] + style + s[oe:]

        hl_title = html.escape(f'高亮 {L} · {p["name"]} · {p["count"]:,} 颗')
        s = s.replace(f'>{title}</text>', f'>{hl_title}</text>')
        s = s.replace(f'>{subtitle}</text>',
                      '>其余颜色已淡化，方便对照挑豆；点右上角【返回总图】回到全图。</text>')

        btn = (f'<rect x="{bx0}" y="{by0}" width="{bx1 - bx0}" height="{by1 - by0}" '
               f'rx="18" fill="#1E7FC2"/>'
               f'<text x="{(bx0 + bx1) / 2}" y="{by0 + (by1 - by0) * 0.65:.1f}" '
               f'font-size="27" font-weight="700" text-anchor="middle" fill="#FFFFFF">'
               f'← 返回总图</text>')
        s = s.replace('</svg>', btn + '\n</svg>')
        sections.append(f'<section class="hl-{L}">' + s + '</section>')

    # page size matching the drawing aspect
    svg_w, svg_h = layout['svg_w'], layout['svg_h']
    content = page_max_mm - 2 * margin_mm
    if svg_w >= svg_h:
        cw, ch = content, content * svg_h / svg_w
    else:
        cw, ch = content * svg_w / svg_h, content
    ratio = svg_h / svg_w
    extra = 1.5
    page_w = cw + 2 * margin_mm + extra
    page_h = ch + 2 * margin_mm + extra + ratio * extra + 1.0

    head = (f'<!doctype html><html><head><meta charset="utf-8"><style>\n'
            f'@page {{ size:{page_w:.2f}mm {page_h:.2f}mm; margin:{margin_mm}mm; }}\n'
            'html,body { margin:0; padding:0; background:#fff; }\n'
            'section { break-after:page; page-break-after:always; }\n'
            'section:last-child { break-after:auto; page-break-after:auto; }\n'
            'svg { display:block; width:100%; height:auto; }\n'
            '</style></head><body>\n')
    work_html = os.path.join(workdir, 'interactive-print.html')
    open(work_html, 'w', encoding='utf-8').write(head + '\n'.join(sections) + '\n</body></html>')

    raw_pdf = os.path.join(workdir, 'interactive-raw.pdf')
    chrome = find_chrome(chrome)
    url = 'file:///' + os.path.abspath(work_html).replace('\\', '/')
    subprocess.run([chrome, '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
                    f'--print-to-pdf={os.path.abspath(raw_pdf)}', url],
                   check=True, timeout=600,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    doc = fitz.open(raw_pdf)
    if len(doc) != 1 + K:
        raise RuntimeError(f'expected {1 + K} pages, got {len(doc)}')
    W, H = doc[0].rect.width, doc[0].rect.height
    margin = margin_mm / 25.4 * 72
    scale = (W - 2 * margin) / svg_w
    ox, oy = margin, margin

    def to_pdf(x0, y0, x1, y1):
        return fitz.Rect(ox + x0 * scale, oy + y0 * scale,
                         ox + x1 * scale, oy + y1 * scale)

    legend_rects = [to_pdf(*r) for r in layout['legend_rows']]
    back_rect = to_pdf(bx0, by0, bx1, by1)
    for pno in range(len(doc)):
        page = doc[pno]
        for i, r in enumerate(legend_rects):
            page.insert_link({'kind': fitz.LINK_GOTO, 'from': r,
                              'page': 1 + i, 'to': fitz.Point(0, 0)})
        if pno > 0:
            page.insert_link({'kind': fitz.LINK_GOTO, 'from': back_rect,
                              'page': 0, 'to': fitz.Point(0, 0)})
    doc.save(out_pdf, garbage=0, deflate=True)
    doc.close()

    check = fitz.open(out_pdf)
    metrics = {
        'pages': len(check),
        'page_size_pt': [round(W, 2), round(H, 2)],
        'links_page1': len(check[0].get_links()),
        'links_page2': len(check[1].get_links()) if len(check) > 1 else 0,
    }
    check.close()
    return metrics
