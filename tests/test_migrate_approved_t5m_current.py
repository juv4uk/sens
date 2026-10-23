#!/usr/bin/env python3
"""Чинний manifest-мігратор: позитивний фізичний T5M і негативні свідки.

Тести НЕ виконують SENS-обчислення і НЕ дозволяють реліз; вони доводять
коректний фізичний шлях для наявної D4-програми без переписування Lisp.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/migrate-approved-t5m.py"
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

    def test_manifest_rejects_lexical_traversal_and_symlink_parent(self):
        # Перевіряємо вхідне ім'я, не результат os.path.normpath.
        with tempfile.TemporaryDirectory(prefix="sens-manifest-path-") as tmp:
            root = Path(tmp) / "джерела"
            root.mkdir()
            directory = root / "програми"
            directory.mkdir()
            source = directory / "програма.lisp"
            # Реальна українська програма, а не синтетичний текст.
            source.write_bytes(SOURCE.read_bytes())
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            manifest = Path(tmp) / "manifest.json"

            def check(path: str):
                manifest.write_text(json.dumps({"files": [
                    {"path": path, "sha256": digest},
                ]}, ensure_ascii=False), encoding="utf-8")
                return approved.load_manifest(manifest, root)

            self.assertEqual(check("програми/програма.lisp"), [
                (Path("програми/програма.lisp"), digest),
            ])
            for invalid in (
                "програми/../програми/програма.lisp",
                "програми/./програма.lisp",
                "./програми/програма.lisp",
                "програми//програма.lisp",
                "програми\\\\програма.lisp",
                "../джерела/програми/програма.lisp",
                "/програми/програма.lisp",
                "програми/програма.LISP",
            ):
                with self.subTest(path=invalid):
                    with self.assertRaisesRegex(ValueError, "safe relative"):
                        check(invalid)
            (root / "посилання").symlink_to(directory, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink component"):
                check("посилання/програма.lisp")

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

    def test_nested_symlink_cannot_redirect_current_t5m_outside_mirror(self):
        # Попередня перевірка лише target.parent не виявляла
        # symlink на проміжному рівні й створювала файли за межами mirror.
        _, physical, _ = approved.migrate_one(
            SOURCE, ROOT, self.maps, source_era="current",
        )
        with tempfile.TemporaryDirectory(prefix="sens-t5m-path-safety-") as temp:
            base = Path(temp)
            mirror = base / "mirror"
            outside = base / "outside"
            mirror.mkdir()
            outside.mkdir()
            (mirror / "alias").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(approved.engine.SensT5Error, "symlink"):
                approved.publish_batch([
                    (Path("alias/nested/program.sens"), physical),
                ], mirror)
            self.assertFalse((outside / "nested").exists())
            self.assertFalse((outside / "program.sens").exists())
            self.assertFalse((mirror / "alias/nested/program.sens").exists())
            # Звичайна вкладена тека продовжує працювати.
            approved.publish_batch([
                (Path("ordinary/nested/program.sens"), physical),
            ], mirror)
            self.assertEqual(
                (mirror / "ordinary/nested/program.sens").read_bytes(), physical
            )
            self.assertTrue((mirror / "ordinary/nested/program").is_file())

    def test_relative_path_escape_rejected_without_any_output(self):
        _, physical, _ = approved.migrate_one(
            SOURCE, ROOT, self.maps, source_era="current",
        )
        with tempfile.TemporaryDirectory(prefix="sens-t5m-path-escape-") as temp:
            mirror = Path(temp) / "mirror"
            mirror.mkdir()
            for rel in (Path("../escape.sens"), Path("/tmp/escape.sens")):
                with self.subTest(rel=str(rel)):
                    with self.assertRaisesRegex(
                        approved.engine.SensT5Error, "safe relative"
                    ):
                        approved.publish_batch([(rel, physical)], mirror)
            self.assertEqual(list(mirror.iterdir()), [])
            self.assertFalse((Path(temp) / "escape.sens").exists())

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

    def test_failed_nested_batch_removes_new_directories(self):
        # Другий фізичний носій пошкоджено: нуль файлів І каталогів.
        _, physical, _ = approved.migrate_one(
            SOURCE, ROOT, self.maps, source_era="current",
        )
        with tempfile.TemporaryDirectory(prefix="sens-nested-rollback-") as temp:
            out = Path(temp) / "mirror"
            with self.assertRaises(approved.engine.SensT5Error):
                approved.publish_batch([
                    (Path("first/nested/program.sens"), physical),
                    (Path("second/broken.sens"), b"\xff"),
                ], out)
            self.assertFalse(out.exists())

    def test_legacy_sid8_is_not_an_executable_era(self):
        with self.assertRaisesRegex(approved.engine.MigrationError,
                                    "HISTORICAL_SOURCE_ERA_DISABLED"):
            approved.migrate_one(SOURCE, ROOT, self.maps, source_era="legacy")

    def test_unrepresentable_codepoint_blocks_not_coerces_to_text7(self):
        with tempfile.TemporaryDirectory(prefix="sens-t5m-negative-") as temp:
            root = Path(temp)
            # Тимчасове дерево зберігає власне джерело ратифікованих
            # доменів: мігратор не має потай підвантажувати глобальний ROOT.
            foundation = root / "knowledge/d1-d11-foundation.json"
            foundation.parent.mkdir(parents=True)
            foundation.write_bytes(
                (ROOT / "knowledge/d1-d11-foundation.json").read_bytes()
            )
            source = root / "неприпустиме.lisp"
            source.write_text("(перше ☃)\n", encoding="utf-8")
            with self.assertRaises((
                approved.engine.MigrationError,
                approved.engine.SensT5Error,
            )):
                approved.migrate_one(source, root, self.maps, source_era="current")


if __name__ == "__main__":
    unittest.main()
