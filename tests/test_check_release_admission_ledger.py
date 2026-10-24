#!/usr/bin/env python3
"""Negative witnesses for the fail-closed release admission-ledger mechanism.

Proves the checker can never admit without every one of F1–F4 well-formed AND an
explicit owner ``ratified=1``, and that the claimed ``typed_word_sha256`` is
verified against the real ``.sens`` bytes.
"""

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "check-release-admission-ledger.py"
SPEC = importlib.util.spec_from_file_location("sens_check_release_admission_ledger", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

REF = "juv4uk/sens@f63b46c4eab71c6fd6f3ceea45589b4ef92d2718:tests/donor-evidence.lisp:1"
POSITIVE_REF = "juv4uk/sens@f63b46c4eab71c6fd6f3ceea45589b4ef92d2718:tests/positive-evidence.lisp:2"
NEGATIVE_REF = "juv4uk/sens@f63b46c4eab71c6fd6f3ceea45589b4ef92d2718:tests/negative-evidence.lisp:3"
F4_REF = "juv4uk/sens@f63b46c4eab71c6fd6f3ceea45589b4ef92d2718:tests/physical-t5-evidence.lisp:4"
DEDUP = "D1-D9@f63b46c4eab71c6fd6f3ceea45589b4ef92d2718=NO-MATCH;D10@f63b46c4eab71c6fd6f3ceea45589b4ef92d2718=NO-MATCH"
REAL_SENS = "tests/fixtures/migration-d1-cond-cohort/branch.sens"


def entry(**over):
    base = {
        "sens": "tests/fixtures/x.sens",
        "typed_word_sha256": "a" * 64,
        "f1_donor_provenance": REF,
        "f2_positive_witness": POSITIVE_REF,
        "f2_negative_witness": NEGATIVE_REF,
        "f3_dedup": DEDUP,
        "f4_t5_execution": F4_REF,
        "ratified": 0,
    }
    base.update(over)
    return base


def ledger(entries):
    return {"schema": MODULE.SCHEMA, "entries": entries}


class FormatTests(unittest.TestCase):
    def check(self, entries):
        return MODULE.validate_ledger(ledger(entries), verify_content=False)

    def test_empty_ledger_admits_nothing(self):
        receipt = self.check([])
        self.assertEqual(receipt["release_admitted"], 0)

    def test_pending_entry_not_admitted(self):
        self.assertEqual(self.check([entry(ratified=0)])["release_admitted"], 0)

    def test_ratified_full_entry_is_not_admitted_without_content(self):
        receipt = self.check([entry(ratified=1)])
        self.assertEqual(receipt["validation_mode"], "form_only")
        self.assertEqual(receipt["form_candidates"], 1)
        self.assertEqual(receipt["release_admitted"], 0)
        self.assertEqual(receipt["uk_oracle_verified"], 0)
        self.assertEqual(receipt["admitted_sens"], [])

    def test_unknown_schema_blocks(self):
        with self.assertRaises(MODULE.LedgerBlocked):
            MODULE.validate_ledger({"schema": "other/v9", "entries": []}, verify_content=False)

    def test_bad_provenance_ref_blocks(self):
        with self.assertRaises(MODULE.LedgerBlocked):
            self.check([entry(f1_donor_provenance="not-a-ref")])

    def test_bad_typed_sha_blocks(self):
        with self.assertRaises(MODULE.LedgerBlocked):
            self.check([entry(typed_word_sha256="xyz")])

    def test_bad_dedup_blocks(self):
        with self.assertRaises(MODULE.LedgerBlocked):
            self.check([entry(f3_dedup="D1-D9@abc=NO-MATCH")])

    def test_duplicate_sens_blocks(self):
        with self.assertRaises(MODULE.LedgerBlocked):
            self.check([entry(), entry()])
    def test_same_f2_positive_and_negative_reference_blocks(self):
        with self.assertRaises(MODULE.LedgerBlocked):
            self.check([entry(f2_negative_witness=POSITIVE_REF, ratified=1)])

    def test_extra_or_missing_field_blocks(self):
        with self.assertRaises(MODULE.LedgerBlocked):
            self.check([entry(extra="x")])
        with self.assertRaises(MODULE.LedgerBlocked):
            bad = entry()
            del bad["f4_t5_execution"]
            self.check([bad])

    def test_bool_ratified_blocks(self):
        with self.assertRaises(MODULE.LedgerBlocked):
            self.check([entry(ratified=True)])


class ContentTests(unittest.TestCase):
    def test_real_fixture_hash_verifies_content_not_semantics(self):
        good = MODULE.content_sha256(ROOT, REAL_SENS)
        receipt = MODULE.validate_ledger(
            ledger([entry(sens=REAL_SENS, typed_word_sha256=good, ratified=1)])
        )
        self.assertEqual(receipt["content_verified"], 1)
        self.assertEqual(receipt["uk_oracle_verified"], 0)
        self.assertEqual(receipt["release_admitted"], 0)
        self.assertEqual(receipt["admitted_sens"], [])

    def test_fake_f2_f4_receipts_never_release_admit_real_t5(self):
        good = MODULE.content_sha256(ROOT, REAL_SENS)
        fake_ref = "juv4uk/sens@" + "f" * 40 + ":missing-native-witness.lisp:1"
        candidate = entry(
            sens=REAL_SENS,
            typed_word_sha256=good,
            f2_positive_witness=fake_ref,
            f4_t5_execution=fake_ref,
            ratified=1,
        )
        receipt = MODULE.validate_ledger(ledger([candidate]))
        self.assertEqual(receipt["content_verified"], 1)
        self.assertEqual(receipt["uk_oracle_verified"], 0)
        self.assertEqual(receipt["release_admitted"], 0)
        with tempfile.TemporaryDirectory() as tmp:
            from contextlib import redirect_stderr, redirect_stdout
            import io

            path = Path(tmp) / "ledger.json"
            path.write_text(json.dumps(ledger([candidate])), encoding="utf-8")
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = MODULE.main(["--ledger", str(path)])
            self.assertEqual(exit_code, 2)
            self.assertNotIn("RELEASE_ADMISSION_PASS", stdout.getvalue())
            self.assertIn("RELEASE_ADMISSION_BLOCKED", stderr.getvalue())

    def test_current_t5m_d24_word_verifies_bytes_without_granting_release_admission(self):
        # Physical T5M carries D24-width words; legacy T5 stops at W11.
        # This proves transport integrity only, not a semantic D24 law.
        wide = "1" + "0" * 23
        physical = MODULE.CODEC.encode_t5m_projection(wide)
        expected_hash = MODULE.CODEC.typed_sha256([wide])
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "operand.sens").write_bytes(physical)
            self.assertEqual(MODULE.content_sha256(repo, "operand.sens"), expected_hash)
            receipt = MODULE.validate_ledger(
                ledger([entry(sens="operand.sens", typed_word_sha256=expected_hash,
                              ratified=1)]),
                root=repo,
            )
            self.assertEqual(receipt["content_verified"], 1)
            self.assertEqual(receipt["uk_oracle_verified"], 0)
            self.assertEqual(receipt["release_admitted"], 0)

    def test_wrong_content_hash_blocks(self):
        with self.assertRaises(MODULE.LedgerBlocked):
            MODULE.validate_ledger(ledger([entry(sens=REAL_SENS, typed_word_sha256="b" * 64)]))
    def test_same_f2_reference_blocks_even_with_matching_t5_hash_and_ratification(self):
        good = MODULE.content_sha256(ROOT, REAL_SENS)
        candidate = entry(
            sens=REAL_SENS,
            typed_word_sha256=good,
            f2_negative_witness=POSITIVE_REF,
            ratified=1,
        )
        with self.assertRaises(MODULE.LedgerBlocked):
            MODULE.validate_ledger(ledger([candidate]))

    def test_root_regular_file_is_accepted_but_symlink_evidence_is_rejected(self):
        data = (ROOT / REAL_SENS).read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = base / "repo"
            repo.mkdir()
            regular = repo / "valid.sens"
            regular.write_bytes(data)
            outside = base / "external.sens"
            outside.write_bytes(data)
            digest = MODULE.content_sha256(repo, "valid.sens")
            admitted = MODULE.validate_ledger(
                ledger([entry(sens="valid.sens", typed_word_sha256=digest, ratified=1)]),
                root=repo,
            )
            self.assertEqual(admitted["content_verified"], 1)
            self.assertEqual(admitted["release_admitted"], 0)
            for target in (regular, outside):
                link = repo / "linked.sens"
                link.symlink_to(target)
                try:
                    with self.subTest(target=target), self.assertRaises(MODULE.LedgerBlocked):
                        MODULE.validate_ledger(
                            ledger([entry(sens="linked.sens", typed_word_sha256=digest,
                                          ratified=1)]), root=repo,
                        )
                finally:
                    link.unlink()

            external_dir = base / "linked-directory"
            external_dir.mkdir()
            (external_dir / "nested.sens").write_bytes(data)
            (repo / "linkdir").symlink_to(external_dir, target_is_directory=True)
            with self.assertRaises(MODULE.LedgerBlocked):
                MODULE.validate_ledger(
                    ledger([entry(sens="linkdir/nested.sens",
                                  typed_word_sha256=digest, ratified=1)]), root=repo,
                )

    def test_hardlink_alias_with_identical_t5_bytes_cannot_prove_release_content(self):
        if not hasattr(os, "link"):
            self.skipTest("hardlink primitive unavailable on this host")
        payload = (ROOT / REAL_SENS).read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = base / "repo"
            repo.mkdir()
            # Byte-identical independent copy is legitimate physical evidence.
            independent = repo / "independent.sens"
            independent.write_bytes(payload)
            claimed = MODULE.content_sha256(repo, "independent.sens")
            clean = MODULE.validate_ledger(
                ledger([entry(sens="independent.sens",
                              typed_word_sha256=claimed, ratified=1)]),
                root=repo,
            )
            self.assertEqual(clean["content_verified"], 1)
            self.assertEqual(clean["release_admitted"], 0)

            # The same inode reachable outside the checkout must never pass.
            outside = base / "outside.sens"
            outside.write_bytes(payload)
            linked = repo / "linked.sens"
            os.link(outside, linked)
            with self.assertRaisesRegex(MODULE.LedgerBlocked, "hardlink"):
                MODULE.validate_ledger(
                    ledger([entry(sens="linked.sens",
                                  typed_word_sha256=claimed, ratified=1)]),
                    root=repo,
                )

            # Internal same-inode aliases must fail, even with correct SHA.
            internal = repo / "also-linked.sens"
            os.link(linked, internal)
            with self.assertRaisesRegex(MODULE.LedgerBlocked, "hardlink"):
                MODULE.content_sha256(repo, "also-linked.sens")

    def test_noncanonical_alias_paths_cannot_duplicate_admission(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "one.sens").write_bytes((ROOT / REAL_SENS).read_bytes())
            for alias in ("./one.sens", "a/../one.sens", "a//one.sens"):
                with self.subTest(alias=alias), self.assertRaises(MODULE.LedgerBlocked):
                    MODULE.content_sha256(root, alias)

    def test_missing_sens_file_blocks(self):
        with self.assertRaises(MODULE.LedgerBlocked):
            MODULE.validate_ledger(ledger([entry(sens="tests/fixtures/does-not-exist.sens")]))


