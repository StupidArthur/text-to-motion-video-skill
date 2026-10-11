#!/usr/bin/env python3
"""Validate the documented Scene DSL v1. Standard library only.

Usage: python3 scripts/validate_scene.py path/to/video.json
Exit 0 = valid (possibly warnings); exit 1 = invalid.
"""
import argparse
import json
import math
import re
import sys
import unicodedata
from pathlib import Path

KNOWN_TYPES = {"text", "rect", "circle", "line"}
MOTION_PROPERTIES = {"dx", "dy", "opacity", "scale", "rotate"}
COMMON_ELEMENT_FIELDS = {"id", "type", "visibleFrom", "visibleUntil", "motion"}
ELEMENT_FIELDS = {
    "text": COMMON_ELEMENT_FIELDS | {"x", "y", "width", "height", "text", "fill", "fontSize", "fontWeight", "fontFamily", "lineHeight", "align", "verticalAlign"},
    "rect": COMMON_ELEMENT_FIELDS | {"x", "y", "width", "height", "fill", "radius"},
    "circle": COMMON_ELEMENT_FIELDS | {"x", "y", "r", "fill", "stroke", "strokeWidth"},
    "line": COMMON_ELEMENT_FIELDS | {"x", "y", "x2", "y2", "stroke", "strokeWidth", "arrowHead"},
}
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


class Check:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, path, message):
        self.errors.append(f"ERROR {path}: {message}")

    def warn(self, path, message):
        self.warnings.append(f"WARN  {path}: {message}")


def is_number(x):
    return type(x) in (int, float) and math.isfinite(x)


def is_int(x):
    return type(x) is int


def get_number(ch, obj, key, path, *, positive=False, nonnegative=False, required=True):
    if key not in obj and not required:
        return None
    value = obj.get(key)
    if not is_number(value):
        ch.error(path, f"{key} must be a finite number")
        return None
    if positive and value <= 0:
        ch.error(path, f"{key} must be > 0")
    if nonnegative and value < 0:
        ch.error(path, f"{key} must be >= 0")
    return value


def check_id(ch, value, path):
    if not isinstance(value, str) or not ID_PATTERN.fullmatch(value):
        ch.error(path, "id must match [A-Za-z0-9][A-Za-z0-9_-]*")


def check_audio(ch, audio, path, project_dir):
    if audio is None:
        return
    if not isinstance(audio, dict):
        ch.error(path, "audio reference must be an object")
        return
    unexpected = set(audio) - {"file", "volume"}
    if unexpected:
        ch.error(path, f"unsupported audio fields: {', '.join(sorted(unexpected))}")
    filename = audio.get("file")
    if not isinstance(filename, str) or not filename.strip():
        ch.error(path, "file must be a nonempty path relative to public/")
    else:
        normalized = filename.replace("\\", "/")
        part = Path(normalized)
        if part.is_absolute() or any(p in ("..", "") for p in part.parts) or ":" in normalized or normalized.startswith("//"):
            ch.error(path, "unsafe filename; use relative paths under public/")
        else:
            asset_path = (project_dir / "public" / part).resolve()
            public_root = (project_dir / "public").resolve()
            if not asset_path.is_relative_to(public_root):
                ch.error(path, "asset escapes public/ directory")
            elif not asset_path.is_file():
                ch.error(path, f"missing audio asset: public/{normalized}")
    volume = get_number(ch, audio, "volume", path, nonnegative=True, required=False)
    if volume is not None and volume > 1:
        ch.warn(path, "volume > 1 may clip audio")


def check_motion(ch, element, path, duration):
    points = element.get("motion", [])
    if not isinstance(points, list):
        ch.error(path, "motion must be a list")
        return
    last_frame = -1
    for index, point in enumerate(points):
        here = f"{path}.motion[{index}]"
        if not isinstance(point, dict):
            ch.error(here, "motion entry must be an object")
            continue
        frame = point.get("frame")
        if not is_int(frame) or not (0 <= frame < duration):
            ch.error(here, f"frame must be an integer in [0,{duration - 1}]")
        elif frame <= last_frame:
            ch.error(here, "motion frames must increase strictly")
        else:
            last_frame = frame
        active = [key for key in MOTION_PROPERTIES if key in point]
        if not active:
            ch.error(here, "keyframe must declare at least one motion property")
        unknown = set(point) - (MOTION_PROPERTIES | {"frame"})
        if unknown:
            ch.error(here, f"unsupported properties: {', '.join(sorted(unknown))}")
        for key in active:
            value = point[key]
            if not is_number(value):
                ch.error(here, f"{key} must be a finite number")
            elif key == "opacity" and not 0 <= value <= 1:
                ch.error(here, "opacity must be between 0 and 1")
            elif key == "scale" and value < 0:
                ch.error(here, "scale must be nonnegative")


