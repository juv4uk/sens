#!/usr/bin/env python3
"""Core-only regression tests for scripts/sens8-to-ladder.py."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sens8-to-ladder.py"
if not SCRIPT.exists():
    SCRIPT = Path(__file__).resolve().with_name("sens8-to-ladder.py")
spec = importlib.util.spec_from_file_location("sid8_domain_projection", SCRIPT)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


class DomainProjectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        (cls.root / "knowledge").mkdir()
        foundation = {
            "status": "owner-ratified",
            "domains": {
                "D3": {"width": 3, "residents": {"001": "QUOTE", "111": "CONS", "100": "CAR", "011": "CDR"}},
                "D4": {"width": 4, "residents": {"0010": "LAMBDA"}},
                "D5": {"width": 5, "residents": {"01010": "PLUS", "00011": "MACRO"}},
                "D8": {"width": 8, "residents": {"11110110": "DIVIDE"}},
            }
        }
        known = {
            1: ("quote", "DIRECT-CURRENT-IDENTITY", "D3:001 QUOTE"),
            4: ("cons", "DIRECT-CURRENT-IDENTITY", "D3:111 CONS"),
            5: ("car", "DIRECT-CURRENT-IDENTITY", "D3:100 CAR"),
            6: ("cdr", "DIRECT-CURRENT-IDENTITY", "D3:011 CDR"),
            8: ("lambda", "DIRECT-CURRENT-IDENTITY", "D4:0010 LAMBDA"),
            12: ("plus", "DIRECT-CURRENT-IDENTITY", "D5:01010 PLUS"),
            15: ("divide", "DIRECT-CURRENT-IDENTITY", "D8:11110110 DIVIDE"),
            10: ("defmacro", "CURRENT-PROJECTION-DERIVED", "D5:00011 MACRO + D4:0010 LAMBDA"),
        }
        rows = []
        for i in range(256):
            name, classification, target = known.get(i, (None, "BLANK-UNUSED-CELL", None))
            rows.append({"legacy_code": f"{i:08b}", "legacy_name": name,
                         "classification": classification, "current_target": target})
        (cls.root / "knowledge/d1-d9-foundation.json").write_text(json.dumps(foundation))
        (cls.root / "knowledge/sens8-current-coverage-v1.json").write_text(
            json.dumps({"status": "AUDIT-COMPLETE", "rows": rows}))
        cls.mapping, cls.all_rows, _ = m.load_authorities(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_exact_heads_and_preservation(self):
        src = '; 00000101 intact\n(00000100 (00000101 x) (00000110 y))\n"00000100"\n'
        out, counts, blocks = m.project(src, self.mapping, self.all_rows, "legacy")
        self.assertEqual(blocks, [])
        self.assertEqual(counts["replaced"], 3)
        self.assertEqual(out, '; 00000101 intact\n(D3:111 (D3:100 x) (D3:011 y))\n"00000100"\n')

    def test_idempotence(self):
        src = '(D3:111 (D3:100 x) (D3:011 y))'
        result, counts, blocks = m.project(src, self.mapping, self.all_rows, "auto")
        self.assertEqual((result, counts["replaced"], blocks), (src, 0, []))

    def test_w8_target_remains_explicitly_typed(self):
        out, _, blocks = m.project('(00001111 a)', self.mapping, self.all_rows, 'legacy')
        self.assertEqual(out, '(D8:11110110 a)')
        self.assertEqual(blocks, [])

    def test_unproved_compound_fails(self):
        out, _, blocks = m.project('(00001010 x)', self.mapping, self.all_rows, 'legacy')
        self.assertIsNone(out)
        self.assertIn('NO_SINGLE_RATIFIED_SUCCESSOR', blocks[0]['reason'])

    def test_ambiguous_era_fails(self):
        out, _, blocks = m.project('(00000100 x)', self.mapping, self.all_rows, 'auto')
        self.assertIsNone(out)
        self.assertEqual(blocks[0]['reason'], 'AMBIGUOUS_W8_SOURCE_ERA')

    def test_data_and_quoted_bits_fail_closed(self):
        for src in ('(00000100 00000101)', "'(00000100 x)", '(D3:001 (00000100 x))'):
            with self.subTest(src=src):
                out, _, blocks = m.project(src, self.mapping, self.all_rows, 'legacy')
                self.assertIsNone(out)
                self.assertEqual(blocks[0]['reason'], 'UNPROVEN_W8_DATA_OR_VALUE')

    def test_parentheses_and_comments(self):
        for src in ('(00000100 x', '00000100)', '#| unfinished', '"unfinished'):
            with self.subTest(src=src):
                with self.assertRaises(m.Blocked):
                    m.project(src, self.mapping, self.all_rows, 'legacy')

    def test_comment_and_strings_do_not_create_mappings(self):
        src = '(D3:111 "00000001") ; (00000100 x)\n#| (00000101 x) |#'
        out, counts, blocks = m.project(src, self.mapping, self.all_rows, 'legacy')
        self.assertEqual((out, counts['replaced'], blocks), (src, 0, []))


if __name__ == '__main__':
    unittest.main()
