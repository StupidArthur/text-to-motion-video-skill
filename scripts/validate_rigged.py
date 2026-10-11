"""Additional validation for hierarchical 2D rigs, keyed joints, props and attachments."""
import math
from pathlib import Path


def numeric(x):
    return type(x) in (float, int) and math.isfinite(x)


def point(ch, v, at):
    if not isinstance(v, dict) or set(v) != {'x', 'y'} or not all(numeric(n) for n in v.values()):
        ch.error(at, 'point requires finite x and y'); return False
    return True


def framewindow(ch, obj, at, duration, *, a='from', b='to'):
    v, w = obj.get(a), obj.get(b)
    if type(v) is not int or type(w) is not int or not 0 <= v < w < duration:
        ch.error(at, 'invalid timeline window'); return False
    return True


def validate_visual(ch, visual, loc, project_root):
    if not isinstance(visual, dict): ch.error(loc, 'visual object required'); return
    typ = visual.get('type')
    needed = {
        'path': {'d', 'fill'}, 'ellipse': {'cx', 'cy', 'rx', 'ry', 'fill'},
        'rect': {'x', 'y', 'width', 'height', 'fill'},
        'svg': {'file', 'x', 'y', 'width', 'height'},
    }
    extras = {'path': {'stroke', 'strokeWidth'}, 'ellipse': set(),
              'rect': {'radius'}, 'svg': set()}
    if typ not in needed: ch.error(loc, 'unsupported visual type'); return
    if set(visual)-needed[typ]-extras[typ]-{'type'}: ch.error(loc, 'unsupported visual fields')
    for k in needed[typ]:
        v = visual.get(k)
        if k in ('fill', 'd', 'file'):
            if not isinstance(v, str) or not v.strip(): ch.error(loc, f'invalid {k}')
        elif not numeric(v) or (k in ('width', 'height', 'rx', 'ry') and v <= 0):
            ch.error(loc, f'invalid {k}')
    if typ == 'svg' and isinstance(visual.get('file'), str) and project_root:
        name = visual['file'].replace('\\', '/')
        p = Path(name)
        if p.is_absolute() or not p.parts or '..' in p.parts or ':' in name or not name.lower().endswith('.svg'):
            ch.error(loc, 'unsafe SVG filename')
        else:
            base = (project_root / 'public').resolve()
            resource = (base / p).resolve()
            if not resource.is_relative_to(base): ch.error(loc, 'unsafe SVG filename')
            elif not resource.is_file(): ch.error(loc, f'missing SVG asset public/{name}')


def check_rig(ch, asset, loc, project_root):
    rig = asset.get('rig')
    if not isinstance(rig, dict) or not isinstance(rig.get('bones'), list) or not rig['bones']:
        ch.error(loc, 'custom rig must have nonempty bones'); return set(), set()
    if set(rig)-{'bones', 'ikChains'}: ch.error(loc, 'unsupported rig fields')
    bones={}
    for i, b in enumerate(rig['bones']):
        at=f'{loc}.rig.bones[{i}]'
        if not isinstance(b, dict): ch.error(at, 'bone object required'); continue
        if set(b)-{'id','parent','pivot','visual','anchors','layer'}: ch.error(at, 'unsupported bone fields')
        name=b.get('id')
        if not isinstance(name,str) or not name: ch.error(at,'bone id required'); continue
        if name in bones: ch.error(at, f'duplicate bone id {name}')
        bones[name]=b
        point(ch,b.get('pivot'),at+'.pivot')
        if 'visual' in b:validate_visual(ch,b['visual'],at+'.visual',project_root)
        if 'anchors' in b:
            if not isinstance(b['anchors'],dict): ch.error(at,'anchors must be object')
            else:
                for an,p in b['anchors'].items():point(ch,p,f'{at}.anchors.{an}')
        if 'layer' in b and not numeric(b['layer']):ch.error(at,'invalid layer')
    for name,b in bones.items():
        if b.get('parent') and b['parent'] not in bones: ch.error(loc,f'{name} unknown parent')
        seen=set(); cur=name
        while cur in bones and cur not in seen:
            seen.add(cur);cur=bones[cur].get('parent')
        if cur in seen:ch.error(loc,f'cycle in rig at {name}')
    chains = rig.get('ikChains',[])
    if not isinstance(chains,list):ch.error(loc,'ikChains must be list');chains=[]
    chain_ids=set()
    for i,c in enumerate(chains):
        at=f'{loc}.rig.ikChains[{i}]'
        if not isinstance(c,dict):ch.error(at,'chain object required');continue
        if set(c)-{'id','upper','lower','effector','bend'}:ch.error(at,'unsupported IK fields')
        if not isinstance(c.get('id'),str) or c['id'] in chain_ids:ch.error(at,'invalid or duplicate IK id')
        chain_ids.add(c.get('id'))
        upper=bones.get(c.get('upper'));lower=bones.get(c.get('lower'))
        if not upper or not lower or lower.get('parent') != c.get('upper'):ch.error(at,'IK chain requires child lower under upper');continue
        eff=c.get('effector')
        if not isinstance(eff,str) or '.' not in eff:ch.error(at,'effector must be bone.anchor');continue
        bn,anc=eff.split('.',1)
        if bn!=c['lower'] or anc not in lower.get('anchors',{}):ch.error(at,'IK effector must reference lower bone anchor')
        if c.get('bend',1) not in (-1,1):ch.error(at,'bend must be -1 or 1')
        if point(ch,lower.get('pivot'),at+'.lowerPivot'):
            p=lower['pivot']
            if math.hypot(p['x'],p['y']) < 1e-5:ch.error(at,'IK upper length zero')
        if isinstance(lower.get('anchors',{}).get(anc),dict):
            p=lower['anchors'][anc]
            if math.hypot(p['x'],p['y']) < 1e-5:ch.error(at,'IK lower length zero')
    anchors={name+'.'+anchor for name,b in bones.items() for anchor in b.get('anchors',{})}
    anchors |= {name+'.origin' for name in bones}
    return set(bones),anchors


