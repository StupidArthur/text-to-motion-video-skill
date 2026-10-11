# Video QA checklist

## Gate A — Before browser rendering (automatable)

- [ ] JSON is parseable and scenes/elements conform to DSL v1 (`scripts/validate_scene.py`).
- [ ] Every ID unique in its scope, frame bounds valid, motion keyframes ascending.
- [ ] No negative sizes, NaN/Infinity, opacity outside [0,1], unexpected audio paths.
- [ ] No mandatory asset points to missing `public/` files.
- [ ] Text boxes are plausibly big enough and inside safe margins; these checks are **heuristics**, not typography proof.
- [ ] Total frame count correctly corresponds to expected runtime: sum of scenes / fps.

## Gate B — Storyboard & preview

- [ ] Still frames exported for scene beginning, midpoint and ending.
- [ ] No accidental all-background/near-uniform frames (use `check_frames.py` if Pillow available; intentional transitions can trigger warnings).
- [ ] Titles and captions readable; CJK glyphs present; no clipping or overlap.
- [ ] Typography hierarchy consistent; line length manageable, contrast sufficient.
- [ ] Every shot has a clear focal point, and scene contents appear in the intended order.
- [ ] If no tool can view images, state **“visual QA not performed”** rather than falsely confirming it.

## Gate C — Export & delivery

- [ ] `out/video.mp4` exists and is non-empty.
- [ ] H.264 video track, expected fps/resolution, duration within roughly 2 frames.
- [ ] If audio was required: real audio files exist, audio stream present and tested; do not mark speech as done merely because subtitles exist.
- [ ] User receives source project (JSON + renderer) as well as MP4.
- [ ] Final status lists checks that actually ran and any remaining blockers.

## Failure-response policy

1. **Invalid JSON:** fix schema/coordinates/frame bounds and rerun validator.
2. **npm unavailable:** preserve project and supply `npm install` command; stop before asserting render success.
3. **Browser missing:** install/point Remotion to Chromium if permitted; otherwise report environment limitation.
4. **Missing fonts:** install suitable CJK fonts or revise typography; rerun keyframes.
5. **Audio file missing:** leave out track or obtain explicit audio asset; never fabricate.
6. **Frame appears blank:** verify `visibleFrom`, `visibleUntil`, opacity keyframes and scene-local timeline; check intentional blank transitions.
7. **Visual overflow:** adjust positions, box width, font size or break into another scene; do not hide by shrinking all elements.

## Tests and evidence

For reproducible delivery, record: `video.json` checksum, installed npm dependency versions, validator results, rendered screenshot paths, `ffprobe` metadata and whether manual/visual review occurred.