class CliTests(unittest.TestCase):
    def test_absent_ledger_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(MODULE.main(["--ledger", str(Path(tmp) / "nope.json")]), 2)

    def test_format_only_roundtrip(self):
        import io
        from contextlib import redirect_stdout

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.json"
            path.write_text(json.dumps(ledger([entry(ratified=1)])), encoding="utf-8")
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(MODULE.main(["--ledger", str(path), "--no-verify-content"]), 0)
            self.assertIn("RELEASE_ADMISSION_FORM_ONLY", output.getvalue())
            self.assertNotIn("RELEASE_ADMISSION_PASS", output.getvalue())
            self.assertIn('"release_admitted": 0', output.getvalue())
            self.assertIn('"form_candidates": 1', output.getvalue())


class HostedCiAdmissionWiringTests(unittest.TestCase):
    def test_actual_hosted_ci_replays_ledger_negative_controls(self):
        workflow = (ROOT / ".github" / "workflows" / "ci-hosted.yml").read_text(
            encoding="utf-8"
        )
        label = "      - name: Physical T5 admission-ledger positive and negative witnesses (no tag)"
        self.assertEqual(workflow.count(label), 1)
        block = workflow.split(label, 1)[1].split("\n      - name:", 1)[0]
        self.assertIn("if: always()", block)
        self.assertIn(
            "python3 -m unittest discover -s tests -p 'test_check_release_admission_ledger.py' -v",
            block,
        )


if __name__ == "__main__":
    unittest.main()
