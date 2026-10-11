#!/usr/bin/env python3
"""Storyboard-first production contract validation and deterministic Remotion compilation.

The compiler never invents art or claims visual quality. Missing files are errors.
V3 is an opt-in authoring layer; V1/V2 JSON stays supported.
"""
import argparse
import json
import math
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
EXT = {".svg", ".png", ".jpg", ".jpeg", ".webp"}
SHOT_TYPES = {"wide", "medium", "closeup", "detail", "over-shoulder", "insert", "aerial"}
CHECK_CATEGORIES = {"action", "visual", "continuity", "technical"}
REQUIRED = ("storyboard.json", "visual-bible.json", "acceptance.json")

class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []
    def error(self, loc, msg): self.errors.append(f"{loc}: {msg}")
    def warn(self, loc, msg): self.warnings.append(f"{loc}: {msg}")
    def check(self):
        if self.errors:
            raise ValueError("\n".join(self.errors))

def finite(x):
    return type(x) in (int, float) and math.isfinite(x)

def positive_int(x):
    return type(x) is int and x > 0

def safe_path(root, file):
    if not isinstance(file, str) or not file.strip() or "\\" in file or ":" in file:
        return None
    path = Path(file)
    if path.is_absolute() or any(part in ("..", ".") for part in path.parts):
        return None
    base = root.resolve()
    result = (base / path).resolve()
    return result if result.is_relative_to(base) else None

def check_svg_safety(path):
    """Conservative SVG asset safety check (not a comprehensive sanitizer)."""
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return f"invalid SVG XML: {exc}"
    for el in root.iter():
        tag = el.tag.split("}")[-1].lower()
        if tag in ("script", "foreignobject", "iframe", "image", "animate", "set", "style"):
            return f"disallowed active or embedded SVG node: {tag}"
        for key, value in el.attrib.items():
            name = key.split("}")[-1].lower()
            val = value.strip().lower()
            if name.startswith("on") or name in ("href", "src") or ("url(" in val and not re.fullmatch(r"url\(\s*['\"]?#[a-zA-Z0-9_-]+['\"]?\s*\)",val)) or "javascript:" in val:
                return f"disallowed SVG attribute: {name}"
    return None


def load_contract(folder):
    folder = Path(folder)
    return tuple(json.loads((folder / item).read_text(encoding="utf-8")) for item in REQUIRED)

