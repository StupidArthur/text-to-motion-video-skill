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

---

# V2.1 — Custom articulated SVG rigs, props and interactions (implemented)

V1 and built-in V2 human/dog character specifications are still accepted. V2.1 adds generic **characterAssets[].kind = "custom"**, declarative nested bones, local joint action tracks, optional imported SVG pieces, two-link IK, scene props with frame-based pickup/release, and cinematic camera tracks. No 3D, realtime player input or photorealistic generation is provided.

## Custom rig example

Each bone contains `id`, optional `parent`, required `pivot:{x,y}` relative to its parent's coordinate system, and an optional `visual`. The parent-less bone is attached to character ground root. Bones support `anchors` (named points relative to that bone), optional `layer` (paint order). A visual can be:

- `path`: `{ "type":"path", "d":"M0,0 L50,0", "fill":"#F00", "stroke":"#222", "strokeWidth":3 }` — static SVG path.
- `rect`: `{ "type":"rect", "x":0, "y":-15, "width":100, "height":30, "fill":"#FA0", "radius":10 }`.
- `ellipse`: `{ "type":"ellipse", "cx":0, "cy":0, "rx":40, "ry":50, "fill":"#FA0" }`.
- `svg`: `{ "type":"svg", "file":"parts/head.svg", "x":-60, "y":-60, "width":120, "height":120 }` — image-backed external SVG part. The actual file must be within the Remotion project's `public/` folder. Individual part files are positioned by their bone, not parsed as arbitrary XML.

Example:

```json
{
  "id": "robot", "kind": "custom",
  "rig": {
    "bones": [
      {"id":"torso","pivot":{"x":0,"y":-100}, "visual":{"type":"rect","x":-60,"y":-80,"width":120,"height":160,"fill":"#607BDD"}},
      {"id":"upper","parent":"torso","pivot":{"x":60,"y":-50},"visual":{"type":"rect","x":0,"y":-10,"width":85,"height":20,"fill":"#FFD39B"}},
      {"id":"lower","parent":"upper","pivot":{"x":85,"y":0},"anchors":{"hand":{"x":80,"y":0}},"visual":{"type":"rect","x":0,"y":-9,"width":80,"height":18,"fill":"#FFD39B"}}
    ],
    "ikChains": [{"id":"rightHand","upper":"upper","lower":"lower","effector":"lower.hand","bend":-1}]
  }
}
```

Joint angles are relative to the **parent bone**. Frame-based local actions (each joint track runs in action-local frames, and is blended by weight in declared order):

```json
"jointActions": [
  {"name":"wave","from":10,"to":65,"strength":1,"fadeFrames":8,
   "joints":{"upper":[{"frame":0,"angle":-10},{"frame":25,"angle":-65},{"frame":55,"angle":-10}]}}
]
```

The IK solver targets the named end anchor on the lower bone; the lower bone must be a direct child of the upper bone. An unreachable target is clamped to the chain's geometric reach (also inspect keyframes to avoid implausible poses). Custom rigs should make their default limb axis run from upper pivot to the lower pivot, and from lower pivot to the effector anchor. Parts are separately illustrated with SVG primitive or imported static SVG files, preserving editability.

## Semantic behaviors

Any character can have `behaviors` with `type`, `from`, `to` and `target:{x,y}`, with optional `strength`:

- `moveTo` — smoothly offsets the root toward a world target by the behavior's end frame;
- `lookAt` — turns the head mildly toward a world target (custom rigs need a bone named `head`);
- `reachTo` — asks the active arm IK to reach a world point; custom rigs require `ikChains`.

Example: `"behaviors":[{"type":"reachTo","from":70,"to":130,"target":{"x":980,"y":575}}]`. These behaviors are resolved as deterministic frame functions, not simulation.

## Prop assets and attachments

Declare top-level `propAssets:[{"id":"ball","visual":{"type":"ellipse","cx":0,"cy":0,"rx":18,"ry":18,"fill":"#EDC34A"}}]`. Put `props` inside a scene with `{id,asset,x,y,scale?,rotation?,layer?:"back"|"front"}`. Props use the same `visual` types as rig bones.

An attachment period follows a named character anchor: `"attachments":[{"id":"pickup","prop":"ball1","character":"robot1","anchor":"lower.hand","from":100,"to":155,"releaseTo":{"x":1350,"y":700},"releaseEnd":200}]`. Before `from`, the prop is at its base position. During `[from,to)`, it follows the bone's world anchor. After release, it interpolates toward `releaseTo` until `releaseEnd`; if no release target is provided it remains at its last attached position. For built-in human/dog characters, named anchors include `rightHand`, `leftHand`, `paw`, `head`, `root`, `frontFoot`, `backFoot`. For custom rigs use `bone.anchorName` or `bone.origin`.

**Important limitations:** attach at frame `from` snaps to the anchor; place your prop near the hand on that frame or design a pickup movement in advance. Release trajectories are time-eased linear, not real gravity. A prop cannot be bound to two characters at the same time. The renderer does not import skinned mesh, full Spine runtime rigs, or automatically retarget arbitrary external skeletal files. Instead, import a *folder of isolated SVG parts* and define their pivots/bone hierarchy in JSON.

## Contact and gait

Existing `highFive` events can target either built-in people/dogs or a custom rig with a valid `ikChains` definition. The contact point is in scene/world coordinates. For custom rigs each IK chain is eligible for the event; use one contact chain per character for unambiguous contact. Foot planting is a deterministic world-space stance/swing plan for built-in human/dog `walk`/`run` actions. Custom rigs require explicit leg joint tracks for gait; arbitrary ground meshes, collision physics and cloth dynamics are not implied.

## Example and QA

- **Complete custom/asset example:** `examples/custom-rig/video.json` with `examples/custom-rig/public/robot-face.svg`.
- Switch into the bundled starter using `npm run demo:custom` (copies example JSON and asset), then `npm run test:rig && npm run storyboard && npm run render`.
- For original scenes use `npm run demo:v1` / `npm run demo:v2`.
- `npm run storyboard` also samples interaction contact frames, action beats, attach/detach instants, and scene boundaries. Use the text-only checks for structural validation, not visual/aesthetic assessment.
