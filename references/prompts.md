# 图像预处理与提示词

## API 配置

```bash
BEAD_IMG_BASE_URL=https://api.openai.com     # 或兼容代理，可带 /v1
BEAD_IMG_API_KEY=sk-...
BEAD_IMG_MODEL=gpt-image-1                   # 或你的服务商模型名
BEAD_IMG_API_STYLE=openai                    # openai | chat
```

- `openai`：调用 `POST {base}/v1/images/edits`，multipart 上传图片。
- `chat`：调用 `POST {base}/v1/chat/completions`，把图片以 data URL 放入消息。
- 响应支持 `data[0].b64_json`、`data[0].url`、chat 的 `images[0].image_url.url`、
  content 中的 data URI / 图片 URL。
- 密钥只从环境变量读取，不落盘、不打印、不提交。

## 人物 → Q 版（chibi）

用于 `--mode chibi`。目标不是“滤镜”，而是重新画成适合像素化的 Q 版贴纸：

```text
Redraw the person in the image as a cute chibi / Q-version sticker character.
Big head, small body, simplified facial features, clean thick outlines, flat
colours suitable for pixel art. Keep the original hairstyle, clothing colours
and recognisable accessories. Full body, front view, centred.
Pure solid white background (#FFFFFF), no shadow, no floor, no text, no border,
no watermark. The subject must not touch the image edges.
```

## 卡通 / 物体 / 其他 → 抠主体

用于 `--mode cutout`：

```text
Isolate the main subject of the image and redraw it as a clean flat-colour
sticker. Keep the original style, colours and details. Remove the background
completely and place the subject on a pure solid white background (#FFFFFF).
No shadow, no floor, no text, no border, no watermark.
The subject must not touch the image edges.
```

## 提示词要点

- **纯白背景**便于边缘漫水填充移除；不要让主体接触画布边缘。
- **全身/完整主体**：否则会被裁掉手脚。
- **平涂、粗轮廓**：像素化后更清晰。
- **保留服装/发色**：避免模型“自由发挥”。
- **不要文字/水印/边框**：这些会被当成图案。
- 若模型支持尺寸，使用方形 1024×1024 或与原图接近的比例。

## 已经抠好的图

`--mode none`：直接把输入当作主体。会尝试移除白底；加 `--keep-bg` 可保留。
透明 PNG 效果最好。

## 失败排查

- 返回 401/403：检查 key 与 base URL。
- 返回 404：base URL 可能已经带 `/v1`，或服务商路径不同；脚本会兼容两种。
- 返回无图片：日志里会打印响应前 800 字符，按服务商格式调整 `--api-style`。
- 主体被裁：在提示词中强调 full body / do not crop，并留出边距。
