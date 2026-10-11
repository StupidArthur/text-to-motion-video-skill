#!/usr/bin/env python3
"""Self-test for validator semantics; runs offline with Python standard library."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from validate_scene import validate

SKILL = Path(__file__).resolve().parents[1]
DEMO = SKILL / "examples" / "v1-video.json"


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.demo = json.loads(DEMO.read_text(encoding="utf-8"))

    def test_demo_is_valid(self):
        ch = validate(self.demo, DEMO)
        self.assertEqual([], ch.errors)

    def test_invalid_timing(self):
        broken = copy.deepcopy(self.demo)
        broken["scenes"][0]["elements"][0]["motion"][1]["frame"] = -7
        ch = validate(broken, DEMO)
        self.assertTrue(ch.errors)

    def test_duplicate_element_id(self):
        broken = copy.deepcopy(self.demo)
        broken["scenes"][0]["elements"][1]["id"] = broken["scenes"][0]["elements"][0]["id"]
        ch = validate(broken, DEMO)
        self.assertTrue(any("duplicate" in msg for msg in ch.errors))

    def test_missing_audio(self):
        broken = copy.deepcopy(self.demo)
        broken["scenes"][0]["audio"] = {"file": "does-not-exist.wav"}
        ch = validate(broken, DEMO)
        self.assertTrue(any("missing audio asset" in msg for msg in ch.errors))

    def test_empty_scene(self):
        broken = copy.deepcopy(self.demo)
        broken["scenes"][0]["elements"] = []
        ch = validate(broken, DEMO)
        self.assertFalse(ch.errors)
        self.assertTrue(ch.warnings)

    def test_audio_path_traversal(self):
        broken = copy.deepcopy(self.demo)
        broken["scenes"][0]["audio"] = {"file": "../../secret.mp3"}
        ch = validate(broken, DEMO)
        self.assertTrue(any("unsafe filename" in msg for msg in ch.errors))


if __name__ == "__main__":
    unittest.main(verbosity=2)
