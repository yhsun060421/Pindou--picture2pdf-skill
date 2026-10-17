# 故障排查

## 图像 API

**`Image API is not configured`**
设置 `BEAD_IMG_BASE_URL` 与 `BEAD_IMG_API_KEY`，或对已抠图使用 `--mode none`。

**401 / 403**
key 错误或额度不足；确认 base URL 与服务商匹配。

**404**
base URL 可能已包含 `/v1`，脚本两种都兼容；若仍 404，确认服务商是否提供
`/v1/images/edits` 或改用 `BEAD_IMG_API_STYLE=chat`。

**返回没有图片**
用 `--api-style chat` 或检查响应格式；错误信息会打印响应前 800 字符。

## Chrome / PDF

**`Chrome/Edge not found`**
安装 Chrome 或 Edge；或 `export BEAD_CHROME=/path/to/chrome`。

**打印超时**
格子特别多（> 100×100）或颜色很多时，减少 `--colors` / `--max-cells`。

**PDF 页数不对**
通常是某页 SVG 高度超出页面。检查 `--max-cells`，或看 `interactive-print.html`
里是否有 section 溢出；`validate.py` 会直接报错。

## 图纸内容

**`No subject pixels found`**
抠图是空的：换 `--mode cutout/chibi`，或提供透明 PNG + `--mode none`。

**白色主体消失**
白底上的白色区域被当成背景。改用透明 PNG，或让预处理输出浅蓝/浅灰背景。

**颜色太少 / 细节丢失**
提高 `--max-cells`（如 60→75）和 `--colors`（如 12→15），重跑并看 `preview.png`。

**颜色太杂 / 用量太散**
降低 `--colors`，或提高 `--min-delta`（如 8–10）合并相近色。

**背景格太多**
用 `--pad-cells 0`；或在预处理阶段裁紧主体。背景格可留空不摆。

## 交付

**苹果用户打不开 HTML**
不要发 HTML。发 `pattern-interactive.pdf`（Apple Books / 文件原生支持）。

**PDF 链接点不动**
确认使用的是支持链接注释的阅读器（Apple Books、Files、Adobe、WPS）；
部分极简阅读器会忽略链接。`validate.py` 可确认链接数量。

**文件太大**
交互 PDF 大小与颜色数、格数成正比。14 页 / 13 色约 10MB；
减少 `--colors` 或 `--max-cells` 可显著减小。
