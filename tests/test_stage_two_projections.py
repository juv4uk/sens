"""Regression tests for provisional SENS name.lisp + name staging (no name.sens)."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
IMPL = ROOT / "scripts/stage-two-projections.py"
SPEC = importlib.util.spec_from_file_location("stage_two_projections", IMPL)
assert SPEC and SPEC.loader
pair = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pair)


class StageTwoProjectionsTests(unittest.TestCase):
    BRANCH = "tests/fixtures/migration-d1-cond-cohort/branch.lisp"

    def test_current_d1_d11_maps_do_not_restore_sid8(self):
        data, my, upper, text7 = pair.migration_maps()
        self.assertEqual(len(data["domains"]["D10"]["residents"]), 1024)
        self.assertEqual(len((data, my, upper, text7)), 4)
        self.assertIn("keyboard-v2", text7)
        self.assertTrue(pair.BITS.fullmatch("0101010101"))

    def test_current_exact_word_widths_exclude_d11_proposals(self):
        # D1–D10 are eligible word widths; D11 is catalogue-only.
        # D12+ can carry exact mathematical words, but these bytes alone
        # cannot prove a callable identity or authorize semantic execution.
        for width in range(1, 11):
            with self.subTest(width=width):
                self.assertIsNotNone(pair.BITS.fullmatch("0" * width))
        # D12 — перший числовий домен за чинною ратифікацією; D11 не числовий.
        for width in (11, 16, 23, 25, 32, 47, 49, 95, 97, 191, 193):
            with self.subTest(rejected_width=width):
                self.assertIsNone(pair.BITS.fullmatch("0" * width))
        for width in (12, 24, 48, 96, 192):
            with self.subTest(math_width=width):
                self.assertIsNotNone(pair.BITS.fullmatch("0" * width))
        self.assertIsNone(pair.BITS.fullmatch("0" * 24 + "2"))
        self.assertIsNone(pair.BITS.fullmatch("0" * 24 + " "))

    def test_legacy_source_era_cannot_reanimate_retired_bridge(self):
        with tempfile.TemporaryDirectory(prefix="sens-two-legacy-") as td:
            mirror = Path(td) / "mirror"
            with self.assertRaisesRegex(pair.ProjectionBlocked,
                                        "HISTORICAL_SOURCE_ERA_DISABLED"):
                pair.stage(ROOT, mirror, [self.BRANCH], "legacy", True)
            self.assertFalse(mirror.exists())

    def test_existing_uk_fixture_roundtrips_without_packing(self):
        with tempfile.TemporaryDirectory(prefix="sens-two-test-") as td:
            mirror = Path(td) / "mirror"
            result = pair.stage(ROOT, mirror, [self.BRANCH], "auto", True)
            self.assertEqual(result["summary"]["files_created"], 2)
            self.assertEqual(result["semantic_oracle"], "NOT_VERIFIED")
            self.assertFalse(result["physical_codec_invoked"])
            self.assertEqual(result["third_file"],
                             "name.sens PENDING verified Zig/T5M physical encoding")
            self.assertFalse(result["release_admitted"])
            self.assertFalse(list(mirror.rglob("*.sens")))
            source = ROOT / self.BRANCH
            uk = mirror / self.BRANCH
            view = uk.with_suffix("")
            self.assertEqual(uk.read_bytes(), source.read_bytes())
            self.assertEqual(
                view.read_bytes(),
                (source.with_suffix("").read_bytes()),
            )
            self.assertTrue(view.read_bytes().endswith(b"\n"))
            self.assertNotIn(b"2", view.read_bytes())

    def test_comment_changes_do_not_change_executable_two_projections(self):
        # The inverse concerns the program, not the original Lisp bytes.
        # Unicode numbers and non-Ukrainian text inside comments are inert.
        with tempfile.TemporaryDirectory(prefix="sens-two-comment-") as td:
            base = Path(td)
            root = base / "source"
            root.mkdir()
            source = root / "програма.lisp"
            program = (ROOT / self.BRANCH).read_text(encoding="utf-8")
            original = "; English note ٢ -- not an executable atom\n" + program
            source.write_text(original, encoding="utf-8")
            mirror = base / "mirror"
            report = pair.stage(root, mirror, ["програма.lisp"], "auto", True)
            self.assertFalse(report["release_admitted"])
            self.assertEqual(report["semantic_oracle"], "NOT_VERIFIED")
            self.assertEqual(source.read_text(encoding="utf-8"), original)
            self.assertEqual((mirror / "програма.lisp").read_text(encoding="utf-8"), program)
            self.assertEqual(
                (mirror / "програма").read_bytes(),
                (ROOT / self.BRANCH).with_suffix("").read_bytes(),
            )
            self.assertFalse((mirror / "програма.sens").exists())

    def test_komentari_ne_zminyuyut_programu_i_ne_potraplyayut_u_kodek(self):
        # Одна програма з різним оформленням дає ту саму точну проєкцію.
        with tempfile.TemporaryDirectory(prefix="sens-two-comments-") as td:
            root = Path(td) / "input"
            root.mkdir()
            source = root / "branch.lisp"
            original = ("; Це коментар, а не SENS-команда\n"
                        + (ROOT / self.BRANCH).read_text(encoding="utf-8"))
            source.write_text(original, encoding="utf-8")
            mirror = Path(td) / "mirror"
            report = pair.stage(root, mirror, ["branch.lisp"], "current", True)
            self.assertEqual(report["summary"]["files_created"], 2)
            self.assertEqual((mirror / "branch.lisp").read_bytes(),
                             (ROOT / self.BRANCH).read_bytes())
            self.assertEqual((mirror / "branch").read_bytes(),
                             (ROOT / self.BRANCH).with_suffix("").read_bytes())
            self.assertEqual(source.read_text(encoding="utf-8"), original)
            self.assertFalse((mirror / "branch.sens").exists())
            self.assertFalse(report["release_admitted"])

    def test_preview_creates_nothing(self):
        with tempfile.TemporaryDirectory(prefix="sens-two-test-") as td:
            mirror = Path(td) / "mirror"
            result = pair.stage(ROOT, mirror, [self.BRANCH], "auto", False)
            self.assertEqual(result["summary"]["files_created"], 0)
            self.assertEqual(result["summary"]["would_create"], 2)
            self.assertFalse(mirror.exists())

    def test_repeated_stage_refuses_to_clobber_both_files(self):
        with tempfile.TemporaryDirectory(prefix="sens-two-test-") as td:
            mirror = Path(td) / "mirror"
            pair.stage(ROOT, mirror, [self.BRANCH], "auto", True)
            original = (mirror / self.BRANCH).read_bytes()
            with self.assertRaises(pair.ProjectionBlocked):
                pair.stage(ROOT, mirror, [self.BRANCH], "auto", True)
            self.assertEqual((mirror / self.BRANCH).read_bytes(), original)

    def test_failed_second_projection_rolls_back_files_and_new_directories(self):
        # Помилка другої проєкції не залишає файлів та каталогів.
        with tempfile.TemporaryDirectory(prefix="sens-two-atomic-") as td:
            mirror = Path(td) / "mirror"
            source = ROOT / self.BRANCH
            original = source.read_bytes()
            publish = pair.publish_new
            calls = 0

            def interrupted(target, content):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("імітація помилки другого запису")
                publish(target, content)

            with patch.object(pair, "publish_new", side_effect=interrupted):
                with self.assertRaisesRegex(OSError, "другого запису"):
                    pair.stage(ROOT, mirror, [self.BRANCH], "current", True)
            self.assertEqual(calls, 2)
            self.assertFalse(mirror.exists())
            self.assertEqual(source.read_bytes(), original)

    def test_path_traversal_and_duplicate_sources_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix="sens-two-test-") as td:
            mirror = Path(td) / "mirror"
            with self.assertRaises(pair.ProjectionBlocked):
                pair.stage(ROOT, mirror, ["../outside.lisp"], "auto", True)
            with self.assertRaises(pair.ProjectionBlocked):
                pair.stage(ROOT, mirror, [self.BRANCH, self.BRANCH], "auto", True)
            self.assertFalse(list(mirror.rglob("*"))) if mirror.exists() else None

    def test_invalid_program_does_not_claim_migration(self):
        # The bounded Ukrainian renderer must not make up a source-level
        # mapping for arbitrary arithmetic, a binder or unresolved call.
        with tempfile.TemporaryDirectory(prefix="sens-two-test-") as td:
            root = Path(td) / "input"
            root.mkdir()
            (root / "invalid.lisp").write_text("(unknown-fn 17)\n", encoding="utf-8")
            mirror = Path(td) / "mirror"
            with self.assertRaises(pair.ProjectionBlocked):
                pair.stage(root, mirror, ["invalid.lisp"], "auto", True)
            self.assertFalse(list(mirror.rglob("*"))) if mirror.exists() else None


if __name__ == "__main__":
    unittest.main()
