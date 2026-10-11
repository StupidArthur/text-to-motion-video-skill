#!/usr/bin/env python3
"""Use ffprobe to assert that a rendered MP4 matches video.json metadata.

Requires an ffprobe executable on PATH. Does not inspect audiovisual aesthetics.
"""
import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video_json", type=Path)
    parser.add_argument("mp4", type=Path)
    args = parser.parse_args()
    if not args.mp4.is_file() or args.mp4.stat().st_size <= 0:
        print(f"ERROR expected non-empty MP4 at {args.mp4}", file=sys.stderr)
        return 1
    if not shutil.which("ffprobe"):
        print("ERROR ffprobe is unavailable; install FFmpeg or provide a path to ffprobe", file=sys.stderr)
        return 2
    try:
        spec = json.loads(args.video_json.read_text(encoding="utf-8"))
        result = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries",
            "stream=index,codec_type,codec_name,width,height,r_frame_rate:format=duration",
            "-of", "json", str(args.mp4)
        ], check=True, capture_output=True, text=True)
        probe = json.loads(result.stdout)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"ERROR unable to inspect video: {exc}", file=sys.stderr)
        return 1
    meta = spec["meta"]
    streams = probe.get("streams", [])
    video_stream = next((st for st in streams if st.get("codec_type") == "video"), None)
    audio_stream = next((st for st in streams if st.get("codec_type") == "audio"), None)
    errors = []
    if not video_stream:
        errors.append("no video stream")
    else:
        if (video_stream.get("width"), video_stream.get("height")) != (meta["width"], meta["height"]):
            errors.append(f"resolution mismatch: got {video_stream.get('width')}x{video_stream.get('height')}")
        rate = video_stream.get("r_frame_rate", "0/1")
        try:
            numerator, denominator = map(int, rate.split("/"))
            actual_fps = numerator / denominator
            if not math.isclose(actual_fps, meta["fps"], abs_tol=0.03):
                errors.append(f"fps mismatch: got {actual_fps:.3f}, expected {meta['fps']}")
        except (ValueError, ZeroDivisionError):
            errors.append(f"unable to parse fps {rate!r}")
        if video_stream.get("codec_name") != "h264":
            errors.append(f"expected H.264, got {video_stream.get('codec_name')}")
    expected_duration = sum(scene["durationFrames"] for scene in spec["scenes"]) / meta["fps"]
    try:
        actual_duration = float(probe.get("format", {}).get("duration", 0))
    except (ValueError, TypeError):
        actual_duration = 0
    tolerance = max(2 / meta["fps"], 0.10)
    if abs(expected_duration - actual_duration) > tolerance:
        errors.append(f"duration mismatch: got {actual_duration:.3f}s, expected {expected_duration:.3f}s ±{tolerance:.3f}s")
    expects_audio = bool(meta.get("music") or any(scene.get("audio") for scene in spec["scenes"]))
    if expects_audio and audio_stream is None:
        errors.append("audio requested but output has no audio stream")
    print(f"MP4: {args.mp4} ({args.mp4.stat().st_size:,} bytes); duration={actual_duration:.3f}s; "
          f"resolution={video_stream.get('width') if video_stream else '?'}x{video_stream.get('height') if video_stream else '?'}; "
          f"video={video_stream.get('codec_name') if video_stream else '?'}; audio={'yes' if audio_stream else 'no'}")
    for problem in errors:
        print("ERROR", problem, file=sys.stderr)
    print(f"RESULT: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
