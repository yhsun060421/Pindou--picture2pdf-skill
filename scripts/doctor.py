#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check that the skill can run out of the box."""
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
errors = []

if sys.version_info < (3, 10):
    errors.append(f'Python 3.10+ required, found {sys.version.split()[0]}')

for mod in ['PIL', 'numpy', 'fitz', 'requests']:
    try:
        __import__(mod)
    except Exception as e:
        errors.append(f'missing dependency {mod}: {e}')

try:
    from beadlib.interactive_pdf import find_chrome
    print('Chrome:', find_chrome())
except Exception as e:
    errors.append(str(e))

palette = os.path.join(ROOT, 'references', 'palette-mard221.json')
if not os.path.exists(palette):
    errors.append('missing references/palette-mard221.json')
else:
    data = json.load(open(palette, encoding='utf-8'))
    if data.get('count') != 221:
        errors.append(f"palette expected 221 colours, got {data.get('count')}")

if not os.path.exists(os.path.join(ROOT, 'examples', 'sample.png')):
    errors.append('missing examples/sample.png')

if errors:
    print('[ERROR] doctor found problems:')
    for e in errors:
        print(' -', e)
    sys.exit(1)
print('[OK] doctor OK - Python, dependencies, Chrome, palette and sample are ready.')
