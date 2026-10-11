---
name: text-to-motion-video
description: Create scripted narrative videos, original SVG scenes, characters, explainer motion graphics and editable MP4 using text-only code agents; supports external director shot scripts, on-demand artwork, explicit acceptance criteria, and Remotion rendering. Use when the user asks to create a video, motion graphics, animated SVG, data explainer, animated subtitles, or programmatic text-to-video; especially when no image/video generation model is available. 通过纯文本 Code Agent 生成科普、信息图、文字动画与 MP4。
compatibility: Requires a code execution agent, Node.js 20+, npm, Python 3.10+, and the ability to install npm dependencies and render in Chromium. ffprobe is optional for final verification.
---

# Text → Motion Video (React SVG + Remotion)

**Goal:** Turn a user's natural-language brief into a reproducible MP4 **without requiring an image-generation or video-generation model**. Build scenes as structured JSON, render React SVG and HTML text deterministically at each frame, check keyframes, revise and export.

## Mandatory principles

1. **A video is a function of frame index**, never of wall-clock time. No `setTimeout`, CSS keyframe autoplay, `requestAnimationFrame`, random values without fixed seeds, or screen recording for final export.
2. Prefer the bundled **JSON scene DSL** to unconstrained hand-written SVG. Do not rewrite the renderer for routine projects. Extend TSX components only if the DSL genuinely cannot express an element.
3. Preserve **editable project sources**, not just `mp4`. Never say a render succeeded before confirming the output exists and checks pass.
4. **Text-only model** does not mean visual inspection. Run automated structural checks; if screenshots cannot be visually examined by this agent, explicitly state that the visual pass was not performed. Do not pretend to see rendered frames.
5. No invented narration, music, fonts, image files, or successful tool runs. Use real files in `public/`, or leave the track out. Obtain permission and appropriate rights to use third-party assets.
6. Respect a consistent director-provided visual bible: fixed character identities, reusable palette/typography rules, safe margins, readable timing, and a deliberate focal point per shot. Do not impose a generic palette over the script.

## Trigger examples

- “做一个 15 秒的视频讲 Transformer”, “文字转动画”, “SVG 动效视频”, “自动生成信息图视频”, “Make a motion explainer”, “Render an animated MP4 from text.”
- If the user instead requests photo-realistic live-action footage, explain that this Skill produces vector-led motion graphics rather than realistic filmed scenes; augment with licensed footage only when suitable assets and tools are available.

## Workflow (run in order)

### 1. Analyze and plan

Extract purpose, audience, aspect ratio, total duration, fps, language, visual style, narration/audio needs and delivery path. If absent, use **1920×1080, 30 fps, 12 seconds, Simplified Chinese, dark minimal vector graphics, no audio**. Do not stall on optional preferences.

Create a compact shot plan before coding. For each shot state: `durationFrames`, one communication goal, 1–5 visual elements, intended motion, on-screen copy and any required narration. Budget reading speed and allow key text to remain visible for at least ~1.5 seconds when practical. Scenes are **sequential hard cuts** in this starter.

### 2. Initialize the project

The skill root contains `assets/remotion-starter/`, which is a **project template**, not the output destination. Copy it to a writable project directory, e.g.:

```bash
cp -R assets/remotion-starter ./motion-video
cd motion-video
npm install
```

Run from the skill root for `cp`; adapt Windows file-copy commands when necessary. Avoid overwriting an existing project. `npm install` requires access to the package registry or a prepared dependency cache. Use one matching version for all Remotion packages. Read `references/SCENE_DSL.md` for the contract before editing the timeline.

### 3. Generate/edit video.json

Write or replace `motion-video/video.json` following `references/SCENE_DSL.md` and `assets/remotion-starter/video.json`. Scenes run sequentially; the sum of `durationFrames` is the total duration. All scene element `motion[].frame`, `visibleFrom` and `visibleUntil` are **scene-local** frame numbers. Use `dx/dy` for relative motion rather than rewriting base coordinates.

