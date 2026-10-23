#!/usr/bin/env python3
"""Перевірка атомарного експорту української програми у фізичний T5M."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from publish_verified_uk_triplets import (
    ProjectionBlocked, attest_source, export, no_symlink_destination,
)
from sens_t5_t5m_codec import decode_t5m_bytes, encode_t5m_projection


class SafeTripletPublisher(unittest.TestCase):
    REL1 = "tests/fixtures/migration-d1-cond-cohort/branch.lisp"
    REL2 = "tests/fixtures/migration-d4-selector-cohort/caar.lisp"

    def test_existing_canonical_uk_source_is_admissible_as_three_views(self):
        for rel in (self.REL1, self.REL2):
            with self.subTest(rel=rel):
                src = (ROOT / rel).read_bytes()
                words, packed, view = attest_source(src)
                self.assertEqual(decode_t5m_bytes(packed), words)
                self.assertEqual(packed, encode_t5m_projection(" ".join(words)))
                self.assertEqual(view, (" ".join(words) + "\n").encode("ascii"))
                self.assertNotIn(b"2", view)
                self.assertGreater(len(packed), 0)

    def test_two_real_fixture_sources_batch_is_atomic_and_verified(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "mirror"
            report = Path(td) / "admit.json"
            original1 = (ROOT / self.REL1).read_bytes()
            original2 = (ROOT / self.REL2).read_bytes()
            res = export(ROOT, target, report, [self.REL1, self.REL2], write=True)
            self.assertEqual(res["summary"]["triplets_written"], 2)
            self.assertTrue(all(row["physical_codec"] == "t5m" for row in res["files"]))
            self.assertTrue(all(row["physical_authority"] == "zig-attested-t5m"
                                for row in res["files"]))
            self.assertTrue(all(len(row["zig_binary_sha256"]) == 64
                                for row in res["files"]))
            self.assertEqual(res["summary"]["original_executables_oracle_certified"], 0)
            self.assertEqual((target / self.REL1).read_bytes(), original1)
            self.assertEqual((target / self.REL2).read_bytes(), original2)
            for rel in (self.REL1, self.REL2):
                out = target / Path(rel)
                packed = out.with_suffix(".sens").read_bytes()
                words = decode_t5m_bytes(packed)
                self.assertEqual(out.with_suffix("").read_bytes(),
                                 (" ".join(words) + "\n").encode("ascii"))
            self.assertEqual(json.loads(report.read_text())["summary"]["triplets_written"], 2)
            # All generated files must be in the EXTERNAL mirror, not the source.
            self.assertEqual((ROOT / self.REL1).read_bytes(), original1)
            self.assertEqual((ROOT / self.REL2).read_bytes(), original2)

    def test_comments_and_layout_do_not_change_exported_program(self):
        # Порівнюємо доменні слова та програму, не відтворення коментарів.
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "source"
            root.mkdir()
            original = (ROOT / self.REL1).read_text(encoding="utf-8")
            decorated = "; Інформаційний коментар — не частина програми\n" + original.replace(" ", "  ", 1)
            (root / "program.lisp").write_text(decorated, encoding="utf-8")
            mirror = base / "mirror"
            report = base / "report.json"
            result = export(root, mirror, report, ["program.lisp"], write=True)
            self.assertEqual(result["summary"]["triplets_written"], 1)
            lisp = mirror / "program.lisp"
            sens = mirror / "program.sens"
            view = mirror / "program"
            self.assertEqual(lisp.read_text(encoding="utf-8"), decorated)
            words = decode_t5m_bytes(sens.read_bytes())
            self.assertEqual(view.read_text(encoding="ascii"), " ".join(words) + "\n")
            self.assertEqual(result["files"][0]["physical_codec"], "t5m")
            self.assertEqual(result["summary"]["original_executables_oracle_certified"], 0)

    def test_zig_unavailable_never_mints_python_reference_as_sens(self):
        # Навіть якщо незалежний Python-еталон успішно закодував програму,
        # фізичне видання через інший ніж Zig шлях заборонене.
        with tempfile.TemporaryDirectory() as td:
            mirror = Path(td) / "mirror"
            report = Path(td) / "report.json"
            source = (ROOT / self.REL1).read_bytes()
            with mock.patch(
                "publish_verified_uk_triplets.zig_codec_bridge.build_transport",
                side_effect=ValueError("ZIG_CODEC_UNAVAILABLE"),
            ) as build:
                with self.assertRaisesRegex(ValueError, "ZIG_CODEC_UNAVAILABLE"):
                    export(ROOT, mirror, report, [self.REL1], write=True)
            self.assertEqual(build.call_count, 1)
            self.assertFalse(mirror.exists())
            self.assertFalse(report.exists())
            self.assertEqual((ROOT / self.REL1).read_bytes(), source)

    def test_zig_reference_divergence_cannot_publish(self):
        # Незалежний еталон не дає Zig повернути іншу програму під тим же ім'ям.
        # Фізичні файли, включно з першим .sens, ще не створені.
        with tempfile.TemporaryDirectory() as td:
            mirror = Path(td) / "mirror"
            report = Path(td) / "report.json"
            with mock.patch(
                "publish_verified_uk_triplets.zig_codec_bridge.build_transport",
                return_value=Path(td) / "verified-transport",
            ), mock.patch(
                "publish_verified_uk_triplets.zig_codec_bridge.carry_t5",
                return_value=b"\\xff",
            ), mock.patch(
                "publish_verified_uk_triplets.zig_codec_bridge.verify_t5",
                return_value={"zig_binary_sha256": "a" * 64},
            ):
                with self.assertRaisesRegex(
                    ProjectionBlocked, "ZIG_T5M_REFERENCE_PARITY_MISMATCH"
                ):
                    export(ROOT, mirror, report, [self.REL1], write=True)
            self.assertFalse(mirror.exists())
            self.assertFalse(report.exists())

    def test_preview_is_reference_only_without_zig_mint(self):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch(
                "publish_verified_uk_triplets.zig_codec_bridge.build_transport",
                side_effect=AssertionError("preview must not build Zig"),
            ):
                preview = export(
                    ROOT, Path(td) / "mirror", Path(td) / "report.json",
                    [self.REL1], write=False,
                )
            self.assertEqual(preview["summary"]["triplets_written"], 0)
            self.assertEqual(preview["files"][0]["physical_authority"],
                             "reference-only-nonpublic")

    def test_preview_only_does_not_write_or_fake_semantics(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "mirror"
            report = Path(td) / "preview.json"
            out = export(ROOT, target, report, [self.REL1], write=False)
            self.assertEqual(out["summary"]["candidates"], 1)
            self.assertEqual(out["summary"]["triplets_written"], 0)
            self.assertEqual(out["summary"]["original_executables_oracle_certified"], 0)
            self.assertFalse(target.exists())

    def test_noncanonical_and_unknown_uk_does_not_create_any_triplet(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "repo"
            src.mkdir()
            (src / "unknown.lisp").write_text("(невідома-функція ())\n", encoding="utf-8")
            target = Path(td) / "mirror"
            res = export(src, target, Path(td) / "blocked.json",
                         ["unknown.lisp"], write=True)
            self.assertEqual(res["summary"]["blocked"], 1)
            self.assertEqual(res["summary"]["triplets_written"], 0)
            self.assertFalse(target.exists())

    def test_bad_member_blocks_entire_cohort_even_with_good_source(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "mirror"
            res = export(ROOT, target, Path(td) / "blocked.json",
                         [self.REL1, "does-not-exist.lisp"], write=True)
            self.assertEqual(res["summary"]["blocked"], 1)
            self.assertEqual(res["summary"]["triplets_written"], 0)
            self.assertFalse(target.exists())

    def test_existing_view_or_sens_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "mirror"
            view = target / Path(self.REL1).with_suffix("")
            view.parent.mkdir(parents=True)
            view.write_text("tampered \u2603\n", encoding="utf-8")
            res = export(ROOT, target, Path(td) / "blocked.json", [self.REL1], write=True)
            self.assertEqual(res["summary"]["blocked"], 1)
            self.assertEqual(view.read_text(encoding="utf-8"), "tampered \u2603\n")
            self.assertFalse(view.with_suffix(".sens").exists())

    def test_link_failure_mid_second_triplet_rolls_back_every_file(self):
        # Негативний свідок: фізичний T5 не повинен залишитися сиротою
        # після відмови четвертого hard-link (три файли першої трійки вже є).
        with tempfile.TemporaryDirectory() as td:
            mirror = Path(td) / "mirror"
            report = Path(td) / "blocked.json"
            original = {rel: (ROOT / rel).read_bytes()
                        for rel in (self.REL1, self.REL2)}
            real_link = os.link
            observed = []

            def interrupt_link(source, destination):
                observed.append(Path(destination))
                if len(observed) == 4:
                    raise OSError("injected fourth-link failure")
                return real_link(source, destination)

            with mock.patch("publish_verified_uk_triplets.os.link",
                            side_effect=interrupt_link):
                with self.assertRaisesRegex(OSError, "fourth-link failure"):
                    export(ROOT, mirror, report, [self.REL1, self.REL2],
                           write=True)
            self.assertEqual(len(observed), 4)
            for rel in (self.REL1, self.REL2):
                stem = mirror / rel
                for path in (stem, stem.with_suffix(".sens"),
                             stem.with_suffix("")):
                    self.assertFalse(path.exists(), str(path))
                    self.assertFalse(path.is_symlink(), str(path))
                self.assertEqual((ROOT / rel).read_bytes(), original[rel])
            self.assertFalse(report.exists())
            self.assertEqual(list(mirror.rglob(".t5m-stage-*")), [])
            # Тільки новостворені посилання видаляються, не оригінали.
            self.assertEqual({rel: (ROOT / rel).read_bytes()
                              for rel in (self.REL1, self.REL2)}, original)

    def test_second_verifier_failure_rolls_back_all_six_published_files(self):
        # Негативний свідок після завершення фізичного запису:
        # перевірка другої трійки відмовила — усі шість файлів відкотити.
        with tempfile.TemporaryDirectory() as td:
            mirror = Path(td) / "mirror"
            report = Path(td) / "blocked.json"
            original = {rel: (ROOT / rel).read_bytes()
                        for rel in (self.REL1, self.REL2)}
            good_verdict = {"runtime_oracle_admitted_by_this_audit": False}
            with mock.patch(
                "publish_verified_uk_triplets.verify",
                side_effect=[good_verdict,
                             ProjectionBlocked("injected second-verifier failure")],
            ) as verifier:
                with self.assertRaisesRegex(ProjectionBlocked,
                                            "second-verifier failure"):
                    export(ROOT, mirror, report, [self.REL1, self.REL2],
                           write=True)
            self.assertEqual(verifier.call_count, 2)
            for rel in (self.REL1, self.REL2):
                stem = mirror / rel
                self.assertFalse(stem.exists())
                self.assertFalse(stem.with_suffix(".sens").exists())
                self.assertFalse(stem.with_suffix("").exists())
                self.assertEqual((ROOT / rel).read_bytes(), original[rel])
            self.assertFalse(report.exists())
            self.assertEqual(list(mirror.rglob(".t5m-stage-*")), [])

    def test_report_write_failure_rolls_back_all_new_triplets(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "mirror"
            report = Path(td) / "report.json"
            with mock.patch("publish_verified_uk_triplets.json.dump",
                            side_effect=OSError("simulated report write failure")):
                with self.assertRaisesRegex(OSError, "report write failure"):
                    export(ROOT, target, report, [self.REL1], write=True)
            lisp = target / self.REL1
            self.assertFalse(lisp.exists())
            self.assertFalse(lisp.with_suffix(".sens").exists())
            self.assertFalse(lisp.with_suffix("").exists())
            self.assertFalse(report.exists())

    def test_reject_symlink_source_and_output_parent(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "src"
            src.mkdir()
            (src / "original.lisp").write_text("(як-є ())\n")
            (src / "link.lisp").symlink_to(src / "original.lisp")
            out = export(src, Path(td) / "mirror", Path(td) / "blocked.json",
                         ["link.lisp"], write=True)
            self.assertEqual(out["summary"]["blocked"], 1)
            self.assertEqual(out["summary"]["triplets_written"], 0)

    def test_symlinked_mirror_parent_cannot_write_into_source_tree(self):
        # The lexical target is outside ROOT, but its real path points inside
        # source. No staged .sens/view may be materialized via this alias.
        with tempfile.TemporaryDirectory() as td:
            alias = Path(td) / "linked-checkout"
            alias.symlink_to(ROOT, target_is_directory=True)
            destination = alias / "blocked-mirror-4756"
            with self.assertRaisesRegex(ProjectionBlocked, "outside source repository"):
                export(ROOT, destination, Path(td) / "blocked.json",
                       [self.REL1], write=True)
            self.assertFalse((ROOT / "blocked-mirror-4756").exists())
            self.assertFalse(destination.exists())

    def test_no_filename_confusion_or_source_mirror_escape(self):
        with tempfile.TemporaryDirectory() as td:
            for bad in ("/etc/passwd.lisp", "../escape.lisp", "./file.lisp",
                        "tests/foo.sens", "tests\\backslash.lisp"):
                res = export(ROOT, Path(td) / "out",
                             Path(td) / ("report-" + str(len(bad)) + "-" +
                             str(abs(hash(bad))) + ".json"),
                             [bad], write=False)
                self.assertEqual(res["summary"]["blocked"], 1, bad)
            with self.assertRaises(ProjectionBlocked):
                export(ROOT, ROOT / "mirror", Path(td) / "x.json",
                       [self.REL1], write=True)


if __name__ == "__main__":
    unittest.main()
