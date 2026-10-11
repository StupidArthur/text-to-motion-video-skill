"""V2 additions to the existing Scene DSL verifier."""
from math import hypot
from pathlib import Path

ACTIONS = {'idle','walk','run','wave','sit','reach','pawRaise','blink','headTurn','tailWag'}

def number(value):
    return type(value) in (int,float) and __import__('math').isfinite(value)

def check_v2(ch, doc, video_path=None):
    assets = doc.get('characterAssets', [])
    if not isinstance(assets,list):
        ch.error('$.characterAssets','must be a list');return
    names = {}
    for i, asset in enumerate(assets):
        loc = f'$.characterAssets[{i}]'
        if not isinstance(asset,dict):ch.error(loc,'object required');continue
        if set(asset)-{'id','kind','colors','rig'}:ch.error(loc,'unsupported fields')
        name = asset.get('id')
        if not isinstance(name,str) or not name:ch.error(loc,'invalid id');continue
        if name in names:ch.error(loc,'duplicate asset id')
        if asset.get('kind') not in ('human','dog','custom'):ch.error(loc,'kind must be human or dog')
        names[name]=asset.get('kind')
        colors = asset.get('colors',{})
        if not isinstance(colors,dict) or any(k not in ('body','skin','accent','outline') or not isinstance(v,str) for k,v in colors.items()):ch.error(loc,'invalid colors')
    for si, scene in enumerate(doc.get('scenes', [])):
        if not isinstance(scene,dict) or type(scene.get('durationFrames')) is not int or scene['durationFrames'] <=0:continue
        loc = f'$.scenes[{si}]'
        duration=scene['durationFrames']
        characters=scene.get('characters',[])
        if not isinstance(characters,list):ch.error(loc+'.characters','list required');continue
        ids={}
        for ci,char in enumerate(characters):
            where=f'{loc}.characters[{ci}]'
            if not isinstance(char,dict):ch.error(where,'object required');continue
            if set(char)-{'id','asset','x','y','scale','facing','motion','actions','jointActions','behaviors'}:ch.error(where,'unsupported fields')
            cid=char.get('id')
            if not isinstance(cid,str) or not cid:ch.error(where,'invalid id');continue
            if cid in ids:ch.error(where,'duplicate character id')
            ids[cid]=char
            if char.get('asset') not in names:ch.error(where,'unknown character asset')
            for field in ('x','y'):
                if not number(char.get(field)):ch.error(where,f'invalid {field}')
            if 'scale' in char and (not number(char['scale']) or char['scale']<=0):ch.error(where,'scale must be > 0')
            if 'facing' in char and char['facing'] not in (-1,1):ch.error(where,'facing must be -1 or 1')
            motion=char.get('motion',[])
            if not isinstance(motion,list):ch.error(where,'motion must be list');motion=[]
            prev=-1
            for mi,m in enumerate(motion):
                mw=f'{where}.motion[{mi}]'
                if not isinstance(m,dict):ch.error(mw,'object required');continue
                if set(m)-{'frame','x','y','scale','facing'}:ch.error(mw,'unsupported fields')
                fr=m.get('frame')
                if type(fr) is not int or not 0<=fr<duration or fr<=prev:ch.error(mw,'frames must be strictly increasing and inside scene')
                else:prev=fr
                for field in ('x','y'):
                    if not number(m.get(field)):ch.error(mw,f'invalid {field}')
                if 'scale' in m and (not number(m['scale']) or m['scale']<=0):ch.error(mw,'scale must be > 0')
                if 'facing' in m and m['facing'] not in (-1,1):ch.error(mw,'facing must be -1 or 1')
            actions=char.get('actions',[])
            if not isinstance(actions,list):ch.error(where,'actions must be list');actions=[]
            for ai,action in enumerate(actions):
                aw=f'{where}.actions[{ai}]'
                if not isinstance(action,dict):ch.error(aw,'object required');continue
                if set(action)-{'name','from','to','strength'}:ch.error(aw,'unsupported fields')
                if action.get('name') not in ACTIONS:ch.error(aw,'unsupported action')
                if type(action.get('from')) is not int or type(action.get('to')) is not int or not 0<=action['from']<action['to']<duration:ch.error(aw,'invalid action window')
                if 'strength' in action and (not number(action['strength']) or not 0<=action['strength']<=1):ch.error(aw,'strength must be in [0,1]')
        events=scene.get('interactions',[])
        if not isinstance(events,list):ch.error(loc+'.interactions','list required');continue
        event_ids=set()
        for ii,event in enumerate(events):
            ew=f'{loc}.interactions[{ii}]'
            if not isinstance(event,dict):ch.error(ew,'object required');continue
            if set(event)-{'id','type','actors','frame','target','holdFrames'}:ch.error(ew,'unsupported fields')
            if event.get('type')!='highFive':ch.error(ew,'unsupported interaction type')
            if not isinstance(event.get('id'),str) or event['id'] in event_ids:ch.error(ew,'duplicate or invalid event id')
            else:event_ids.add(event['id'])
            actors=event.get('actors')
            if not isinstance(actors,list) or len(actors)!=2 or actors[0]==actors[1] or any(a not in ids for a in actors):
                ch.error(ew,'actors must be two distinct scene character ids');continue
            fr=event.get('frame')
            if type(fr) is not int or fr<13 or fr>=duration:ch.error(ew,'contact frame must be >=13 and inside scene');continue
            hold=event.get('holdFrames',8)
            if type(hold) is not int or hold<0 or fr+hold>=duration:ch.error(ew,'invalid holdFrames')
            target=event.get('target')
            if not isinstance(target,dict) or set(target)!={'x','y'} or not all(number(v) for v in target.values()):ch.error(ew,'invalid target');continue
            # Ensure the two contact limbs can actually reach the shared world-space target.
            for actor in actors:
                character=ids[actor];kind=names.get(character.get('asset'))
                if kind not in ('human','dog'):continue
                motion=character.get('motion',[])
                at={k:character.get(k) for k in ('x','y','scale','facing')}
                if motion:
                    # Conservative bound: if motion is active, defer exact reachability to runtime IK test.
                    continue
                scale=at['scale'] or 1; facing=at['facing'] or 1
                sx,sy=(39,-219) if kind=='human' else (66,-110)
                start=(at['x']+sx*scale*facing, at['y']+sy*scale)
                reach=(101+103 if kind=='human' else 115+115)*scale
                d=hypot(target['x']-start[0],target['y']-start[1])
                if d>reach+0.1:ch.error(ew,f'{actor} contact target unreachable ({d:.1f}px > {reach:.1f}px)')
        camera=scene.get('camera',[])
        if not isinstance(camera,list):ch.error(loc+'.camera','list required');continue
        last=-1
        for ki,key in enumerate(camera):
            cw=f'{loc}.camera[{ki}]'
            if not isinstance(key,dict):ch.error(cw,'object required');continue
            if set(key)-{'frame','x','y','zoom'}:ch.error(cw,'unsupported fields')
            fr=key.get('frame')
            if type(fr) is not int or not 0<=fr<duration or fr<=last:ch.error(cw,'invalid camera frame')
            else:last=fr
            for prop in ('x','y','zoom'):
                if prop in key and (not number(key[prop]) or (prop=='zoom' and key[prop]<=0)):ch.error(cw,f'invalid {prop}')

    from validate_rigged import check_advanced
    check_advanced(ch, doc, video_path)