def validate(story, bible, accepts, public_root):
    r = Report()
    if not isinstance(story, dict) or not isinstance(bible, dict) or not isinstance(accepts, dict):
        r.error("contract", "all three files must contain JSON objects"); return r
    if any(obj.get("version") != 3 for obj in (story, bible, accepts)):
        r.error("contract", "all version fields must be 3")
    meta = story.get("meta")
    if not isinstance(meta, dict):
        r.error("storyboard.meta", "object required"); return r
    for key in ("width", "height", "fps"):
        if not positive_int(meta.get(key)):
            r.error("storyboard.meta", f"{key} must be positive integer")
    if not isinstance(meta.get("title"), str) or not meta.get("title", "").strip():
        r.error("storyboard.meta", "nonempty title required")
    if not isinstance(bible.get("style"), dict) or not bible["style"].get("description"):
        r.error("visual-bible.style", "style.description required")
    characters = bible.get("characters")
    if not isinstance(characters, list):
        r.error("visual-bible.characters", "array required"); characters = []
    character_ids = set()
    for c in characters:
        if not isinstance(c, dict) or not isinstance(c.get("id"), str) or not ID.fullmatch(c["id"]):
            r.error("visual-bible.characters", "character id invalid"); continue
        if c["id"] in character_ids: r.error("visual-bible.characters", "duplicate character id")
        character_ids.add(c["id"])
        if not all(isinstance(c.get(k), str) and c[k].strip() for k in ("appearance", "palette")):
            r.error(f"character.{c['id']}", "appearance and palette required")
    assets = bible.get("assets")
    if not isinstance(assets, list):
        r.error("visual-bible.assets", "array required"); assets = []
    asset_ids = set()
    for a in assets:
        if not isinstance(a, dict): r.error("asset", "object required"); continue
        aid = a.get("id"); file = a.get("file")
        if not isinstance(aid, str) or not ID.fullmatch(aid): r.error("asset", "invalid id"); continue
        if aid in asset_ids: r.error("asset", f"duplicate {aid}")
        asset_ids.add(aid)
        if not isinstance(a.get("description"), str) or not a["description"].strip():
            r.error(f"asset.{aid}", "description required; document new asset creation")
        path = safe_path(public_root, file)
        if path is None or (isinstance(file, str) and Path(file).suffix.lower() not in EXT):
            r.error(f"asset.{aid}", "unsafe or unsupported local asset path")
        elif not path.is_file(): r.error(f"asset.{aid}", f"missing asset {file}; create it before compilation")
        elif path.suffix.lower()==".svg":
            danger=check_svg_safety(path)
            if danger:r.error(f"asset.{aid}",danger)
        if a.get("origin") not in ("generated", "provided", "licensed"):
            r.error(f"asset.{aid}", "origin must be generated/provided/licensed")
    shots = story.get("shots")
    if not isinstance(shots, list) or not shots:
        r.error("storyboard.shots", "nonempty shots array required"); return r
    checks = accepts.get("checks")
    if not isinstance(checks, list) or not checks:
        r.error("acceptance.checks", "nonempty checks array required"); checks = []
    check_ids = set(); checks_by_shot = {}
    for c in checks:
        if not isinstance(c, dict): r.error("acceptance", "check must be object"); continue
        cid = c.get("id"); sid = c.get("shotId")
        if not isinstance(cid,str) or not ID.fullmatch(cid): r.error("acceptance", "check id invalid"); continue
        if cid in check_ids: r.error("acceptance", f"duplicate {cid}")
        check_ids.add(cid)
        checks_by_shot.setdefault(sid, []).append(c)
        if c.get("category") not in CHECK_CATEGORIES: r.error(f"check.{cid}", "invalid category")
        if not isinstance(c.get("criterion"), str) or len(c["criterion"].strip()) < 12:
            r.error(f"check.{cid}", "concrete criterion required")
        if type(c.get("requiresVisualReview")) is not bool:
            r.error(f"check.{cid}", "requiresVisualReview must be boolean")
    shot_ids=set(); cursor=0; seen_shot_types=set(); static_only=0
    for i, shot in enumerate(shots):
        loc=f"shots[{i}]"
        if not isinstance(shot, dict): r.error(loc,"shot must be object"); continue
        sid=shot.get("id")
        if not isinstance(sid,str) or not ID.fullmatch(sid): r.error(loc,"invalid id")
        elif sid in shot_ids: r.error(loc,"duplicate id")
        shot_ids.add(sid)
        start,end=shot.get("startFrame"),shot.get("endFrame")
        if type(start) is not int or type(end) is not int or start != cursor or end <= start:
            r.error(loc,f"frame ranges must be contiguous, start {cursor} and end > start"); continue
        cursor=end
        duration=end-start
        if shot.get("shotType") not in SHOT_TYPES: r.error(loc,"unsupported shotType")
        seen_shot_types.add(shot.get("shotType"))
        for k in ("intent", "subject", "beforeState", "afterState"):
            if not isinstance(shot.get(k),str) or len(shot[k].strip()) < 4:
                r.error(loc,f"{k} must be descriptive")
        if shot.get("beforeState") == shot.get("afterState"):
            r.error(loc,"beforeState and afterState must be different (observable story progression)")
        for who in shot.get("characterIds",[]):
            if who not in character_ids: r.error(loc, f"unknown character {who}")
        layers=shot.get("layers")
        if not isinstance(layers,list) or not layers: r.error(loc,"nonempty layers required"); layers=[]
        layer_ids=set()
        for k, layer in enumerate(layers):
            layerloc=f"{loc}.layers[{k}]"
            if not isinstance(layer,dict): r.error(layerloc,"layer must be object"); continue
            lid=layer.get("id")
            if not isinstance(lid,str) or not ID.fullmatch(lid): r.error(layerloc,"invalid id")
            elif lid in layer_ids:r.error(layerloc,"duplicate layer id")
            layer_ids.add(lid)
            if layer.get("assetId") not in asset_ids: r.error(layerloc,"unknown assetId")
            for field in ("x","y","width","height"):
                if not finite(layer.get(field)) or (field in ("width","height") and layer[field]<=0):
                    r.error(layerloc, f"invalid {field}")
            if layer.get("plane","back") not in ("back","front"):
                r.error(layerloc,"plane must be back/front")
            motion=layer.get("motion",[])
            if not isinstance(motion,list): r.error(layerloc,"motion must be array");continue
            last=-1
            for mk in motion:
                if not isinstance(mk,dict):r.error(layerloc,"motion keyframe must be object");continue
                frame=mk.get("frame")
                if type(frame) is not int or not 0<=frame<duration or frame<=last:
                    r.error(layerloc,"motion frames must ascend and fit within shot")
                else:last=frame
                if not set(mk).intersection({"dx","dy","rotate","scale","opacity"}):
                    r.error(layerloc,"motion keyframe must animate something")
                for field in ("dx","dy","rotate","scale","opacity"):
                    if field in mk and (not finite(mk[field]) or (field=="scale" and mk[field]<0) or (field=="opacity" and not 0<=mk[field]<=1)):
                        r.error(layerloc, f"invalid {field}")
        camera=shot.get("camera",[])
        if not isinstance(camera,list):r.error(loc,"camera must be an array");camera=[]
        last_camera=-1
        for cam in camera:
            if not isinstance(cam,dict) or type(cam.get("frame")) is not int or not 0<=cam["frame"]<duration or cam["frame"]<=last_camera:
                r.error(loc,"invalid camera keyframe")
            else:last_camera=cam["frame"]
            for prop in ("x","y","zoom"):
                if isinstance(cam,dict) and prop in cam and (not finite(cam[prop]) or (prop=="zoom" and cam[prop]<=0)):
                    r.error(loc,f"invalid camera {prop}")
        if "sceneOverlay" in shot:
            overlay=shot["sceneOverlay"]
            if not isinstance(overlay,dict) or set(overlay)-{"elements","characters","interactions","props","attachments","audio"}:
                r.error(loc,"sceneOverlay can only add V2 scene data, not override timelines/layers")
        beats=shot.get("beats",[])
        if not isinstance(beats,list) or not beats:r.error(loc,"at least one action beat required");beats=[]
        beatframes=[]
        for beat in beats:
            if not isinstance(beat,dict):r.error(loc,"beat must be object");continue
            at=beat.get("atFrame")
            if type(at) is not int or not start<=at<end:r.error(loc,"beat frame outside shot")
            else:beatframes.append(at)
            if not isinstance(beat.get("action"),str) or len(beat["action"].strip())<4:
                r.error(loc,"beat action must be descriptive")
        if beatframes!=sorted(beatframes):r.error(loc,"beats must be ordered by frame")
        if not checks_by_shot.get(sid):r.error(loc,"missing acceptance checks")
        if not any(c.get("category")=="action" for c in checks_by_shot.get(sid,[])):
            r.error(loc,"at least one action acceptance check required")
        for c in checks_by_shot.get(sid,[]):
            f=c.get("expectedAtFrame")
            if type(f) is not int or not start<=f<end:
                r.error(f"check.{c.get('id')}","expectedAtFrame outside shot")
        # A programmatic SVG layer can be a static reference; ensure shots include actual changes.
        if len(beats)<=1 and all(len(x.get("motion",[]))<=1 for x in layers):static_only+=1
    for sid in checks_by_shot:
        if sid not in shot_ids:r.error("acceptance",f"check references unknown shot {sid}")
    if static_only>len(shots)//2:r.warn("storyboard", "more than half of shots may be static; review visual progression")
    if len(shots)>=5 and len(seen_shot_types)<3:r.warn("storyboard", "low shot-type variety; review repetitive composition")
    return r