- Compose from `text`, `rect`, `circle`, `line`; combine elements for diagrams, arrows, charts, progress indicators, motion titles.
- Prefer SVG-native elements for shapes and HTML text inside SVG `foreignObject` for wrapping, CJK typography and line height.
- Use `motion` arrays for frame-controlled translation, opacity, rotation and scale. `motion` values hold their last value.
- Turn spoken-word transcripts into timed on-screen `text` elements if subtitles are needed; the JSON DSL does **not** synthesize speech.
- Audio is optional. If user provides/generated audio legitimately, copy into `motion-video/public/`, reference it using `audio.file` or `meta.music.file`, and align narration duration with the scene.

### 4. Validate before rendering (required)

From the **skill root**:

```bash
python3 scripts/validate_scene.py ./motion-video/video.json
```

From any working directory, point the script to the actual JSON path. Fix all **ERRORS** before continuing. Inspect **WARNINGS** (text overflow is heuristic). Never delete warnings by lowering checking strictness without reason.

### 5. Preview and sample keyframes

From `motion-video/`:

```bash
npm run studio
npm run storyboard
```

`npm run storyboard` outputs first/middle/last frames per scene to `out/storyboard/` using deterministic `remotion still --frame`. Review all resulting frames if image viewing is available. For a **text-only** agent, rely on validator and optionally `python3 <SKILL_ROOT>/scripts/check_frames.py out/storyboard` (requires Pillow) to detect nearly-uniform frames; this is not a substitute for visual aesthetic review.

Check opening frame, each scene midpoint and end, title readability, line wraps, edges, background contrast, timing, transitions and missing assets. If problems arise, edit JSON and repeat steps 4–5. Limit unattended revision to three passes; report residual issues rather than silently inventing quality.

### 6. Render and verify

From `motion-video/`:

```bash
npm run render
```

Expected output: `motion-video/out/video.mp4` (H.264/yuv420p). Remotion renders frame-deterministically rather than making a live screen recording.

If `ffprobe` is installed, validate metadata from the skill root:

```bash
python3 scripts/check_video.py ./motion-video/video.json ./motion-video/out/video.mp4
```

Verify file exists, non-zero size, expected resolution, approximately expected duration and fps, and audio if one was requested. Use the visual/keyframe review as an additional quality gate if accessible. If npm/browser installation or rendering fails, report the **exact blocked stage**, preserve sources and provide reproducible run commands; never claim the MP4 was created.

### 7. Deliver

Return paths to **both** `out/video.mp4` and the editable source project. In the final response say what was actually checked: JSON validation, rendered sample frames, MP4 metadata, and optional visual review. Describe any skipped step accurately.

## Operating guidance

- Read `references/SCENE_DSL.md` whenever adding/changing scene elements or animation.
- Read `references/QUALITY_CHECKLIST.md` during storyboard, review and final delivery.
- Look at `assets/remotion-starter/src/Video.tsx` only when a primitive or behavior needs extending.
- Keep the generated work inside the user's project, not inside the installed skill directory.
- Prefer to fix timing by modifying `durationFrames` and motion frames, not by changing the global fps.
- If advanced functionality (morphing paths, 3D, camera, nested timelines, automated TTS or crossfades) is needed, implement an **explicit renderer extension** and document its schema; do not use fields that the bundled renderer silently ignores.
- Do not import arbitrary scripts, remote SVG or HTML without reviewing trust and rights. Do not interpolate unsanitized external markup as raw HTML.

## Command reference

```bash
# SKILL_ROOT is the folder containing SKILL.md
cp -R "$SKILL_ROOT/assets/remotion-starter" ./motion-video
cd ./motion-video && npm install
python3 "$SKILL_ROOT/scripts/validate_scene.py" video.json
npm run storyboard  # frame PNGs under out/storyboard/
python3 "$SKILL_ROOT/scripts/check_frames.py" out/storyboard # optional Pillow
npm run render       # out/video.mp4
python3 "$SKILL_ROOT/scripts/check_video.py" video.json out/video.mp4  # optional ffprobe
```

