# text-to-motion-video — Text-only Agent → MP4

A portable Agent Skill plus a usable Remotion starter project for **text-only code agents**. It transforms a structured scene plan into React SVG/HTML animation and renders deterministic MP4 files.

## Files

- `SKILL.md` — instructions that the Code Agent reads.
- `references/SCENE_DSL.md` — the actual supported JSON schema, timing rules and extension guidelines.
- `references/QUALITY_CHECKLIST.md` — automatic and manual quality gates.
- `scripts/validate_scene.py` — dependency-free structural/lint checks.
- `scripts/check_frames.py` — optional low-information PNG checks (needs Pillow).
- `scripts/check_video.py` — optional MP4 metadata check (needs `ffprobe`).
- `assets/remotion-starter/` — editable example Remotion project (`video.json`, `src/`, `package.json`).

## Install into a Code Agent

Copy the **entire** `text-to-motion-video/` directory into the Skills location supported by your Code Agent. Examples:

```bash
# Claude Code (project scope)
mkdir -p .claude/skills
cp -R text-to-motion-video .claude/skills/

# Agents supporting project-local .agents/skills (check your client's docs)
mkdir -p .agents/skills
cp -R text-to-motion-video .agents/skills/
```

Invoke by asking your agent: `使用 text-to-motion-video skill，生成一个 12 秒、16:9、解释 AI Agent 工作流的中文视频。`

## Directly run the bundled demo

```bash
cp -R text-to-motion-video/assets/remotion-starter ./motion-video
cd motion-video
npm install
python3 ../text-to-motion-video/scripts/validate_scene.py video.json
npm run storyboard
npm run render
python3 ../text-to-motion-video/scripts/check_video.py video.json out/video.mp4
```

Requirements: Node.js 20+, npm, Python 3.10+, Chromium environment supported by Remotion, internet or npm dependency cache for the first installation. `ffprobe` optional. Font selection may vary by OS; install a suitable Simplified Chinese font for consistent typography. Audio is deliberately absent in the bundled demo.

**Scope:** animated diagrams, text effects, vector explainer videos, timelines, charts and educational content. It does not generate photorealistic footage or synthesize narration on its own.

**Validation caveat:** Included JSON validator and Python unit tests can run without npm/network; Remotion render still requires installation of npm dependencies and a working rendering browser. The project ships source, not a pre-rendered MP4.

## Technical references

- Agent Skills specification: https://agentskills.io/specification
- Remotion fundamentals: https://www.remotion.dev/docs/the-fundamentals
- Remotion CLI: https://www.remotion.dev/docs/cli
- Remotion still frame option: https://www.remotion.dev/docs/options/frame

## V2: character animation (new)

The default starter demo is now an **18-second cartoon character story**:
Girl waves → puppy runs → puppy sits → hand/paw high-five → closing camera zoom.
The V1 pure infographic example remains available at `examples/v1-video.json`.

Key additions: `characterAssets`, per-scene `characters`, timed `actions`,
shared world-space `highFive` targets, deterministic two-link inverse kinematics,
and `camera` keyframes. See `references/SCENE_DSL.md` for the exact supported
schema, `src/rig.ts` for the pure numerical motion engine, and `src/Characters.tsx`
for the rendered procedural characters.

### Test and render V2

```bash
python3 scripts/validate_scene.py assets/remotion-starter/video.json
python3 -m unittest discover -s scripts -p test_skill.py
cd assets/remotion-starter
npm run test:rig          # TypeScript compile + pure motion tests, no React browser needed
npm install              # dependencies for Remotion
npm run typecheck
npm run storyboard        # render sampled frames, browser needed
npm run render            # out/video.mp4
```

**Limitations:** A text-only agent can author stylized characters and scripted
interactions, but not automatically create convincing photoreal humans, animals,
or acting performances. The currently implemented rigs are code-generated SVG,
not a general imported-skeleton format. This package has numerical and structural
tests; rendering and artistic QA must be performed in an environment with npm
and a Chromium-compatible browser.

## V2.1: Custom 2D character rigs (current)

Alongside the original V1 graphics and V2 girl/dog demo, the Skill now supports *editable multipart SVG character assets* with user-defined bones, pivot points, named hand/foot anchors, joint action blending, local-to-world IK, deterministic `highFive` contact, built-in gait foot planting, scene props that attach to/release from character anchors, and semantic storyboard sampling. Custom rigs are not photorealistic models or full Spine/Lottie skeletal importers: supply one SVG image per articulated body part and a JSON rig with pivots.

Run validation and demos:

```bash
# From repository root
python3 scripts/test_skill.py
python3 scripts/test_v2.py
python3 scripts/test_advanced.py

# From the starter
cd assets/remotion-starter
npm run test:rig   # deterministic math, IK, frame random access, prop attachment, planted feet
npm run demo:custom
python3 ../../scripts/validate_scene.py video.json
npm install        # network required on first run
npm run storyboard
npm run render
```

`npm run demo:custom` switches the starter JSON to an 8-second robot-and-dog cartoon sample, including imported `robot-face.svg` as an independently movable head. Restore samples with `npm run demo:v2` or `npm run demo:v1`. Example files and docs are under `examples/custom-rig/` and `references/SCENE_DSL.md`. Do not claim the MP4 exists until Remotion successfully renders it and checks are complete.

## V3 — Director storyboard → on-demand art → Remotion (NEW)

For stories/MVs, start with **three structured files** authored by a stronger directing model: `storyboard.json` (frame-level timing, action beats, composition), `visual-bible.json` (style/character continuity and asset requests), and `acceptance.json` (per-shot visible results). A lower-cost local Code Agent builds any missing artwork **on demand** as SVG/PNG/WebP/JPEG and verifies each shot; generic built-in character templates are not required.

See **[`workflows/scripted-production.md`](workflows/scripted-production.md)** and **[`examples/scripted-cottage/`](examples/scripted-cottage/)**. This opt-in workflow does not modify existing V1/V2 rendering behavior.

```bash
# From Skill root:
cp -R assets/remotion-starter /tmp/my-remotion
python3 scripts/production_pipeline.py examples/scripted-cottage \
  --output /tmp/my-remotion/video.json --copy-assets
python3 scripts/validate_scene.py /tmp/my-remotion/video.json
python3 scripts/test_production.py
cd /tmp/my-remotion
npm install
npm run storyboard
npm run render
```

Quality assurance uses `scripts/shot_review.py`: run `init` to create a **pending** review form; actual frame screenshots and a reviewer are required before `verify` succeeds. A text-only model cannot truthfully declare visual checks passed. The compiler does not create art itself—your code agent must write files declared by the storyboard; missing files cause a clear error. An example generated SVG person/cottage is provided to exercise the pipeline, not to limit future subjects.
