#!/usr/bin/env python3
"""Validate Scene DSL v1 before rendering; dependency-free."""
import argparse
import json
import math
import re
import sys
from pathlib import Path

TYPES = {
    'text': {'x','y','width','height','text','fontSize','fill'},
    'rect': {'x','y','width','height','fill'},
    'circle': {'x','y','r','fill'},
    'line': {'x','y','x2','y2','stroke'},
}
EXTRA = {'text': {'fontWeight','fontFamily','lineHeight','align','verticalAlign'},
         'rect': {'radius'}, 'circle': {'stroke','strokeWidth'},
         'line': {'strokeWidth','arrowHead'}}
MOTION = {'dx','dy','opacity','scale','rotate'}
class Check:
    def __init__(self):
        self.errors, self.warnings = [], []
    def error(self, where, why):
        self.errors.append(f'ERROR {where}: {why}')
    def warn(self, where, why):
        self.warnings.append(f'WARN {where}: {why}')

def num(x):
    return type(x) in (int,float) and math.isfinite(x)

def audio(ch, value, where, path):
    if value is None: return
    if not isinstance(value, dict) or not isinstance(value.get('file'), str):
        ch.error(where, 'audio must contain a filename'); return
    name = value['file'].replace('\\','/')
    p = Path(name)
    if not name or p.is_absolute() or '..' in p.parts or ':' in name or name.startswith('//'):
        ch.error(where, 'unsafe filename'); return
    root = (path.parent / 'public').resolve()
    asset = (root / p).resolve()
    if not asset.is_relative_to(root): ch.error(where, 'unsafe filename')
    elif not asset.is_file(): ch.error(where, f'missing audio asset: public/{name}')
    if 'volume' in value and (not num(value['volume']) or value['volume'] < 0):
        ch.error(where, 'invalid audio volume')