def validate_element(ch, el, path, duration, width, height):
    if not isinstance(el, dict):
        ch.error(path, "element must be an object")
        return
    check_id(ch, el.get("id"), path + ".id")
    kind = el.get("type")
    if not isinstance(kind, str) or kind not in KNOWN_TYPES:
        ch.error(path, f"unsupported element type {kind!r}; expected {sorted(KNOWN_TYPES)}")
        return
    unexpected = set(el) - ELEMENT_FIELDS[kind]
    if unexpected:
        ch.error(path, f"unsupported {kind} fields: {', '.join(sorted(unexpected))}")
    if kind in ("text", "rect"):
        for key in ("x", "y", "width", "height"):
            get_number(ch, el, key, path, positive=key in ("width", "height"))
    elif kind == "circle":
        for key in ("x", "y", "r"):
            get_number(ch, el, key, path, positive=key == "r")
    elif kind == "line":
        for key in ("x", "y", "x2", "y2"):
            get_number(ch, el, key, path)
        if "arrowHead" in el and type(el["arrowHead"]) is not bool:
            ch.error(path, "arrowHead must be boolean")
    if kind in ("text", "rect", "circle"):
        if not isinstance(el.get("fill"), str) or not el["fill"].strip():
            ch.error(path, "fill must be nonempty CSS color string")
    if kind == "line" or (kind == "circle" and "stroke" in el):
        if not isinstance(el.get("stroke"), str) or not el["stroke"].strip():
            ch.error(path, "stroke must be nonempty CSS color string")
    if "strokeWidth" in el:
        get_number(ch, el, "strokeWidth", path, nonnegative=True)
    if "radius" in el:
        get_number(ch, el, "radius", path, nonnegative=True)
    if kind == "text":
        if not isinstance(el.get("text"), str) or not el["text"].strip():
            ch.error(path, "text must be a nonempty string")
        get_number(ch, el, "fontSize", path, positive=True)
        weight = get_number(ch, el, "fontWeight", path, required=False)
        if weight is not None and not (100 <= weight <= 900):
            ch.error(path, "fontWeight must be between 100 and 900")
        get_number(ch, el, "lineHeight", path, positive=True, required=False)
        if el.get("align", "left") not in ("left", "center", "right"):
            ch.error(path, "align must be left, center or right")
        if el.get("verticalAlign", "top") not in ("top", "middle", "bottom"):
            ch.error(path, "verticalAlign must be top, middle or bottom")
        if "fontFamily" in el and (not isinstance(el["fontFamily"], str) or not el["fontFamily"].strip()):
            ch.error(path, "fontFamily must be nonempty string")
        x, y, w, h, fs = (el.get(k) for k in ("x", "y", "width", "height", "fontSize"))
        if all(is_number(v) for v in (x, y, w, h, fs)) and w > 0 and h > 0:
            safe = min(width, height) * 0.06
            if x < safe or y < safe or x + w > width - safe or y + h > height - safe:
                ch.warn(path, "text box crosses 6% recommended safe margin")
            if isinstance(el.get("text"), str):
                # Approximate CJK character cells; not a browser text measurement.
                lines = el["text"].split("\n")
                units = [sum(1.0 if unicodedata.east_asian_width(ch_) in "WF" else 0.56 for ch_ in line) for line in lines]
                estimated_lines = sum(max(1, math.ceil((line_units * fs) / w)) for line_units in units)
                estimated_h = estimated_lines * fs * (el.get("lineHeight", 1.22) if is_number(el.get("lineHeight", 1.22)) else 1.22)
                if estimated_h > h * 1.15:
                    ch.warn(path, f"possible text clipping; estimated {estimated_lines} lines need ~{estimated_h:.0f}px but box is {h}px")
    for key in ("visibleFrom", "visibleUntil"):
        if key in el and (not is_int(el[key]) or el[key] < 0 or el[key] > duration):
            ch.error(path, f"{key} must be an integer in [0, {duration}]")
    visible_from = el.get("visibleFrom", 0)
    visible_until = el.get("visibleUntil", duration)
    if is_int(visible_from) and is_int(visible_until) and visible_from >= visible_until:
        ch.error(path, "visibleFrom must be less than visibleUntil")
    check_motion(ch, el, path, duration)
    # Non-text elements may intentionally enter from offscreen; flag only total offscreen.
    if kind == "rect" and all(is_number(el.get(k)) for k in ("x", "y", "width", "height")):
        if el["x"] >= width or el["y"] >= height or el["x"] + el["width"] <= 0 or el["y"] + el["height"] <= 0:
            ch.warn(path, "rectangle is entirely off canvas at base position")