## V2 — animated people, animals, and scripted interactions

The bundled starter now supports both **V1 motion graphics** and **V2 procedural
cartoon characters**. Before authoring a character story:

1. Read the V2 section of `references/SCENE_DSL.md`. Define `characterAssets` at
   the document root (`human` or `dog`), then character instances inside scenes.
2. Create a **character bible** (names, species, palette, sizes, facing).
   Reuse those definitions across all scenes to keep identities consistent.
3. Break the narrative into beats: establish → initiate → approach → react → contact → resolve.
   Each action takes scene-local frames and does not run in wall-clock time.
4. Put `characters[].actions` (`walk`, `run`, `wave`, `sit`, `reach`,
   `pawRaise`, `blink`, `headTurn`, `tailWag`) and `characters[].motion` into
   scenes; use `interactions[]` for exact hand/paw contact points.
5. For high-five interactions specify both actor IDs, the contact frame and a
   reachable shared world-space target. Run validation and `npm run test:rig`
   before visual inspection. The numeric test verifies contact precision.
6. Use `camera` keyframes for restrained pans/zooms. Avoid camera motion that
   hides the interacting limbs. Extract the contact frame with Remotion still.
7. Render and review at scene boundaries and key action frames. If the agent is
   text-only, report that manual visual review is pending rather than inventing it.

Starter V2 example: an 18-second scene with a girl waving to a dog, the dog
running and sitting, and a two-character high-five. V1-only examples are kept
in `examples/v1-video.json` and can still be rendered by replacing video.json
with the V1 example. For an immediate character demo:

```bash
cd assets/remotion-starter
npm install
npm run test:rig
npm run storyboard
npm run render
```

**Current scope:** the included rigs are stylized procedural SVG humanoid and
puppy characters. This is not a photorealistic video model or a general importer
for arbitrary PNG/video/Lottie rigs. MP4 interactions are scripted, not
interactive with the viewer at playback time. Full 2D rig import, user-defined
skeletons, automatic lip sync and physics require subsequent features.

## V2.1 — full 2D articulated stories with imported SVG parts and props

**This section supersedes previous V2 scope descriptions:** the bundled Skill now also implements *declarative custom bone rigs*, layer-specific SVG images, hierarchical joint transforms, weighted local joint tracks, generic two-bone IK, root moveTo/head lookAt/reachTo behaviors, deterministic planted-stance motion for built-in walkers, world-anchor prop pickup/release, and semantic storyboard frames. It does **not** promise photorealistic 3D, arbitrary skinned skeleton binary imports, collision physics or clickable MP4 players.

Workflow for complex character videos:

1. Ask the user for the story beats, number/kind of characters, dialogue, visual style, duration, aspect ratio and any **optional** reference/part SVG/audio files. When no art is provided, make stylized SVG part assets in `public/` yourself (or compose path/rect/ellipse bodies in the JSON).
2. Create a character bible for each actor: colors, proportions, species, named body parts, anchors, facial expressions. Reuse assets across scenes. Author characters using `characterAssets[].kind='custom'`, bones and `ikChains` according to `references/SCENE_DSL.md` when default human/dog does not suffice.
3. Split story into shots. For each character write ordered root `motion` plus `jointActions` with action-local keyed angles. Use the builtin human/dog `actions` when appropriate; add semantic `behaviors` only if supported.
4. For multi-actor touches/handshakes/high-fives define reachable world targets, contact frames and the correct hand/paw anchor; verify using numeric IK tests. Do not animate just a full-body flat SVG if articulated motion is requested.
5. For held objects define `propAssets`, scene `props` and `attachments` with attach/detach intervals. Account for the possibility of a snap when the object is picked up.
6. Run schema tests and storyboard extraction at every beat and contact frame. **Inspect actual rasterized keyframes if your agent has image viewing.** If only text-based checks are possible, report the limitation.
7. Render with Remotion, verify MP4 with `ffprobe`, retain editable project. If npm/browser is unavailable, deliver the correct project and explicit blocker rather than claim successful video generation.

