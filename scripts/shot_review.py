#!/usr/bin/env python3
"""Generate honest shot QA requests; refuse to mark visual checks passed without review.

init: creates a JSON checklist with pending entries and frame evidence locations.
verify: ensures every requirement was reviewed, and specified evidence files exist.
"""
import argparse
import json
import sys
from pathlib import Path
from production_pipeline import load_contract, validate


def initial(story, acceptance):
    by_id={s['id']:s for s in story['shots']}
    out=[]
    for check in acceptance['checks']:
        shot=by_id[check['shotId']]
        start=shot['startFrame']; end=shot['endFrame']
        frames=sorted(set([start,(start+end-1)//2,end-1,check['expectedAtFrame']]))
        out.append({
            'checkId':check['id'], 'shotId':check['shotId'],
            'category':check['category'], 'criterion':check['criterion'],
            'requiresVisualReview':check['requiresVisualReview'],
            'evidenceFrames':frames, 'evidenceFiles':[],
            'status':'pending','reviewer':'','notes':''
        })
    return {'version':3, 'checks':out}

def verify(review, acceptance, base):
    failures=[]
    expected={c['id']:c for c in acceptance['checks']}
    records=review.get('checks') if isinstance(review,dict) else None
    if not isinstance(records,list):return ['review.checks must be an array']
    found=set()
    for record in records:
        cid=record.get('checkId') if isinstance(record,dict) else None
        if cid not in expected or cid in found:failures.append(f'invalid/duplicate check {cid}');continue
        found.add(cid)
        if record.get('status')!='passed':failures.append(f'{cid}: status not passed')
        if not isinstance(record.get('reviewer'),str) or not record['reviewer'].strip():
            failures.append(f'{cid}: reviewer required')
        if expected[cid].get('requiresVisualReview'):
            files=record.get('evidenceFiles')
            if not isinstance(files,list) or not files:
                failures.append(f'{cid}: visual review requires one or more real evidence files')
            else:
                for path in files:
                    p=Path(path)
                    if p.is_absolute() or '..' in p.parts or not (base/p).is_file():
                        failures.append(f'{cid}: invalid/missing evidence {path}')
    for cid in expected.keys()-found:failures.append(f'{cid}: missing review entry')
    return failures

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='cmd',required=True)
    init=sub.add_parser('init');init.add_argument('contract_dir',type=Path);init.add_argument('--output',type=Path,required=True)
    check=sub.add_parser('verify');check.add_argument('contract_dir',type=Path);check.add_argument('review_json',type=Path)
    args=parser.parse_args()
    try:
        story,bible,acceptance=load_contract(args.contract_dir)
        report=validate(story,bible,acceptance,args.contract_dir/'public')
        report.check()
        if args.cmd=='init':
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(json.dumps(initial(story,acceptance),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
            print(f'WROTE {args.output} — all reviews pending')
        else:
            doc=json.loads(args.review_json.read_text(encoding='utf-8'))
            failures=verify(doc,acceptance,args.review_json.parent)
            if failures:
                for failure in failures:print('BLOCKED',failure,file=sys.stderr)
                return 1
            print('PASS: every acceptance criterion has verified evidence and reviewer')
    except (OSError,ValueError) as exc:
        print('ERROR',exc,file=sys.stderr);return 1
    return 0
if __name__=='__main__':sys.exit(main())
