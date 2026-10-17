---
name: bead-pattern
description: Convert any image into a standard-colour bead pattern (1 cell = 1 bead, 5×5 = one big cell, per-cell A–Z colour codes) and deliver a zero-install interactive PDF. Use when the user asks for 拼豆图纸, perler/Hama bead art, pixel bead chart, or wants an image turned into a bead pattern with a colour legend and counts.
---

# Bead Pattern Skill

Turn **any image** into a production-ready bead chart + interactive PDF that works on
iPhone, iPad, Android and desktop **without installing anything**.

## Hard rules (do not break)

1. **One cell = one bead.** Never draw a "bead" that spans more than one cell.
2. **5×5 cells = one big cell.** Both grid dimensions MUST be multiples of 5.
3. Every cell MUST carry its colour code (A, B, C …). No blank cells, no guessed codes.
4. Colours MUST come from the bundled **MARD 221** standard palette
   (`references/palette-mard221.json`). Never invent a hex value by eye.
5. The interactive PDF is the primary deliverable. Do not hand the user a local HTML
   file as the main product — iOS Safari cannot open local HTML.

## Inputs to collect

- An image path (required).
- A title (optional, default `拼豆图纸`).
- Preferred longest side in cells (optional, default 60; must be a multiple of 5).
- Colour count (optional, default 12; max 20).
- If the image contains people: use `--mode chibi`. Cartoons / objects: `--mode cutout`.
  If the image is already a clean cutout with transparency: `--mode none`.

## Image API configuration (ask the user)

The preprocessing model is **user supplied**. Ask for and read from environment:

```bash
BEAD_IMG_BASE_URL   # e.g. https://api.openai.com  or a compatible proxy
BEAD_IMG_API_KEY
BEAD_IMG_MODEL      # optional, default gpt-image-1
BEAD_IMG_API_STYLE  # openai | chat, default openai
```

Never hardcode a key, never print it, never commit it. If the key is missing and the
mode is not `none`, stop and ask the user for it (or ask whether the image is already cut out).

## Run

From this skill's directory (the folder containing `SKILL.md`; use its absolute path if your CWD is elsewhere):

```bash
python scripts/run_pipeline.py \
  --input /path/to/photo.jpg \
  --out outputs/my-pattern \
  --title "卷发女孩" \
  --mode chibi \
  --colors 13 \
  --max-cells 60
```

Write `--out` to a folder in the user's workspace, not inside the skill folder. Then validate:

```bash
python scripts/validate.py --out outputs/my-pattern
```

## Quality gate (inspect, don't assume)

1. Open `outputs/my-pattern/preview.png`. The subject must be recognisable.
2. If details are lost, re-run with `--max-cells 60` (or 75) and/or `--colors 14–16`.
3. If the background was eaten or the cutout is wrong, re-run preprocessing or use
   `--mode none` with a manually cleaned PNG.
4. `validate.py` must print `OK` (SVG cell count, palette counts, PDF pages, PDF links).
5. Check that every legend colour has a MARD code and a count.

## Deliverables to give the user

| File | Purpose |
|---|---|
| `pattern-interactive.pdf` | **Primary.** Overview + one highlight page per colour; tap a legend colour to jump, tap 返回总图 to go back. Works in Apple Books / Files / any PDF viewer. |
| `pattern.pdf` | One-page vector chart for printing. |
| `pattern.svg` | Editable vector source. |
| `preview.png` | Quick preview. |
| `report.md` / `report.json` | Grid, palette, counts, validation. |

Explain the buyer workflow in one short paragraph:

> 打开交互 PDF → 点右侧颜色看该颜色高亮 → 点右上角“返回总图”回到全图。
> 不需要联网、不需要装 App，iPhone / iPad / 安卓都能用。

## Colour methodology (why it is trustworthy)

- The palette is **MARD 221**, the mainstream Chinese bead standard (MIT-licensed data,
  see `references/palette-mard221.json`).
- Cells are clustered in **CIELAB** (weighted k-means), then each cluster is matched to
  the nearest MARD colour using **CIEDE2000**.
- Colours closer than `--min-delta` (default 6) are merged, so the chart stays buildable.
- Every cell is finally assigned to a **real MARD colour**, never to an interpolated hex.
- White/background is added as the last palette entry and can be left empty when beading.

## Failure handling

- `Image API is not configured` → ask for base URL/key, or use `--mode none`.
- `No subject pixels` → the cutout is empty; try another mode or a cleaner image.
- `Chrome/Edge not found` → set `BEAD_CHROME` to a Chromium executable.
- PDF link count mismatch → do not deliver; re-run `validate.py` and fix before sending.

## References

- `references/palette-methodology.md` — colour selection details.
- `references/output-spec.md` — exact output contract.
- `references/prompts.md` — preprocessing prompts.
- `references/troubleshooting.md` — common failures.
