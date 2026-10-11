"""Check generated 2D compositing layers referenced by V3 compiled videos."""
import math
from pathlib import Path


def finite(value):
    return type(value) in (int,float) and math.isfinite(value)

def check_layers(ch, scene, here, project_dir):
    layers=scene.get('layers', [])
    if not isinstance(layers,list):
        ch.error(here,'layers must be an array');return
    seen=set()
    duration=scene['durationFrames']
    base=(project_dir/'public').resolve()
    for i,layer in enumerate(layers):
        loc=f'{here}.layers[{i}]'
        if not isinstance(layer,dict):ch.error(loc,'layer must be object');continue
        if set(layer)-{'id','file','assetId','x','y','width','height','plane','motion'}:
            ch.error(loc,'unsupported layer fields')
        name=layer.get('id')
        if not isinstance(name,str) or not name:ch.error(loc,'layer id required')
        elif name in seen:ch.error(loc,'duplicate layer id')
        seen.add(name)
        file=layer.get('file')
        if not isinstance(file,str) or not file or '\\' in file or ':' in file:
            ch.error(loc,'unsafe layer file');continue
        p=Path(file)
        if p.is_absolute() or '..' in p.parts or p.suffix.lower() not in {'.svg','.png','.jpg','.jpeg','.webp'}:
            ch.error(loc,'unsupported or unsafe layer asset');continue
        target=(base/p).resolve()
        if not target.is_relative_to(base):ch.error(loc,'layer escapes public')
        elif not target.is_file():ch.error(loc,f'missing layer asset public/{file}')
        for key in ('x','y','width','height'):
            if not finite(layer.get(key)) or (key in ('width','height') and layer[key]<=0):
                ch.error(loc,f'invalid {key}')
        if layer.get('plane','back') not in ('back','front'):ch.error(loc,'invalid plane')
        keys=layer.get('motion',[])
        if not isinstance(keys,list):ch.error(loc,'motion must be array');continue
        last=-1
        for key in keys:
            frame=key.get('frame') if isinstance(key,dict) else None
            if type(frame) is not int or not 0<=frame<duration or frame<=last:
                ch.error(loc,'invalid keyframe ordering or frame bounds')
            else:last=frame
            if isinstance(key,dict):
                if set(key)-{'frame','dx','dy','rotate','scale','opacity'}:ch.error(loc,'unknown keyframe props')
                if not (set(key)-{'frame'}):ch.error(loc,'empty motion keyframe')
                for field in ('dx','dy','rotate','scale','opacity'):
                    if field in key and (not finite(key[field]) or (field=='scale' and key[field]<0) or (field=='opacity' and not 0<=key[field]<=1)):
                        ch.error(loc,f'invalid {field}')
