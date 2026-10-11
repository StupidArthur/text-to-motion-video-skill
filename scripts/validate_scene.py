#!/usr/bin/env python3
"""Validate Scene DSL v1 before rendering."""
import argparse
import json
import sys
from pathlib import Path
from validator_root import validate

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("video_json",type=Path)
    args=parser.parse_args()
    try:
        doc=json.loads(args.video_json.read_text(encoding="utf-8"))
    except (OSError,ValueError) as exc:
        print("ERROR",exc,file=sys.stderr)
        return 1
    ch=validate(doc,args.video_json.resolve())
    for item in ch.warnings: print(item)
    for item in ch.errors: print(item,file=sys.stderr)
    print(f"RESULT: {len(ch.errors)} error(s), {len(ch.warnings)} warning(s)")
    return 1 if ch.errors else 0

if __name__ == "__main__":
    sys.exit(main())
