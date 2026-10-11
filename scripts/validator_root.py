from validator_common import *
from validator_elements import check_elements

def validate(doc,path):
    ch=Check()
    if not isinstance(doc,dict) or not isinstance(doc.get('meta'),dict):
        ch.error('$','meta object required');return ch
    m=doc['meta']
    for k in ('width','height','fps'):
        if type(m.get(k)) is not int or m[k]<=0:ch.error('meta',f'invalid {k}')
    if not isinstance(m.get('title'),str) or not m['title'].strip():ch.error('meta','title required')
    if not isinstance(doc.get('scenes'),list) or not doc['scenes']:
        ch.error('$','scenes required');return ch
    audio(ch,m.get('music'),'meta.music',path)
    ids=set()
    for i,scene in enumerate(doc['scenes']):
        loc=f'scenes[{i}]'
        if not isinstance(scene,dict):ch.error(loc,'invalid scene');continue
        sid=scene.get('id')
        if not isinstance(sid,str) or not re.fullmatch('[A-Za-z0-9_-]+',sid):ch.error(loc,'invalid id')
        elif sid in ids:ch.error(loc,'duplicate scene id')
        ids.add(sid)
        duration=scene.get('durationFrames')
        if type(duration) is not int or duration<=0:ch.error(loc,'invalid duration');continue
        audio(ch,scene.get('audio'),loc,path)
        els=scene.get('elements')
        if not isinstance(els,list):ch.error(loc,'elements must be array');continue
        if not els:ch.warn(loc,'scene has no elements')
        check_elements(ch,els,duration,loc)
    return ch
