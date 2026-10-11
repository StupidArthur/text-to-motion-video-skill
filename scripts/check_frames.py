#!/usr/bin/env python3
"""Heuristic check for very low-information storyboard PNG files.

Requires Pillow (`python3 -m pip install Pillow`). This does NOT visually judge composition.
"""
import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("frames_dir", type=Path)
    args = parser.parse_args()
    try:
        from PIL import Image, ImageStat
    except ImportError:
        print("ERROR Pillow is not installed. Install with: python3 -m pip install Pillow", file=sys.stderr)
        return 2
    files = sorted(args.frames_dir.glob("*.png"))
    if not files:
        print(f"ERROR no PNG files in {args.frames_dir}", file=sys.stderr)
        return 1
    warnings = 0
    for path in files:
        with Image.open(path) as img:
            gray = img.convert("L").resize((160, 90))
            stddev = ImageStat.Stat(gray).stddev[0]
            extrema = gray.getextrema()
            if stddev < 7:
                warnings += 1
                print(f"WARN {path.name}: low brightness variance (stddev={stddev:.2f}, extrema={extrema}). Could be intentional.")
            else:
                print(f"OK   {path.name}: brightness variance stddev={stddev:.2f}")
    print(f"RESULT: {len(files)} images scanned; {warnings} low-information warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
