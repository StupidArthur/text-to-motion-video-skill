"""Regression and negative-input tests for complete hierarchical rig & props DSL."""
import copy
import json
import unittest
from pathlib import Path
from validate_scene import validate

ROOT=Path(__file__).resolve().parents[1]
EXAMPLE=ROOT/'examples'/'custom-rig'/'video.json'
V1=ROOT/'examples'/'v1-video.json'
V2=ROOT/'assets'/'remotion-starter'/'video.json'

class AdvancedValidationTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads(EXAMPLE.read_text())
    def check(self,mutate):
        value=copy.deepcopy(self.data)
        mutate(value)
        return validate(value,EXAMPLE).errors
    def test_demo_valid(self):
        self.assertEqual(validate(self.data,EXAMPLE).errors,[])
    def test_v1_valid(self):
        self.assertEqual(validate(json.loads(V1.read_text()),V1).errors,[])
    def test_v2_valid(self):
        self.assertEqual(validate(json.loads(V2.read_text()),V2).errors,[])
    def test_duplicate_bone(self):
        def mutate(j):j['characterAssets'][0]['rig']['bones'][1]['id']='root'
        self.assertTrue(any('duplicate bone' in x for x in self.check(mutate)))
    def test_cycle_detected(self):
        def mutate(j):j['characterAssets'][0]['rig']['bones'][0]['parent']='head'
        self.assertTrue(any('cycle' in x for x in self.check(mutate)))
    def test_missing_parent(self):
        def mutate(j):j['characterAssets'][0]['rig']['bones'][2]['parent']='unknown'
        self.assertTrue(any('unknown parent' in x for x in self.check(mutate)))
    def test_bad_ik_chain(self):
        def mutate(j):j['characterAssets'][0]['rig']['ikChains'][0]['effector']='head.eyes'
        self.assertTrue(any('IK effector' in x for x in self.check(mutate)))
    def test_bad_joint(self):
        def mutate(j):j['scenes'][0]['characters'][0]['jointActions'][0]['joints']['not-bone']=[{'frame':0,'angle':10}]
        self.assertTrue(any('unknown bone joint' in x for x in self.check(mutate)))
    def test_frame_outside_action(self):
        def mutate(j):j['scenes'][0]['characters'][0]['jointActions'][0]['joints']['tail'][1]['frame']=999
        self.assertTrue(any('joint frame out' in x for x in self.check(mutate)))
    def test_missing_svg_asset(self):
        def mutate(j):j['characterAssets'][0]['rig']['bones'][-1]['visual']['file']='missing.svg'
        self.assertTrue(any('missing SVG asset' in x for x in self.check(mutate)))
    def test_path_traversal(self):
        def mutate(j):j['characterAssets'][0]['rig']['bones'][-1]['visual']['file']='../../private.svg'
        self.assertTrue(any('unsafe SVG filename' in x for x in self.check(mutate)))
    def test_unknown_prop(self):
        def mutate(j):j['scenes'][0]['attachments'][0]['prop']='broken'
        self.assertTrue(any('unknown prop' in x for x in self.check(mutate)))
    def test_unknown_anchor(self):
        def mutate(j):j['scenes'][0]['attachments'][0]['anchor']='fake.anchor'
        self.assertTrue(any('unknown attachment anchor' in x for x in self.check(mutate)))
    def test_release_window(self):
        def mutate(j):j['scenes'][0]['attachments'][0]['releaseEnd']=130
        self.assertTrue(any('invalid releaseEnd' in x for x in self.check(mutate)))
    def test_overlapping_attachments(self):
        def mutate(j):
            v=copy.deepcopy(j['scenes'][0]['attachments'][0]);v['id']='another'
            j['scenes'][0]['attachments'].append(v)
        self.assertTrue(any('overlapping prop attachments' in x for x in self.check(mutate)))
    def test_unsupported_behavior(self):
        def mutate(j):j['scenes'][0]['characters'][0]['behaviors'][0]['type']='teleport'
        self.assertTrue(any('unsupported behavior' in x for x in self.check(mutate)))

if __name__=='__main__':unittest.main(verbosity=2)
