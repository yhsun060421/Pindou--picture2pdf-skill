# -*- coding: utf-8 -*-
"""Subject isolation / chibi conversion through a user-supplied image API."""
from __future__ import annotations

import base64
import io
import json
import mimetypes
import os
import re

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFilter

CHIBI_PROMPT = (
    "Redraw the person in the image as a cute chibi / Q-version sticker character. "
    "Big head, small body, simplified facial features, clean thick outlines, flat "
    "colours suitable for pixel art. Keep the original hairstyle, clothing colours "
    "and recognisable accessories. Full body, front view, centred. "
    "Pure solid white background (#FFFFFF), no shadow, no floor, no text, no border, "
    "no watermark. The subject must not touch the image edges."
)

CUTOUT_PROMPT = (
    "Isolate the main subject of the image and redraw it as a clean flat-colour "
    "sticker. Keep the original style, colours and details. Remove the background "
    "completely and place the subject on a pure solid white background (#FFFFFF). "
    "No shadow, no floor, no text, no border, no watermark. "
    "The subject must not touch the image edges."
)

SENTINEL = (255, 0, 255)


def _endpoint(base, path):
    base = base.rstrip('/')
    if base.endswith('/v1'):
        return base + path
    return base + '/v1' + path


def _decode_response(resp):
    """Return PIL.Image from an image-generation API response."""
    ctype = resp.headers.get('content-type', '')
    if ctype.startswith('image/'):
        return Image.open(io.BytesIO(resp.content)).convert('RGB')
    data = resp.json()
    # OpenAI images
    if isinstance(data, dict) and data.get('data'):
        item = data['data'][0]
        if item.get('b64_json'):
            return Image.open(io.BytesIO(base64.b64decode(item['b64_json']))).convert('RGB')
        if item.get('url'):
            r = requests.get(item['url'], timeout=120)
            r.raise_for_status()
            return Image.open(io.BytesIO(r.content)).convert('RGB')
    # chat-completions style
    if isinstance(data, dict) and data.get('choices'):
        msg = data['choices'][0].get('message', {})
        images = msg.get('images') or []
        for im in images:
            url = (im.get('image_url') or {}).get('url') if isinstance(im, dict) else None
            if url:
                if url.startswith('data:'):
                    return Image.open(io.BytesIO(base64.b64decode(url.split(',', 1)[1]))).convert('RGB')
                r = requests.get(url, timeout=120)
                r.raise_for_status()
                return Image.open(io.BytesIO(r.content)).convert('RGB')
        content = msg.get('content') or ''
        m = re.search(r'data:image/[^;]+;base64,([A-Za-z0-9+/=]+)', content)
        if m:
            return Image.open(io.BytesIO(base64.b64decode(m.group(1)))).convert('RGB')
        m = re.search(r'https?://[^\s)\]]+\.(?:png|jpg|jpeg|webp)', content, re.I)
        if m:
            r = requests.get(m.group(0), timeout=120)
            r.raise_for_status()
            return Image.open(io.BytesIO(r.content)).convert('RGB')
    raise RuntimeError('Image API returned no usable image. Response: '
                       + json.dumps(data, ensure_ascii=False)[:800])