Commands: `python3 scripts/test_advanced.py` from Skill root; inside starter run `npm run test:rig`, `npm run demo:custom`, `npm run storyboard`, `npm run render`. See the full custom-rig demo at `examples/custom-rig/`. Each unsupported request (3D, advanced cloth, arbitrary body mesh retargeting) requires a deliberate new capability; do not invent existing support.

## V3 — script-driven production with on-demand artwork (preferred for narrative video)

**Core principle:** the director script determines *what* must be on screen; the local Code Agent decides *how* to draw, compose and animate it. Do **not** use the default human/dog rig as a substitute for a novel character simply because it is convenient. Existing character rigs, SVG primitives and prop libraries are optional implementation tools, not the screenplay.

When handed a high-detail external screenplay, **read `workflows/scripted-production.md` first**. Treat `storyboard.json`, `visual-bible.json` and `acceptance.json` as a contract. The schema files are in `contracts/`. Create additional assets **from the specific shot requirements**, not by enumerating a fixed asset catalog. Preserve asset origin/provenance and stable identities. A non-existent referenced asset is a production error, not a request to invent its existence.

### Mandatory execution sequence

1. **Parse & audit the contract**: shot timeline must be contiguous; each shot has before/after story state, at least one action beat, framing, explicit asset needs and acceptance rules. For full-length pieces, flag monotone shot types and repeated “walking” beats before generating. Ask the director to revise unrealistic shot requirements rather than pretending a low-cost implementation is equivalent.
2. **Build art on demand**: generate new SVG path groups, layered artwork or other permitted files for the current shot. For a red-hooded child, create the hood, face, cape, hands and boots; for an unknown cabin, create its perspective, doorway, lighting and parts. Keep a canonical style/character definition for shot-to-shot continuity. Do not silently replace novel subjects with generic circles or built-in animals.
3. **Compile verified resources**: use `scripts/production_pipeline.py` to check contracts/paths/frames and assemble a compatible Remotion `video.json`; new external SVG/PNG/WebP/JPEG layers are rendered by `src/ShotLayers.tsx`. Existing V1/V2 scenes still render unchanged.
4. **Verify action states**: before render, test timeline/asset geometry; after rendering, capture action-key frames and compare the visible state to the acceptance contract. If a character must open a door and enter a house, merely moving the character towards a static house **fails** the shot. The scene must visibly show the door changing state and the character entering.
5. **Gate visual QA**: `shot_review.py init` starts **all** checks as pending. Each visual check must have actual screenshot evidence, reviewer identity, and a recorded judgment. If only text capabilities exist, keep the visual requirements pending and explicitly say visual QA was **not** done. Never invent a pass. After approved shots, render the final synchronized video and verify technical metadata.
6. **Preserve human/strong-model intent**: no stealth script rewrites, no repeated walking filler, no claim of cinema-quality art from SVG-only output, and no false declarations of tool access.

See `examples/scripted-cottage/` for an entirely **newly drawn** red-cloaked character and cottage scene. It does not use a preinstalled “Little Red Riding Hood” asset. The demo is illustrative, not a guarantee of professional picture-book quality.

```bash
# From Skill root. All 3 contracts and their public/ files already exist in example.
python3 scripts/production_pipeline.py examples/scripted-cottage \
  --output assets/remotion-starter/video.json --copy-assets
python3 scripts/validate_scene.py assets/remotion-starter/video.json
python3 scripts/test_production.py
# In assets/remotion-starter: npm install && npm run storyboard && npm run render
```

**Scope boundary:** user-facing storyboard is the *creative contract*; `video.json` is the *execution artifact*. The compiler presently supports deterministic per-shot layered still image/SVG motion plus V2-compatible scene overlays; it does not auto-create artwork or synthesize photo/video footage. External text-to-image/video tools, semantic vision review and advanced morphing are separate optional integrations, not claimed bundled features.
