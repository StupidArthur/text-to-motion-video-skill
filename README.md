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
