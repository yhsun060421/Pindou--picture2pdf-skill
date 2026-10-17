# 输出契约

## 硬性不变量

1. `cols % 5 == 0` 且 `rows % 5 == 0`。
2. SVG 中 `<g class="cell …">` 的数量 = `cols × rows`。
3. 每个格子的文字代号 ∈ 调色板字母集合（A–T）。
4. 调色板所有 `count` 之和 = `cols × rows`。
5. 所有 `hex` 来自标准色卡（或白色背景 H1）。
6. 交互 PDF 页数 = `1 + 颜色数`。
7. 第 1 页链接数 = 颜色数；每个高亮页链接数 = 颜色数 + 1（含返回）。

## 文件

| 文件 | 说明 |
|---|---|
| `pattern.svg` | 主矢量图：40 单位/格、5×5 粗蓝线、坐标、逐格代号、图例 |
| `pattern.pdf` | 单页打印版（页面比例跟随图纸） |
| `pattern-interactive.pdf` | 1 + N 页交互版；总图 + 每色高亮页 |
| `preview.png` | 交互 PDF 第 1 页的 150dpi 预览 |
| `preprocessed.png` | 透明底主体，便于复查 |
| `report.md` / `report.json` | 网格、颜色、用量、校验结果 |

## SVG 结构

- 根节点包含 `width/height/viewBox`，纯矢量，无位图。
- 每个格子：`<g class="cell c-A"><rect …/><text class="code">A</text></g>`。
- 5×5 大格用 `#1E7FC2`、宽 4.5 的线；单元格线为低透明度黑线。
- 图例行：`<g class="legend-row" data-code="A">`，交互 PDF 的高亮页依赖该属性。
- 顶部/左侧坐标：大格编号 1..N，子编号 1..5。

## 交互 PDF

- 第 1 页：完整图 + 底部使用提示。
- 第 2..N+1 页：目标色保持原色，其余颜色**预混合成浅色实色**（不是透明度），
  避免透明度组导致的体积膨胀与旧阅读器兼容问题。
- 每页都有完整的可点击图例；高亮页右上角有「返回总图」。
- 页面尺寸按图纸比例自动计算，长边 300mm，适合平板全屏查看与打印。

## report.json 关键字段

```json
{
  "grid": {"cols": 50, "rows": 60, "big_cols": 10, "big_rows": 12},
  "palette": [{"letter": "A", "name": "深棕", "mard": "G8", "hex": "#713D2F", "count": 179}],
  "totals": {"cells": 3000, "non_bg": 1618, "colors": 13},
  "pdf": {"pages": 14, "links_page1": 13, "links_page2": 14},
  "validation": {"ok": true, "errors": []}
}
```
