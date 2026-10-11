# Scene DSL v1 — exact capabilities of the bundled renderer

## Structure

```json
{
  "meta": {
    "title": "A short title",
    "width": 1920,
    "height": 1080,
    "fps": 30,
    "background": "#0B1020",
    "music": {"file": "music.mp3", "volume": 0.15}
  },
  "scenes": [
    {
      "id": "intro",
      "durationFrames": 90,
      "background": "#111827",
      "audio": {"file": "voice-intro.mp3", "volume": 1},
      "elements": []
    }
  ]
}
```

`meta.music` and `scene.audio` are optional. Sound files must be real files under project `public/` and are **never synthesized automatically**. `durationFrames` is scene length (positive integer); total duration is the sum of all scene lengths. Each scene begins immediately after the previous one, with hard cuts. FPS is global, recommended 24 or 30. `id` is unique across scenes.

## Element types

Every element requires a unique (within its scene) `id`, a `type`, and type-specific geometry. The `fill` property is a CSS color. Numeric coordinates refer to design pixels (`meta.width × meta.height`).

| type | required fields | optional fields |
| --- | --- | --- |
| `text` | `x`, `y`, `width`, `height`, `text`, `fontSize`, `fill` | `fontWeight` (100–900), `align` (`left`,`center`,`right`), `verticalAlign` (`top`,`middle`,`bottom`), `fontFamily`, `lineHeight` |
| `rect` | `x`, `y`, `width`, `height`, `fill` | `radius` |
| `circle` | `x`, `y`, `r`, `fill` | `stroke`, `strokeWidth` |
| `line` | `x`, `y`, `x2`, `y2`, `stroke` | `strokeWidth`, `arrowHead` (boolean) |

- Circle `(x,y)` denotes its **center**. Rect and text `(x,y)` denote the top-left corner.
- A line's arrowhead is computed from its endpoint and `strokeWidth`.
- `text` wraps inside its allocated rectangle using SVG `foreignObject` with HTML and has default CSS `whiteSpace: pre-wrap`.
- `text` supports embedded newline (`\n`) but **not Markdown or HTML parsing**.
- `fontWeight`, `lineHeight` and `fontFamily` only affect text. Use a widely installed CJK font. Check installed fonts in the execution environment; missing glyphs can silently fall back.
- `radius` is border radius for rectangles.

## Visibility timing (optional)

Each element may declare `visibleFrom` (inclusive) and `visibleUntil` (exclusive). Both are scene-local frame numbers. Default is the entire scene. Common use: subtitle cards staggered across a single scene.

```json
{"id":"caption-1","type":"text","x":120,"y":870,"width":1680,"height":120,"text":"首先拆分场景","fontSize":48,"fill":"#FFFFFF","visibleFrom":0,"visibleUntil":42}
```

## Animation (optional)

A motion array is ordered by increasing **scene-local frame number**. Supported motion values: `dx`, `dy` (translation in design pixels), `opacity` (0 to 1), `scale` (nonnegative), `rotate` (degrees). Missing values use default (`dx=dy=rotate=0`, `opacity=scale=1`) unless that property was previously explicitly set. Each property is linearly interpolated between its own explicitly declared keyframes and held outside them.

```json
{
  "id": "badge",
  "type": "rect",
  "x": 100,
  "y": 200,
  "width": 500,
  "height": 140,
  "fill": "#3B82F6",
  "motion": [
    {"frame": 0, "opacity": 0, "dy": 50, "scale": 0.9},
    {"frame": 15, "opacity": 1, "dy": 0, "scale": 1},
    {"frame": 75, "opacity": 1},
    {"frame": 89, "opacity": 0}
  ]
}
```

Notes:
- This example lasts 90 frames. The final scene-local frame is `89`, not 90.
- Transform origin is the bounding box center. For circles, use `(x, y)`; for lines, midpoint.
- `motion` does not automatically cause entrance/exit; define opacity endpoints deliberately.
- A keyframe carrying only `opacity` leaves previously specified `dy` and `scale` unchanged.
- Avoid long-distance text motion while it is being read. Use 12–20 frame entrances at 30 fps.

## Audio

```json
{"audio": {"file":"narration/scene1.wav","volume": 1}}
```

The file path is relative to the template's `public/` directory. Scenes play their audio for the duration of the scene; trim or prepare files appropriately. Optional global background track `meta.music` plays from frame 0. The audio objects do not contain automatic TTS, gain ducking, loudness normalization or guaranteed transcript sync: those require an external asset-generation or audio-alignment step.

