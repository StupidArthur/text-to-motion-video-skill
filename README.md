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