def compile_project(story,bible,accepts,public_root,out,copy_assets=False):
    report=validate(story,bible,accepts,public_root)
    report.check()
    out=Path(out)
    if copy_assets:
        for asset in bible["assets"]:
            source=safe_path(public_root,asset["file"])
            dest=safe_path(out.parent/"public",asset["file"])
            if dest is None:raise ValueError("unsafe destination")
            dest.parent.mkdir(parents=True,exist_ok=True)
            if source.resolve()!=dest.resolve():shutil.copyfile(source,dest)
    else:
        for asset in bible["assets"]:
            if not (out.parent/"public"/asset["file"]).exists():
                raise ValueError(f"asset missing from project public/: {asset['file']} (pass --copy-assets)")
    scenes=[]
    for shot in story["shots"]:
        scene={"id":shot["id"],"durationFrames":shot["endFrame"]-shot["startFrame"],
               "background":shot.get("background",story["meta"].get("background","#14212B")),
               "elements":[],"layers":[]}
        for layer in shot["layers"]:
            asset=next(a for a in bible["assets"] if a["id"]==layer["assetId"])
            scene["layers"].append({**layer,"file":asset["file"]})
        if shot.get("camera"):
            scene["camera"]=shot["camera"]
        if shot.get("sceneOverlay"):
            extras=shot["sceneOverlay"]
            if not isinstance(extras,dict) or set(extras)-{"elements","characters","interactions","props","attachments","audio"}:
                raise ValueError(f"invalid sceneOverlay in {shot['id']}: cannot overwrite shot identity, timing or art layers")
            scene.update(extras)
        scenes.append(scene)
    output={"meta":story["meta"],"scenes":scenes}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return output

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract_dir",type=Path)
    parser.add_argument("--public",type=Path,help="directory containing authored/generated artwork")
    parser.add_argument("--output",type=Path,help="target Remotion project video.json")
    parser.add_argument("--copy-assets",action="store_true")
    args=parser.parse_args()
    try:
        story,bible,accepts=load_contract(args.contract_dir)
        public=args.public or args.contract_dir/"public"
        report=validate(story,bible,accepts,public)
        for warning in report.warnings:print("WARN",warning)
        report.check()
        print(f"OK {len(story['shots'])} shots; {story['shots'][-1]['endFrame']} frames; {len(bible['assets'])} assets")
        if args.output:
            compile_project(story,bible,accepts,public,args.output,args.copy_assets)
            print(f"COMPILED {args.output}")
    except (ValueError,OSError,json.JSONDecodeError) as exc:
        print(f"ERROR {exc}",file=sys.stderr);return 1
    return 0
if __name__=="__main__":sys.exit(main())
