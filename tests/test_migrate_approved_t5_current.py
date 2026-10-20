#!/usr/bin/env python3
"""Чинний manifest-мігратор: позитивний фізичний T5M і негативні свідки.

Тести НЕ виконують SENS-обчислення і НЕ дозволяють реліз; вони доводять
коректний фізичний шлях для наявної D4-програми без переписування Lisp.
"""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/migrate-approved-t5.py"
VIEW = ROOT / "tests/fixtures/migration-d4-selector-cohort/caar"
SOURCE = VIEW.with_suffix(".lisp")
SPEC = importlib.util.spec_from_file_location("sens_approved_t5m_test", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
approved = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = approved
SPEC.loader.exec_module(approved)


class CurrentManifestMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.maps = approved.load_engine_maps(ROOT)

    def test_ratified_d1_d11_authority(self):
        foundation = approved.engine.load_foundation(
            ROOT / "knowledge/d1-d11-foundation.json"
        )
        self.assertEqual(len(foundation["domains"]["D10"]["residents"]), 1024)
        self.assertEqual(len(self.maps), 3)

    def test_proven_d4_fixture_preserves_exact_t5m_words_without_source_write(self):
        before = SOURCE.read_bytes()
        expected_words = VIEW.read_text(encoding="ascii").strip().split(" ")
        rel, physical, receipt = approved.migrate_one(
            SOURCE, ROOT, self.maps, before, source_era="current",
            zig_binary=None,
        )
        self.assertEqual(rel.as_posix(),
                         "tests/fixtures/migration-d4-selector-cohort/caar.sens")
        self.assertEqual(approved.engine.decode_t5m_bytes(physical), expected_words)
        self.assertEqual(receipt["physical_codec"], "T5M")
        self.assertEqual(receipt["physical_producer"], "REFERENCE_PREVIEW_ONLY")
        self.assertEqual(receipt["semantic_oracle"], "NOT_VERIFIED")
        self.assertEqual(receipt["source_sha256"], hashlib.sha256(before).hexdigest())
        self.assertEqual(SOURCE.read_bytes(), before)

    def test_legacy_sid8_is_not_an_executable_era(self):
        with self.assertRaisesRegex(approved.engine.MigrationError,
                                    "HISTORICAL_SOURCE_ERA_DISABLED"):
            approved.migrate_one(SOURCE, ROOT, self.maps, source_era="legacy")

    def test_unrepresentable_codepoint_blocks_not_coerces_to_text7(self):
        with tempfile.TemporaryDirectory(prefix="sens-t5m-negative-") as temp:
            root = Path(temp)
            source = root / "неприпустиме.lisp"
            source.write_text("(перше ☃)\n", encoding="utf-8")
            with self.assertRaises((
                approved.engine.MigrationError,
                approved.engine.SensT5Error,
            )):
                approved.migrate_one(source, root, self.maps, source_era="current")


if __name__ == "__main__":
    unittest.main()
