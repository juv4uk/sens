#!/usr/bin/env python3
"""Fail-closed, bounded Core1→D2/D3 physical T5 migration regression."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sens_t5_codec import SensT5Error, decode_bytes, encode_projection, encode_words

SCRIPT = ROOT / "tests" / "fixtures" / "core1-domain-canary" / "regenerate.py"
spec = importlib.util.spec_from_file_location("sens_core1_domain_canary", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class ExistingCore1DomainCanaryTests(unittest.TestCase):
    def test_actual_core1_helper_is_the_only_donor(self):
        source = (ROOT / "lib" / "core1.lisp").read_text(encoding="utf-8")
        self.assertEqual(len(mod.C1_SECOND.findall(source)), 1)
        words = mod.words_from_existing_core1()
        self.assertEqual(words[:3], ["10", "100", "00"])
        self.assertIn("011", words)  # CDR from current D3
        self.assertIn("111", words)  # CONS from current D3
        self.assertIn("001", words)  # QUOTE from current D3
        self.assertNotIn("10101010", words)  # historical LABEL is not smuggled
        self.assertTrue(all(set(w) <= set("01") for w in words))

    def test_same_stem_binary_is_real_and_exact(self):
        rendered, physical, expected_digest = mod.expected_artifacts()
        self.assertEqual(mod.PROJECTION.read_text(encoding="utf-8"), rendered)
        self.assertEqual(mod.PHYSICAL.read_bytes(), physical)
        self.assertEqual(decode_bytes(physical), mod.words_from_existing_core1())
        self.assertEqual(encode_projection(rendered), physical)
        self.assertEqual(mod.PROJECTION.stem, mod.PHYSICAL.stem)
        self.assertNotEqual(physical, rendered.encode("ascii"))
        self.assertEqual(len(expected_digest), 64)
        self.assertGreater(len(physical), 0)
        self.assertEqual(mod.verify_checked_in(), (len(physical), expected_digest))

    def test_no_guessed_symbols_or_historical_sid_as_modern_code(self):
        for bad in ("LABEL", "C1-SECOND", "10 111 00 X 01"):
            with self.subTest(bad=bad), self.assertRaises(SensT5Error):
                encode_projection(bad)
        # T5 is TRANSPORT, not semantic admission. An old 8-bit word is
        # physically valid but must NEVER be assigned modern D8 meaning.
        raw = ["10101010", "10"]
        self.assertEqual(decode_bytes(encode_words(raw)), raw)
        self.assertNotIn("10101010", mod.words_from_existing_core1())

    def test_corruption_fails_closed(self):
        physical = mod.PHYSICAL.read_bytes()
        with self.assertRaises(SensT5Error):
            decode_bytes(physical + bytes([243]))
        with self.assertRaises(SensT5Error):
            decode_bytes(physical + bytes([242]))  # obsolete/extra EOS22 tail

    def test_unratified_domain_coordinate_change_blocks_canary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lib").mkdir()
            (root / "knowledge").mkdir()
            (root / "lib" / "core1.lisp").write_bytes(
                (ROOT / "lib" / "core1.lisp").read_bytes()
            )
            foundation = json.loads(
                (ROOT / "knowledge" / "d1-d9-foundation.json").read_text(
                    encoding="utf-8"
                )
            )
            foundation["domains"]["D3"]["residents"]["100"] = "OTHER"
            (root / "knowledge" / "d1-d9-foundation.json").write_text(
                json.dumps(foundation), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "BLOCK"):
                mod.words_from_existing_core1(root)

    def test_unproved_core1_source_change_blocks_canary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lib").mkdir()
            (root / "knowledge").mkdir()
            historical = (ROOT / "lib" / "core1.lisp").read_text(encoding="utf-8")
            (root / "lib" / "core1.lisp").write_text(
                historical.replace("C1-SECOND", "C1-OTHER", 1), encoding="utf-8"
            )
            (root / "knowledge" / "d1-d9-foundation.json").write_bytes(
                (ROOT / "knowledge" / "d1-d9-foundation.json").read_bytes()
            )
            with self.assertRaisesRegex(ValueError, "BLOCK"):
                mod.words_from_existing_core1(root)


if __name__ == "__main__":
    unittest.main()
