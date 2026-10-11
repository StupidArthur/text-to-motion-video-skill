from validator_common import *

def check_elements(ch, elements, duration, where):
    ids = set()
    for ei, el in enumerate(elements):
        ew = f'{where}.elements[{ei}]'
        if not isinstance(el,dict) or el.get('type') not in TYPES:
            ch.error(ew, 'unsupported element type'); continue
        kind, eid = el['type'], el.get('id')
        if not isinstance(eid,str) or not re.fullmatch('[a-zA-Z0-9_-]+',eid):
            ch.error(ew,'invalid element id')
        elif eid in ids: ch.error(ew, 'duplicate element id')
        ids.add(eid)
        for field in TYPES[kind]:
            if field not in el: ch.error(ew,f'missing {field}')
            elif field not in ('text','fill','stroke') and (not num(el[field]) or (field in ('width','height','r','fontSize') and el[field]<=0)):
                ch.error(ew,f'invalid {field}')
            elif field in ('text','fill','stroke') and (not isinstance(el[field],str) or not el[field].strip()):
                ch.error(ew,f'invalid {field}')
        if set(el)-TYPES[kind]-EXTRA[kind]-{'id','type','motion','visibleFrom','visibleUntil'}:
            ch.error(ew, 'unsupported fields')
        if 'fontWeight' in el and (not num(el['fontWeight']) or not 100<=el['fontWeight']<=900):
            ch.error(ew,'invalid fontWeight')
        for optional in ('visibleFrom','visibleUntil'):
            if optional in el and (type(el[optional]) is not int or not 0<=el[optional]<=duration):
                ch.error(ew,f'invalid {optional}')
        if el.get('visibleFrom',0)>=el.get('visibleUntil',duration):
            ch.error(ew,'visibility window reversed')
        motion = el.get('motion',[])
        if not isinstance(motion,list):
            ch.error(ew,'motion must be an array'); continue
        last=-1
        for ki,kf in enumerate(motion):
            kw=f'{ew}.motion[{ki}]'
            if not isinstance(kf,dict): ch.error(kw,'invalid keyframe');continue
            frame=kf.get('frame')
            if type(frame) is not int or not 0<=frame<duration:
                ch.error(kw,'frame must be in scene bounds')
            elif frame<=last: ch.error(kw,'keyframes must increase')
            else: last=frame
            if not set(kf).intersection(MOTION): ch.error(kw,'empty keyframe')
            for prop,value in kf.items():
                if prop=='frame':continue
                if prop not in MOTION or not num(value) or (prop=='opacity' and not 0<=value<=1) or (prop=='scale' and value<0):
                    ch.error(kw,f'invalid {prop}')