def check_advanced(ch,doc,video_path=None):
    project_root=Path(video_path).resolve().parent if video_path else None
    rig_info={}
    for i,asset in enumerate(doc.get('characterAssets',[])):
        if not isinstance(asset,dict):continue
        if asset.get('kind')=='custom' or 'rig' in asset:
            if asset.get('kind')!='custom':ch.error(f'$.characterAssets[{i}]','rig currently requires kind custom')
            rig_info[asset.get('id')]=check_rig(ch,asset,f'$.characterAssets[{i}]',project_root)
    propAssets={}
    props=doc.get('propAssets',[])
    if not isinstance(props,list):ch.error('$.propAssets','must be list');props=[]
    for i,asset in enumerate(props):
        at=f'$.propAssets[{i}]'
        if not isinstance(asset,dict):ch.error(at,'object required');continue
        if set(asset)-{'id','visual'}:ch.error(at,'unsupported prop fields')
        aid=asset.get('id')
        if not isinstance(aid,str) or not aid or aid in propAssets:ch.error(at,'invalid/duplicate prop id');continue
        propAssets[aid]=asset
        validate_visual(ch,asset.get('visual'),at+'.visual',project_root)
    for si,scene in enumerate(doc.get('scenes',[])):
        if not isinstance(scene,dict) or type(scene.get('durationFrames')) is not int:continue
        duration=scene['durationFrames']; loc=f'$.scenes[{si}]'
        characters={c.get('id'):c for c in scene.get('characters',[]) if isinstance(c,dict)}
        assets={a.get('id'):a for a in doc.get('characterAssets',[]) if isinstance(a,dict)}
        for char in characters.values():
            at=f'{loc}.characters.{char.get("id")}'
            info=rig_info.get(char.get('asset'),(set(),set()))
            for ai,action in enumerate(char.get('jointActions',[])):
                aw=f'{at}.jointActions[{ai}]'
                if not isinstance(action,dict):ch.error(aw,'object required');continue
                if set(action)-{'name','from','to','strength','joints','fadeFrames'}:ch.error(aw,'unsupported fields')
                framewindow(ch,action,aw,duration)
                for key in ('strength','fadeFrames'):
                    if key in action and (not numeric(action[key]) or action[key]<0 or (key=='strength' and action[key]>1)):
                        ch.error(aw,f'invalid {key}')
                joints=action.get('joints')
                if not isinstance(joints,dict):ch.error(aw,'joints must be object');continue
                for name,keys in joints.items():
                    if name not in info[0]:ch.error(aw,f'unknown bone joint {name}')
                    if not isinstance(keys,list) or not keys:ch.error(aw,'joint keys required');continue
                    prev=-1
                    for keyframe in keys:
                        if not isinstance(keyframe,dict) or set(keyframe)!={'frame','angle'}:
                            ch.error(aw,'invalid joint keyframe');continue
                        frame=keyframe['frame']
                        if type(frame) is not int or frame<=prev or frame<0 or frame>action.get('to',0)-action.get('from',0):ch.error(aw,'joint frame out of action bounds')
                        if not numeric(keyframe['angle']):ch.error(aw,'invalid joint angle')
                        prev=frame if type(frame) is int else prev
            move_windows=[]
            for bi,beh in enumerate(char.get('behaviors',[])):
                bw=f'{at}.behaviors[{bi}]'
                if not isinstance(beh,dict):ch.error(bw,'object required');continue
                if set(beh)-{'type','from','to','target','hand','strength'}:ch.error(bw,'unsupported fields')
                if beh.get('type') not in ('reachTo','lookAt','moveTo'):ch.error(bw,'unsupported behavior')
                framewindow(ch,beh,bw,duration)
                if beh.get('type')=='moveTo' and type(beh.get('from')) is int and type(beh.get('to')) is int:
                    if any(beh['from']<b and a<beh['to'] for a,b in move_windows):ch.error(bw,'overlapping moveTo actions')
                    move_windows.append((beh['from'],beh['to']))
                point(ch,beh.get('target'),bw+'.target')
                if 'strength' in beh and (not numeric(beh['strength']) or not 0<=beh['strength']<=1):ch.error(bw,'invalid strength')
                if beh.get('type')=='reachTo' and char.get('asset') in rig_info and not assets[char['asset']].get('rig',{}).get('ikChains'):
                    ch.error(bw,'custom reachTo needs an IK chain')
        placed={}
        for pi,prop in enumerate(scene.get('props',[])):
            at=f'{loc}.props[{pi}]'
            if not isinstance(prop,dict):ch.error(at,'prop instance object required');continue
            if set(prop)-{'id','asset','x','y','scale','rotation','layer'}:ch.error(at,'unsupported prop fields')
            name=prop.get('id')
            if not isinstance(name,str) or not name or name in placed:ch.error(at,'duplicate or invalid prop id');continue
            placed[name]=prop
            if prop.get('asset') not in propAssets:ch.error(at,'unknown prop asset')
            for k in ('x','y'):
                if not numeric(prop.get(k)):ch.error(at,f'invalid {k}')
            if 'scale' in prop and (not numeric(prop['scale']) or prop['scale']<=0):ch.error(at,'invalid scale')
            if 'rotation' in prop and not numeric(prop['rotation']):ch.error(at,'invalid rotation')
            if prop.get('layer','front') not in ('front','back'):ch.error(at,'invalid layer')
        attached={}
        for ai,attach in enumerate(scene.get('attachments',[])):
            at=f'{loc}.attachments[{ai}]'
            if not isinstance(attach,dict):ch.error(at,'attachment object required');continue
            if set(attach)-{'id','prop','character','anchor','from','to','offset','releaseTo','releaseEnd'}:ch.error(at,'unsupported attachment fields')
            prop=attach.get('prop'); ch_id=attach.get('character')
            if prop not in placed:ch.error(at,'unknown prop')
            if ch_id not in characters:ch.error(at,'unknown attachment character')
            framewindow(ch,attach,at,duration)
            if 'offset' in attach:point(ch,attach['offset'],at+'.offset')
            if ('releaseTo' in attach) != ('releaseEnd' in attach):ch.error(at,'releaseTo and releaseEnd must be paired')
            if 'releaseTo' in attach:
                point(ch,attach['releaseTo'],at+'.releaseTo')
                if type(attach.get('releaseEnd')) is not int or not attach.get('to',duration)<=attach['releaseEnd']<duration:
                    ch.error(at,'invalid releaseEnd')
            if ch_id in characters:
                char=characters[ch_id];kind=assets.get(char.get('asset'),{}).get('kind')
                possible={'rightHand','leftHand','paw','head','root','frontFoot','backFoot'} if kind in ('human','dog') else rig_info.get(char.get('asset'),(set(),set()))[1]
                if attach.get('anchor') not in possible:ch.error(at,'unknown attachment anchor')
            spans=attached.setdefault(prop,[])
            if any(attach.get('from',0)<b and a<attach.get('to',0) for a,b in spans):ch.error(at,'overlapping prop attachments')
            if type(attach.get('from')) is int and type(attach.get('to')) is int:spans.append((attach['from'],attach['to']))
