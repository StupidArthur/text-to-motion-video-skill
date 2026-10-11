"""Contract validator, runtime compilation and honest quality-gate regression tests."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from production_pipeline import load_contract,validate,compile_project
from shot_review import initial,verify

ROOT=Path(__file__).resolve().parents[1]
EXAMPLE=ROOT/'examples'/'scripted-cottage'

class ProductionTests(unittest.TestCase):
    def setUp(self):
        self.story,self.bible,self.accepts=load_contract(EXAMPLE)
    def report(self,story=None,bible=None,checks=None,root=None):
        return validate(story or self.story,bible or self.bible,checks or self.accepts,root or EXAMPLE/'public')
    def test_demo_contract_valid(self):
        self.assertFalse(self.report().errors)
    def test_missing_asset_fails_not_invented(self):
        b=copy.deepcopy(self.bible); b['assets'][0]['file']='unmade.svg'
        self.assertTrue(any('missing asset' in e for e in self.report(bible=b).errors))
    def test_path_traversal_rejected(self):
        b=copy.deepcopy(self.bible);b['assets'][0]['file']='../forest.svg'
        self.assertTrue(any('unsafe' in e for e in self.report(bible=b).errors))
    def test_shot_gaps_rejected(self):
        s=copy.deepcopy(self.story);s['shots'][1]['startFrame']+=1
        self.assertTrue(any('contiguous' in e for e in self.report(story=s).errors))
    def test_silent_non_progressing_scene_rejected(self):
        s=copy.deepcopy(self.story);s['shots'][0]['afterState']=s['shots'][0]['beforeState']
        self.assertTrue(any('different' in e for e in self.report(story=s).errors))
    def test_unknown_character_rejected(self):
        s=copy.deepcopy(self.story);s['shots'][0]['characterIds']=['invented']
        self.assertTrue(any('unknown character' in e for e in self.report(story=s).errors))
    def test_missing_action_acceptance_rejected(self):
        a=copy.deepcopy(self.accepts);a['checks'][0]['category']='visual'
        self.assertTrue(any('action acceptance' in e for e in self.report(checks=a).errors))
    def test_keyframe_outside_shot_rejected(self):
        s=copy.deepcopy(self.story);s['shots'][0]['layers'][-1]['motion'][1]['frame']=75
        self.assertTrue(any('motion frames' in e for e in self.report(story=s).errors))
    def test_embedded_script_svg_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'forest.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>')
            for name in ('door.svg','red-hood.svg'):(root/name).write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
            self.assertTrue(any('disallowed' in e for e in self.report(root=root).errors))
    def test_camera_out_of_bounds(self):
        s=copy.deepcopy(self.story);s['shots'][1]['camera'][1]['frame']=75
        self.assertTrue(any('invalid camera' in e for e in self.report(story=s).errors))
    def test_no_sneaky_scene_overlay_override(self):
        s=copy.deepcopy(self.story);s['shots'][0]['sceneOverlay']={'durationFrames':999}
        self.assertTrue(any('sceneOverlay' in e for e in self.report(story=s).errors))
    def test_compile_copies_real_art_and_preserves_timeline(self):
        with tempfile.TemporaryDirectory() as td:
            project=Path(td); out=project/'video.json'
            doc=compile_project(self.story,self.bible,self.accepts,EXAMPLE/'public',out,True)
            self.assertEqual(sum(s['durationFrames'] for s in doc['scenes']),150)
            self.assertTrue((project/'public'/'red-hood.svg').exists())
            self.assertEqual(doc['scenes'][0]['layers'][1]['motion'][1]['dx'],830)
            # Compiled output must validate under legacy V1/V2 scene validator.
            from validate_scene import validate as validate_videos
            self.assertFalse(validate_videos(doc,out).errors)
    def test_review_gate_rejects_pending(self):
        r=initial(self.story,self.accepts)
        self.assertTrue(verify(r,self.accepts,EXAMPLE))
    def test_review_gate_requires_evidence(self):
        r=initial(self.story,self.accepts)
        for c in r['checks']:
            c.update(status='passed',reviewer='human reviewer',evidenceFiles=['no-such-frame.png'])
        self.assertTrue(any('missing evidence' in e for e in verify(r,self.accepts,EXAMPLE)))
    def test_review_gate_can_pass_on_real_files(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);(folder/'frame.png').write_bytes(b'frame')
            r=initial(self.story,self.accepts)
            for c in r['checks']:
                c.update(status='passed',reviewer='reviewer',evidenceFiles=['frame.png'])
            self.assertEqual([],verify(r,self.accepts,folder))

if __name__=='__main__':unittest.main(verbosity=2)
