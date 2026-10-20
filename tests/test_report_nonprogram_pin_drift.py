"""Негативні перевірки дрейфу SHA: жодного автоматичного допуску Lisp/SENS."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from report_nonprogram_pin_drift import scan


def blob_sha(contents: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(contents)).encode("ascii") + b"\x00" + contents
    ).hexdigest()


class PinDriftTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "lib/профіль.lisp"
        self.source.parent.mkdir()
        self.source.write_text("; Тільки дані профілю\n", encoding="utf-8")
        self.manifest = "knowledge/profile.json"
        self.manifest_path = self.root / self.manifest
        self.manifest_path.parent.mkdir()
        self.write_manifest(blob_sha(self.source.read_bytes()))

    def write_manifest(self, sha):
        self.manifest_path.write_text(json.dumps({
            "schema": "sens-migration-nonprogram-manifest/1",
            "issue": 4460,
            "automatic_sens_companion": False,
            "entries": [{"path": "lib/профіль.lisp", "git_blob_sha1": sha}],
        }, ensure_ascii=False), encoding="utf-8")

    def report(self):
        return scan(self.root, manifests=(("comment-only-loader", self.manifest, 1),))

    def test_identical_pinned_nonprogram_is_not_executable_credit(self):
        state = self.report()
        self.assertEqual(state["discrepancies"], 0)
        self.assertEqual(state["status"], "PINNED_SOURCE_BLOBS_MATCH")
        self.assertTrue(state["unreviewed_drift_cannot_authorize_release"])
        self.assertFalse(state["automatic_repin"])

    def test_changed_comment_blob_remains_transitional_not_silently_repinned(self):
        self.source.write_text("; Оновлений профіль\n", encoding="utf-8")
        state = self.report()
        self.assertEqual(state["discrepancies"], 1)
        self.assertEqual(state["sample"][0]["reason"], "SOURCE_BLOB_DRIFT")
        self.assertIn("TRANSITIONAL", state["status"])
        self.assertEqual(state["sample"][0]["pinned_blob_sha"],
                         json.loads(self.manifest_path.read_text())["entries"][0]["git_blob_sha1"])

    def test_nested_block_comments_are_valid_nonprogram_lisp(self):
        self.source.write_text(
            "#| зовнішній (define pretend 1)\n"
            "   #| внутрішній (псевдовиклик) |#\n"
            "   завершення |#\n; пояснення\n",
            encoding="utf-8",
        )
        self.write_manifest(blob_sha(self.source.read_bytes()))
        state = self.report()
        self.assertEqual(state["discrepancies"], 0)
        self.assertEqual(state["status"], "PINNED_SOURCE_BLOBS_MATCH")
        self.assertFalse(state["automatic_repin"])

    def test_executable_after_nested_comment_is_not_nonprogram(self):
        self.source.write_text(
            "#| коментар #| вкладений |# |#\n(визначити проба так)\n",
            encoding="utf-8",
        )
        self.write_manifest(blob_sha(self.source.read_bytes()))
        self.assertEqual(self.report()["sample"][0]["reason"],
                         "NO_LONGER_COMMENT_ONLY")

    def test_unterminated_block_comment_is_invalid_not_nonprogram(self):
        self.source.write_text("#| незавершений #| вкладений |#\n",
                               encoding="utf-8")
        self.write_manifest(blob_sha(self.source.read_bytes()))
        self.assertEqual(self.report()["sample"][0]["reason"],
                         "INVALID_LISP_COMMENT_SYNTAX")

    def test_form_pretending_to_be_profile_is_rejected_even_if_repinning(self):
        self.source.write_text("(визначити нова-функція так)\n", encoding="utf-8")
        self.write_manifest(blob_sha(self.source.read_bytes()))
        state = self.report()
        self.assertEqual(state["sample"][0]["reason"], "NO_LONGER_COMMENT_ONLY")

    def test_new_physical_companion_is_not_admitted(self):
        self.source.with_suffix(".sens").write_bytes(b"fake")
        self.assertEqual(self.report()["sample"][0]["reason"], "UNAPPROVED_PHYSICAL_PAIR")

    def test_missing_or_symlink_source_cannot_pass(self):
        self.source.unlink()
        state = self.report()
        self.assertEqual(state["sample"][0]["reason"], "MISSING_OR_SYMLINK_SOURCE")

    def test_bad_manifest_count_and_sha_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "cardinality"):
            scan(self.root, manifests=(("comment-only-loader", self.manifest, 2),))
        self.write_manifest("a" * 39)
        with self.assertRaisesRegex(ValueError, "invalid pinned SHA"):
            self.report()


if __name__ == "__main__":
    unittest.main()
