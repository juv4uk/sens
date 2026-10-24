#!/usr/bin/env python3
"""Механічна перевірка F4 provenance: скрипт має збігатися з cited Git SHA.

Це НЕ тест семантики SENS: mock замінює лише зовнішнє читання Git-об'єкта.
"""
from pathlib import Path
import runpy
import subprocess
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
CONNECTOR = runpy.run_path(str(ROOT / "scripts" / "connect-release-admission-native.py"))
REF_SHA = "20543d438e81c6937c35c8d5e1950d72bac42a33"
REL = "scripts/prove-d4-selector-width.sh"
SCRIPT = Path("/repo") / REL


class F4ScriptProvenanceTests(unittest.TestCase):
    def verify(self, pinned: bytes, current: bytes, *, status: int = 0) -> tuple[bool, str]:
        reply = subprocess.CompletedProcess(
            args=["git"], returncode=status, stdout=pinned, stderr=b"object absent"
        )
        with (
            mock.patch.object(CONNECTOR["subprocess"], "run", return_value=reply) as git,
            mock.patch.object(Path, "read_bytes", return_value=current),
        ):
            result = CONNECTOR["check_proof_ref"](Path("/repo"), REF_SHA, REL, SCRIPT)
        self.assertEqual(
            git.call_args.args[0], ["git", "-C", "/repo", "show", f"{REF_SHA}:{REL}"]
        )
        return result

    def test_stale_t5_citation_cannot_verify_new_t5m_script(self):
        ok, reason = self.verify(b"historic T5 proof", b"current T5M proof")
        self.assertFalse(ok)
        self.assertIn("F4_PROVENANCE_MISMATCH", reason)

    def test_exact_cited_proof_bytes_are_accepted(self):
        ok, reason = self.verify(b"exact physical proof", b"exact physical proof")
        self.assertTrue(ok)
        self.assertIn("F4_PROVENANCE_OK", reason)

    def test_unavailable_git_citation_fails_closed(self):
        ok, reason = self.verify(b"", b"current T5M proof", status=128)
        self.assertFalse(ok)
        self.assertIn("F4_REF_UNAVAILABLE", reason)



class NativeProofVerdictMarkerTests(unittest.TestCase):
    """Only a terminal native verdict for this exact proof may count as success."""

    def check(self, output: str, status: int = 0) -> tuple[bool, str]:
        reply = subprocess.CompletedProcess(
            args=["bash"], returncode=status, stdout=output, stderr=""
        )
        with mock.patch.object(CONNECTOR["subprocess"], "run", return_value=reply):
            return CONNECTOR["run_proof"](SCRIPT, Path("/repo/sens"), Path("/repo"), 5)

    def test_warning_that_mentions_pass_marker_is_not_a_proof(self):
        ok, _ = self.check("WARNING: NATIVE_SENS_PASS not emitted by this proof\n")
        self.assertFalse(ok)

    def test_correct_positive_and_mutant_terminal_markers_verify(self):
        output = (
            "NATIVE_SENS_NEGATIVE test_id=d4-selector-width-mutant "
            "stderr_sha256=abcdef\n"
            "NATIVE_SENS_PASS test_id=d4-selector-width physical_positive=D1:1 "
            "mutant=D1-noncallable semantic_authority=binary-SENS\n"
        )
        ok, detail = self.check(output)
        self.assertTrue(ok)
        self.assertEqual(detail, "NATIVE_SENS_PASS")

    def test_marker_for_another_proof_does_not_verify_this_script(self):
        output = (
            "NATIVE_SENS_NEGATIVE test_id=other-mutant outcome=D1:0\n"
            "NATIVE_SENS_PASS test_id=other mutant=D1:0 semantic_authority=SENS\n"
        )
        ok, _ = self.check(output)
        self.assertFalse(ok)

    def test_pass_without_negative_witness_is_not_verified(self):
        output = (
            "NATIVE_SENS_PASS test_id=d4-selector-width physical_positive=D1:1 "
            "mutant=D1-noncallable semantic_authority=binary-SENS\n"
        )
        ok, _ = self.check(output)
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
