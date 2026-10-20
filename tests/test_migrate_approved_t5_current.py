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

    def test_manifest_root_selects_its_own_ratified_foundation(self):
        # Заміна --root не повинна потай брати D9 з директорії скрипта.
        # Справжню програму D4 проєктує чинний engine; mock тільки
        # фіксує шлях завантаження таблиці, не імітує SENS-обчислення.
        from unittest.mock import patch
        foundation = approved.engine.load_foundation(
            ROOT / "knowledge/d1-d11-foundation.json"
        )
        with tempfile.TemporaryDirectory(prefix="sens-root-provenance-") as temp:
            root = Path(temp)
            source = root / "program.lisp"
            original = SOURCE.read_bytes()
            source.write_bytes(original)
            with patch.object(approved.engine, "load_foundation",
                              return_value=foundation) as load:
                rel, payload, receipt = approved.migrate_one(
                    source, root, self.maps, original, source_era="current"
                )
            load.assert_called_with(root / "knowledge/d1-d11-foundation.json")
            self.assertEqual(rel, Path("program.sens"))
            self.assertEqual(receipt["physical_codec"], "T5M")
            self.assertEqual(receipt["semantic_oracle"], "NOT_VERIFIED")
            self.assertEqual(source.read_bytes(), original)
            self.assertTrue(approved.engine.decode_t5m_bytes(payload))

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

    def test_physical_and_bits_view_are_published_as_a_pair(self):
        before = SOURCE.read_bytes()
        rel, physical, _ = approved.migrate_one(
            SOURCE, ROOT, self.maps, before, source_era="current",
        )
        with tempfile.TemporaryDirectory(prefix="sens-pair-publish-") as temp:
            out = Path(temp)
            approved.publish_batch([(rel, physical)], out)
            self.assertEqual((out / rel).read_bytes(), physical)
            self.assertEqual(
                (out / rel.with_suffix("")).read_bytes(),
                VIEW.read_bytes(),
            )
            self.assertEqual(SOURCE.read_bytes(), before)
            with self.assertRaisesRegex(approved.engine.SensT5Error, "exists"):
                approved.publish_batch([(rel, physical)], out)
            self.assertEqual((out / rel).read_bytes(), physical)

    def test_later_view_collision_rolls_back_earlier_pair(self):
        _, physical, _ = approved.migrate_one(
            SOURCE, ROOT, self.maps, source_era="current",
        )
        with tempfile.TemporaryDirectory(prefix="sens-pair-rollback-") as temp:
            out = Path(temp)
            (out / "b").write_bytes(b"existing-user-data")
            with self.assertRaisesRegex(approved.engine.SensT5Error, "exists"):
                approved.publish_batch([
                    (Path("a.sens"), physical),
                    (Path("b.sens"), physical),
                ], out)
            self.assertFalse((out / "a.sens").exists())
            self.assertFalse((out / "a").exists())
            self.assertFalse((out / "b.sens").exists())
            self.assertEqual((out / "b").read_bytes(), b"existing-user-data")

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