## Agent rules for coherent layout

1. Keep **text** inside ~100px safe margins for 1920×1080; subtitle box near bottom at y≈860, height≈140.
2. Headline font sizes 72–112, body 40–64, subtitles 42–56 (scale proportionally for other resolutions).
3. Split a dense diagram across scenes instead of shrinking every label.
4. Use limited motion with staging; animate highlights/links after the objects they refer to become visible.
5. Keep line segments and arrowheads within canvas and avoid overlaps with label rectangles.
6. High-contrast body copy; avoid thin/light lettering on low-contrast backgrounds.

## Extending the DSL

The bundled renderer does **not** support paths, gradients, particles, 3D, background videos/images, automatic scene transitions, graph auto-layout or timed per-word text highlighting. To add one: define new schema fields, update `src/types.ts`, implement drawing in `src/Video.tsx`, add validation to `scripts/validate_scene.py`, then create a demo and compare rendered keyframes. Do not assume unknown fields will be rendered.

---

# V2 extension — character-led animated storytelling

V2 adds 2D procedural human/dog characters with articulated joints, actions,
contact-aware two-bone IK, multi-shot asset reuse, and an animated camera.
V1 `rect/`text/`circle/`line schema remains valid.

## Supported fields (only)

At document root:

```json
"characterAssets": [
  {"id":"girl", "kind":"human", "colors":{
    "body":"#8062CA", "skin":"#F0B487", "accent":"#49386C", "outline":"#24354B"
  }},
  {"id":"puppy", "kind":"dog", "colors":{"body":"#C88953"}}
]
```

In each scene (in addition to the V1 `elements array):

```json
"characters": [
  {"id":"girl", "asset":"girl", "x":700, "y":900, "scale":1.15,
   "facing":1,
   "actions":[{"name":"wave", "from":10, "to":120}]},
  {"id":"puppy", "asset":"puppy", "x":1150, "y":900,
   "scale":1.15, "facing":-1,
   "actions":[{"name":"sit", "from":5, "to":140}]}
],
"interactions": [
  {"id":"contact", "type":"highFive", "actors":["girl","puppy"],
   "frame":98, "holdFrames":12, "target":{"x":912,"y":650}}
],
"camera": [{"frame":0,"x":960,"y":540,"zoom":1},
           {"frame":149,"x":960,"y":540,"zoom":1.13}]
```

All timings are **scene-local**. `frame for a highFive is the exact intended
hand/paw contact frame. Interaction ramps in during the 13 preceding frames,
holds for `holdFrames, and ramps back out in 13 frames. Use the validator
to check each participant's initial reachable distance to the target. During
contact, the IK solver clamps unreachable targets; do not rely on the renderer
to magically fix bad geometry.

The `x,y root is the character's ground position. `facing is
+1 (facing right) or -1 (mirrored). `motion root keyframes are ordered
by frame and each requires `x,y; optional `scale,facing.
Two-keyframe motion uses smooth interpolation. For actors that must touch,
avoid a root movement during the contact action unless you calculate reachability
at the exact contact frame.

Actions are timed using `{name, from, to, strength?}. Supported names:
`idle, `walk, `run, `wave, `sit,
`reach, `pawRaise, `blink, `headTurn,
`tailWag. Motion weights use a deterministic 9-frame ease in/out.
Some actions are intentionally species-specific: the human rig responds to wave,
reach and arm motion; the dog responds to run, sit, pawRaise, tailWag.
The built-in rigs are *stylized procedural SVG characters*, not skeletal imports
or photorealistic humans or animals. A multilayer SVG asset importer, nested
rig authoring and full body physics are beyond the current implemented scope.

## Examples

- `assets/remotion-starter/video.json: **V2** 18-second girl-and-puppy demo.
- `examples/character-interaction/video.json: a copy of the V2 example.
- `examples/v1-video.json: original 12-second graphics-only V1 example.

## Quality and testing

Run `python3 scripts/validate_scene.py assets/remotion-starter/video.json,
`python3 -m unittest discover -s scripts -p test_skill.py, and inside the
Remotion starter run `npm run test:rig. For rendered evidence, run
`npm install && npm run storyboard && npm run render.
These offline checks do not replace visual inspection of an actual rendered frame.
