"""V2 schema regression tests (standard library only)."""
import copy
import json
import unittest
from pathlib import Path
from validate_scene import validate

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / 'assets' / 'remotion-starter' / 'video.json'
V1 = ROOT / 'examples' / 'v1-video.json'

class V2ValidationTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads(V2.read_text(encoding='utf-8'))

    def check(self, document):
        return validate(document, V2)

    def test_v1_is_backward_compatible(self):
        self.assertEqual(validate(json.loads(V1.read_text(encoding='utf-8')), V1).errors, [])

    def test_v2_demo_passes(self):
        self.assertEqual(self.check(self.doc).errors, [])

    def test_unknown_asset(self):
        broken=copy.deepcopy(self.doc)
        broken['scenes'][0]['characters'][0]['asset']='not-a-real-rig'
        self.assertTrue(any('unknown character asset' in x for x in self.check(broken).errors))

    def test_invalid_action(self):
        broken=copy.deepcopy(self.doc)
        broken['scenes'][0]['characters'][0]['actions'][0]['name']='fly'
        self.assertTrue(any('unsupported action' in x for x in self.check(broken).errors))

    def test_unreachable_contact(self):
        broken=copy.deepcopy(self.doc)
        broken['scenes'][2]['interactions'][0]['target']={'x':1800,'y':70}
        self.assertTrue(any('unreachable' in x for x in self.check(broken).errors))

    def test_invalid_camera(self):
        broken=copy.deepcopy(self.doc)
        broken['scenes'][3]['camera'][1]['zoom']=-2
        self.assertTrue(any('invalid zoom' in x for x in self.check(broken).errors))

if __name__=='__main__':unittest.main()
