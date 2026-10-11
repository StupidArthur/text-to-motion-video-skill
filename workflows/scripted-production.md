# V3: storyboard-first production (the strong-model / local-agent handoff)

This workflow is an **opt-in top-level authoring interface** above the original Remotion scene DSL. Neither the story generator nor the Code Agent must use preset characters. Reuse existing rigs only when they genuinely satisfy the shot.

## Phase 1 — directing (stronger model, higher-value token budget)

The director creates three independent JSON files:

- `storyboard.json`: globally contiguous `[startFrame,endFrame)` shots, one clear `intent`, `subject`, `shotType`, `beforeState`, `afterState`, `beats`, `layers` and local `camera` timeline per shot.
- `visual-bible.json`: stable identities, colors/proportions, visual style, and an **asset manifest based on story requirements**. It is normal for files listed in the manifest not to exist yet when the director hands off. Never substitute unrelated prebuilt art.
- `acceptance.json`: testable requirements per shot, including at least one state-change action criterion; explicitly mark checks requiring **visual review**.

The director specifies the outcome, not path coordinates of every character body part. Avoid fixing every shot length at 3 seconds: use the actual narrative and music timing. Assign at least three different framing types across longer videos and a meaningful state change per shot. A shot may feature environment, architecture, object or graphic details; a character is not mandatory.

## Phase 2 — local Code Agent (implementation freedom with no silent substitutions)

1. Read the three documents and inspect actual provided assets; produce an **asset-by-asset implementation plan**. Decide independently whether a shot needs generated SVG, layered illustrations, a locally supplied PNG/WebP, or an optional licensed source. Respect the runtime's available rendering capabilities.
2. **Create every missing generated asset** under the project's `public/` directory. For a custom red hood, draw the hood/cape/head/face/boots as paths or grouped SVG and save a concrete file. For a forest cottage, build perspective, windows, doorway, light and foreground layers. Do not fake completion with a rectangle labelled “cottage.”
3. Prefer style-consistent custom path art. You may extend Remotion/TSX or an SVG asset when the shot needs an expressive action. The director's story events are hard requirements; path geometry, rigs, interpolation and caching are implementation decisions.
4. Run `production_pipeline.py` to validate and compile **only after** real artwork files exist. Reject missing assets and unsafe paths. The compiler does not synthesize images; it maps actual authored files into Remotion scenes.
5. Render **first, midpoint, event and last** frames for each shot; the shipped `storyboard.mjs` adds frame evidence based on shot scenes; ensure any non-midpoint action frames are additionally captured. Review interactions (door opening, hand reaching, jumping, object change) against before/after state.
6. Use `shot_review.py init` to create a **pending review checklist**. Attach actual screenshot paths and reviewer identity after checking images. Use `shot_review.py verify` as the delivery gate. Automated JSON/geometry checks are not equivalent to visual judgment. If no model/tool can examine screenshots, keep visual checks pending and request a human check; never counterfeit review records.
7. Render approved shots, preserve original master audio, generate final MP4 and verify using `check_video.py`. Retain full editable source and report failures. Respect media usage rights.

## Limits / escalation

- Text-only agents can programmatically construct SVG/Canvas 2D drawings, not guarantee professional illustration, cinematic performance or realistic 3D. Visual requirements beyond the agent's ability must be **reported explicitly**, never replaced by unrelated stock characters.
- External image/video generation is optional and only if a corresponding tool is actually available and approved. The included V3 runtime directly supports **layered SVG, PNG, JPEG and WebP art**. It does **not** generate assets from text by itself, nor does V3 claim to accept arbitrary video clips in this interface.
- User-provided art and generated SVG are treated as untrusted: avoid external URLs, embedded script, event handlers or remote assets; sanitize before referencing.
- Contact and character animation can continue to use V2 rigs. Storyboard compilation is compatible with the V1/V2 scene format via `sceneOverlay` but an extension must be tested rather than presumed supported.
- A compile pass is **not** acceptance; a render pass is **not** visual review.

## Commands (from Skill root)

```bash
# For an executable example, copy these three contracts and their public/ art
cp -R examples/scripted-cottage /tmp/cottage-production
cp -R assets/remotion-starter /tmp/cottage-remotion
python3 scripts/production_pipeline.py /tmp/cottage-production \
  --output /tmp/cottage-remotion/video.json --copy-assets
python3 scripts/validate_scene.py /tmp/cottage-remotion/video.json
python3 scripts/shot_review.py init /tmp/cottage-production --output /tmp/cottage-remotion/out/shot-review.json
# Render after installing npm dependencies in /tmp/cottage-remotion:
# npm run storyboard && npm run render
# Add genuine review evidence and reviewer manually (or through actual visual tool):
python3 scripts/shot_review.py verify /tmp/cottage-production /tmp/cottage-remotion/out/shot-review.json
```

`shot_review.py verify` **should fail** before someone reviews the images; this is a useful QA gate, not a runtime bug.
