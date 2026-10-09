#!/usr/bin/env python3
"""Negative research gates: D10 notation witnesses never imply ratification."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_d10_music_enharmonic_primary.py"
spec = importlib.util.spec_from_file_location("d10_music_review", SCRIPT)
assert spec and spec.loader
music = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = music
spec.loader.exec_module(music)


class D10MusicSourceReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="d10-music-hold-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for rel in (music.SOURCE, music.D10, music.FOUNDATION):
            destination = self.root / rel.relative_to(ROOT)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(rel, destination)
        self.review_path = self.root / music.SOURCE.relative_to(ROOT)
        self.inventory_path = self.root / music.D10.relative_to(ROOT)

    def review(self):
        return json.loads(self.review_path.read_text(encoding="utf-8"))

    def save(self, data):
        self.review_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def test_two_unselected_meanings_two_model_exhaustive_and_zero_d10_growth(self):
        result = music.verify(self.root)
        self.assertEqual(result["candidate_count"], 2)
        self.assertEqual(result["two_model_bounded_pairs"], 11025)
        self.assertGreaterEqual(result["evidence_examples"], 12)
        self.assertEqual(result["selected_delta"], 0)
        self.assertEqual(result["ratified"], 0)
        self.assertEqual(result["external_source_oracle"], "NOT_EXECUTED")
        self.assertEqual(result["D1_D9_behavioral_dedup"], "REVIEW_REQUIRED")

    def test_cross_octave_enharmonic_falsifier(self):
        self.assertEqual(music.enharmonic_direct(["B", 1, 3], ["C", 0, 4]), 1)
        self.assertEqual(music.enharmonic_direct(["C", 0, 4], ["C", 0, 4]), 0)
        self.assertEqual(music.enharmonic_direct(["C", 0, 4], ["C", 0, 5]), 0)
        self.assertEqual(music.notated_interval(["C", 0, 4], ["D", -2, 4]), (1, 0))
        self.assertEqual(music.notated_interval(["C", 0, 4], ["F", -1, 4]), (3, 4))

    def test_changed_approved_witness_must_block(self):
        item = self.review()
        item["candidates"][0]["positive_witnesses"][0]["expected"] = 0
        self.save(item)
        with self.assertRaisesRegex(music.ReviewBlocked, "WITNESS"):
            music.verify(self.root)

    def test_bad_falsifier_must_block(self):
        item = self.review()
        item["candidates"][1]["falsifiers"][0]["forbid"] = [2, 4]
        self.save(item)
        with self.assertRaisesRegex(music.ReviewBlocked, "FALSIFIER"):
            music.verify(self.root)

    def test_owner_review_cannot_be_spoofed_as_selected_coordinate(self):
        for key, payload in [
            ("selected", True), ("ratified", True), ("coordinate", "0010101010"),
            ("decision", "SELECT-D10"), ("oracle_status", "EXTERNAL-CONFORMER-PASS"),
        ]:
            with self.subTest(key=key):
                item = self.review()
                item["candidates"][0][key] = payload
                self.save(item)
                with self.assertRaisesRegex(music.ReviewBlocked, "REVIEW"):
                    music.verify(self.root)
                self.save(json.loads(music.SOURCE.read_text(encoding="utf-8")))

    def test_counter_minting_selection_and_ratification_blocked(self):
        for key, value in (("selected_added", 1), ("ratified_added", 1),
                           ("coordinates_assigned", 1), ("physical_sens_written", 1)):
            with self.subTest(key=key):
                item = self.review()
                item["accounting"][key] = value
                self.save(item)
                with self.assertRaisesRegex(music.ReviewBlocked, "COUNT"):
                    music.verify(self.root)
                self.save(json.loads(music.SOURCE.read_text(encoding="utf-8")))

    def test_changed_ratified_foundation_or_duplicate_selected_meaning_blocked(self):
        f = self.root / music.FOUNDATION.relative_to(ROOT)
        f.write_bytes(f.read_bytes() + b"\n; forbidden mutation\n")
        with self.assertRaisesRegex(music.ReviewBlocked, "AUTHORITY"):
            music.verify(self.root)
        shutil.copyfile(music.FOUNDATION, f)
        inv = json.loads(self.inventory_path.read_text(encoding="utf-8"))
        inv["rows"][0]["semantic_name"] = music.NAMES[0]
        self.inventory_path.write_text(json.dumps(inv, ensure_ascii=False), encoding="utf-8")
        with self.assertRaisesRegex(music.ReviewBlocked, "DEDUP"):
            music.verify(self.root)

    def test_microtone_out_of_scope_and_invalid_pitch_type_rejected(self):
        for value in (["C", 0.5, 4], ["C", True, 4], ["C", 3, 4],
                      ["C", 0, 10], ["X", 0, 4], ["C", 0, "4"]):
            with self.subTest(value=value), self.assertRaises(music.ReviewBlocked):
                music.pitch(value)


if __name__ == "__main__":
    unittest.main()