def call_image_api(image_path, prompt, base_url, api_key, model,
                   style='openai', size='1024x1024', timeout=240):
    headers = {'Authorization': f'Bearer {api_key}'}
    if style == 'chat':
        with open(image_path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode()
        mime = mimetypes.guess_type(image_path)[0] or 'image/png'
        msg = {
            'role': 'user',
            'content': [
                {'type': 'text', 'text': prompt},
                {'type': 'image_url',
                 'image_url': {'url': f'data:{mime};base64,{b64}'}},
            ],
        }
        payload = {'model': model, 'messages': [msg], 'stream': False}
        r = requests.post(_endpoint(base_url, '/chat/completions'),
                          headers={**headers, 'Content-Type': 'application/json'},
                          json=payload, timeout=timeout)
        r.raise_for_status()
        return _decode_response(r)

    # OpenAI-compatible images/edits
    with open(image_path, 'rb') as f:
        files = {'image': (os.path.basename(image_path), f, 'image/png')}
        data = {'model': model, 'prompt': prompt, 'n': '1', 'size': size}
        r = requests.post(_endpoint(base_url, '/images/edits'),
                          headers=headers, files=files, data=data, timeout=timeout)
    r.raise_for_status()
    return _decode_response(r)


def remove_background(img, tolerance=26):
    """Turn a near-white background into transparency (border flood fill)."""
    img = img.convert('RGBA')
    alpha = img.getchannel('A')
    if alpha.getextrema()[0] < 250:      # already has transparency: trim margins
        bbox = img.getbbox()
        if not bbox:
            raise RuntimeError('No subject found in transparent image.')
        pad = max(2, int(max(img.size) * 0.015))
        w, h = img.size
        bbox = (max(0, bbox[0] - pad), max(0, bbox[1] - pad),
                min(w, bbox[2] + pad), min(h, bbox[3] + pad))
        return img.crop(bbox)
    rgb = img.convert('RGB').copy()
    w, h = rgb.size
    corners = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    for xy in corners:
        px = rgb.getpixel(xy)
        if min(px) < 255 - tolerance:
            continue
        ImageDraw.floodfill(rgb, xy, SENTINEL, thresh=tolerance)
    rgb_arr = np.asarray(rgb)
    mask = ((rgb_arr[:, :, 0] == 255) & (rgb_arr[:, :, 1] == 0)
            & (rgb_arr[:, :, 2] == 255))
    alpha_arr = np.asarray(img).copy()
    alpha_arr[mask, 3] = 0
    img = Image.fromarray(alpha_arr, 'RGBA')
    # erode alpha by 1px to kill white fringes
    a = img.getchannel('A').filter(ImageFilter.MinFilter(3))
    img.putalpha(a)
    # trim transparent border with a small margin
    bbox = img.getbbox()
    if not bbox:
        raise RuntimeError('No subject found after background removal.')
    pad = max(2, int(max(w, h) * 0.015))
    bbox = (max(0, bbox[0] - pad), max(0, bbox[1] - pad),
            min(w, bbox[2] + pad), min(h, bbox[3] + pad))
    return img.crop(bbox)


def preprocess(input_path, output_path, mode='auto', api=None, keep_bg=False):
    """mode: auto | chibi | cutout | none.  api: dict(base_url, api_key, model, style)."""
    img = Image.open(input_path)
    mode = (mode or 'auto').lower()
    if mode == 'auto':
        # The agent normally decides; default to a clean cutout, never a style change.
        mode = 'cutout'
    if mode == 'none':
        out = img.convert('RGBA')
        if not keep_bg:
            try:
                out = remove_background(out)
            except Exception:
                pass
    else:
        if not api or not api.get('base_url') or not api.get('api_key'):
            raise RuntimeError(
                'Image API is not configured. Set BEAD_IMG_BASE_URL and '
                'BEAD_IMG_API_KEY (and optionally BEAD_IMG_MODEL), or run with '
                '--mode none if the input is already a cutout.')
        prompt = CHIBI_PROMPT if mode == 'chibi' else CUTOUT_PROMPT
        generated = call_image_api(
            input_path, prompt, api['base_url'], api['api_key'],
            api.get('model') or 'gpt-image-1', api.get('style') or 'openai')
        out = remove_background(generated)
    out.save(output_path)
    return mode


def api_from_env():
    return {
        'base_url': os.environ.get('BEAD_IMG_BASE_URL', ''),
        'api_key': os.environ.get('BEAD_IMG_API_KEY', ''),
        'model': os.environ.get('BEAD_IMG_MODEL', 'gpt-image-1'),
        'style': os.environ.get('BEAD_IMG_API_STYLE', 'openai'),
    }
