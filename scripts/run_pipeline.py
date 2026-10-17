#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from beadlib.pipeline import build_parser, run

if __name__ == '__main__':
    try:
        run(build_parser().parse_args())
    except RuntimeError as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(2)