def validate(document, video_path):
    ch = Check()
    if not isinstance(document, dict):
        ch.error("$", "JSON root must be an object")
        return ch
    top_unknown = set(document) - {"meta", "scenes", "characterAssets"}
    if top_unknown:
        ch.error("$", f"unsupported root fields: {', '.join(sorted(top_unknown))}")
    meta = document.get("meta")
    if not isinstance(meta, dict):
        ch.error("$.meta", "meta must be an object")
        return ch
    meta_unknown = set(meta) - {"title", "width", "height", "fps", "background", "music"}
    if meta_unknown:
        ch.error("$.meta", f"unsupported meta fields: {', '.join(sorted(meta_unknown))}")
    if not isinstance(meta.get("title"), str) or not meta["title"].strip():
        ch.error("$.meta.title", "must be a nonempty string")
    width = meta.get("width")
    height = meta.get("height")
    fps = meta.get("fps")
    for key, value in (("width", width), ("height", height), ("fps", fps)):
        if not is_int(value) or value <= 0:
            ch.error(f"$.meta.{key}", "must be a positive integer")
    if "background" in meta and not isinstance(meta["background"], str):
        ch.error("$.meta.background", "background must be a color string")
    check_audio(ch, meta.get("music"), "$.meta.music", video_path.parent)
    scenes = document.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        ch.error("$.scenes", "must be a nonempty list")
        return ch
    seen_scene_ids = set()
    total_frames = 0
    for i, scene in enumerate(scenes):
        here = f"$.scenes[{i}]"
        if not isinstance(scene, dict):
            ch.error(here, "scene must be an object")
            continue
        scene_unknown = set(scene) - {"id", "durationFrames", "background", "audio", "elements", "characters", "interactions", "camera"}
        if scene_unknown:
            ch.error(here, f"unsupported scene fields: {', '.join(sorted(scene_unknown))}")
        scene_id = scene.get("id")
        check_id(ch, scene_id, here + ".id")
        if isinstance(scene_id, str):
            if scene_id in seen_scene_ids:
                ch.error(here, f"duplicate scene id {scene_id!r}")
            seen_scene_ids.add(scene_id)
        duration = scene.get("durationFrames")
        if not is_int(duration) or duration <= 0:
            ch.error(here, "durationFrames must be a positive integer")
            continue
        total_frames += duration
        if "background" in scene and not isinstance(scene["background"], str):
            ch.error(here, "background must be a CSS color string")
        check_audio(ch, scene.get("audio"), here + ".audio", video_path.parent)
        elements = scene.get("elements")
        if not isinstance(elements, list):
            ch.error(here, "elements must be a list")
            continue
        ids = set()
        for j, el in enumerate(elements):
            ep = f"{here}.elements[{j}]"
            if isinstance(el, dict) and isinstance(el.get("id"), str):
                if el["id"] in ids:
                    ch.error(ep, f"duplicate element id {el['id']!r}")
                ids.add(el["id"])
            validate_element(ch, el, ep, duration, width if is_int(width) and width > 0 else 1920,
                             height if is_int(height) and height > 0 else 1080)
        if not elements and not scene.get("characters"):
            ch.warn(here, "scene contains zero elements and characters (may be intentional)")
    from validate_characters import check_v2
    check_v2(ch, document)
    if is_int(fps) and fps > 0:
        print(f"VIDEO: {len(scenes)} scenes, {total_frames} frames, {total_frames / fps:.2f}s, {width}x{height} @ {fps}fps")
    return ch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video_json", type=Path)
    args = parser.parse_args()
    try:
        document = json.loads(args.video_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR unable to read JSON: {exc}", file=sys.stderr)
        return 1
    ch = validate(document, args.video_json.resolve())
    for item in ch.warnings:
        print(item)
    for item in ch.errors:
        print(item, file=sys.stderr)
    print(f"RESULT: {len(ch.errors)} error(s), {len(ch.warnings)} warning(s)")
    return 1 if ch.errors else 0


if __name__ == "__main__":
    sys.exit(main())
