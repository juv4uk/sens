#!/usr/bin/env python3
"""REAL old executable -> staged candidate T5 -> REAL current Rust D2 reader.

Only tests unratified #3910 draft. Never publishes or admits a .sens in main.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/machine/block.lisp"
EXPECTED_BLOB = "200201b741787c4e144ad4194848acf51d7b439e"
sys.path.insert(0, str(ROOT / "scripts"))
from sens_t5_codec import decode_bytes, encode_words, typed_sha256

def process(*cmd, timeout=100):
    return subprocess.run(
        [str(x) for x in cmd], cwd=ROOT, capture_output=True,
        text=True, encoding="utf-8", timeout=timeout,
    )


class OriginalPhysicalCandidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="sens-real-block-t5-candidate-")
        cls.folder = Path(cls.temp.name)
        cls.payload = cls.folder / "block.sens"
        cls.receipt = cls.folder / "receipt.json"
        cls.original = SOURCE.read_bytes()
        cls.old_git_sha = process("git", "hash-object", SOURCE).stdout.strip()
        if cls.old_git_sha != EXPECTED_BLOB:
            raise AssertionError("original historical Git blob changed")
        if (ROOT / "lib/machine/block.sens").exists():
            raise AssertionError("unratified candidate leaked into canonical main source")
        cls.execution = process(
            sys.executable, ROOT / "scripts/migrate-three-pass.py",
            SOURCE, "--out", cls.folder, "--report", cls.receipt,
            "--source-era", "legacy",
        )
        if not cls.receipt.exists():
            raise AssertionError(
                "canonical three-pass did not report candidate:\n"
                + cls.execution.stderr[-1800:]
            )
        cls.audit = json.loads(cls.receipt.read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_canonical_historical_source_physically_generated_without_source_rewrite(self):
        self.assertEqual(
            self.execution.returncode, 0,
            "FIRST ACTUAL ORIGINAL CANONICAL EMISSION BLOCKED: "
            + json.dumps(self.audit["files"], ensure_ascii=False)[-2000:]
            + self.execution.stderr[-700:],
        )
        self.assertEqual(len(self.audit["files"]), 1)
        entry = self.audit["files"][0]
        self.assertEqual(entry["status"], "written")
        self.assertEqual(entry["passes"]["pass1-sens8"], 17)
        self.assertEqual(entry["passes"]["passthrough-head"], 0)
        self.assertTrue(self.payload.is_file())
        self.assertTrue(self.payload.read_bytes())
        self.assertEqual(SOURCE.read_bytes(), self.original)

    def test_physical_t5_exact_bit_word_and_byte_roundtrip(self):
        self.test_canonical_historical_source_physically_generated_without_source_rewrite()
        binary = self.payload.read_bytes()
        words = decode_bytes(binary)
        self.assertEqual(encode_words(words), binary)
        self.assertTrue(all(word and set(word) <= {"0", "1"} for word in words))
        self.assertEqual(typed_sha256(words), self.audit["files"][0]["typed_word_sha256"])
        self.assertEqual(hashlib.sha256(binary).hexdigest(),
                         self.audit["files"][0]["physical_sha256"])
        bits_view = (" ".join(words) + "\n").encode("ascii")
        self.assertEqual(bits_view.count(b"\n"), 1)
        self.assertNotIn(b"2", bits_view)
        self.assertEqual(encode_words(bits_view[:-1].decode("ascii").split(" ")),
                         binary)

    def test_real_current_rust_D2_reader_accepts_emitted_candidate(self):
        self.test_physical_t5_exact_bit_word_and_byte_roundtrip()
        reader = Path(os.environ.get(
            "SENS_TRIT_BIN", ROOT / "target/debug/sens-trit"
        ))
        self.assertTrue(reader.is_file(),
                        "must build actual sens-trit Rust binary before candidate probe")
        outcome = process(reader, "open", self.payload)
        self.assertEqual(
            outcome.returncode, 0,
            "REAL Rust D2 READER BLOCKS candidate produced by canonical migrator; "
            "do not publish bytes: " + outcome.stderr[-1400:],
        )

    def test_real_current_rust_evaluator_accepts_emitted_six_definitions(self):
        self.test_real_current_rust_D2_reader_accepts_emitted_candidate()
        reader = Path(os.environ.get(
            "SENS_TRIT_BIN", ROOT / "target/debug/sens-trit"
        ))
        outcome = process(reader, "eval-core4", self.payload)
        self.assertEqual(
            outcome.returncode, 0,
            "REAL Rust current evaluator BLOCKS six historical DEFINE closures; "
            "historical source-only 9-case oracle is NOT physical parity: "
            + outcome.stderr[-1800:],
        )
        self.assertTrue(outcome.stdout.strip(),
                        "eval returned zero but did not produce observable output")

    def test_first_real_global_calls_match_historical_nil_and_list_nil(self):
        """Prove TWO observable results from ORIGINAL six functions, not all nine."""
        self.test_real_current_rust_evaluator_accepts_emitted_six_definitions()
        reader = Path(os.environ.get(
            "SENS_TRIT_BIN", ROOT / "target/debug/sens-trit"
        ))
        # Appending a *probe call* to the pinned original in the external
        # fixture mirror tests runtime; it does NOT change original Git blob,
        # and this longer staged T5 is NOT a same-stem original admission.
        for suffix, expected in (
            ("(machine-block-empty)\n", "()"),
            ("(machine-block-one (00000001 ()))\n", "(())"),
        ):
            with self.subTest(call=suffix.strip()), tempfile.TemporaryDirectory(
                prefix="sens-block-real-call-"
            ) as folder:
                folder_path = Path(folder)
                trial = folder_path / "original-plus-probe.lisp"
                trial.write_bytes(self.original + b"\n" + suffix.encode("ascii"))
                payload_out = folder_path / "physical"
                receipt = folder_path / "receipt.json"
                cmd = process(
                    sys.executable, ROOT / "scripts/migrate-three-pass.py",
                    trial, "--out", payload_out, "--report", receipt,
                    "--source-era", "legacy",
                )
                self.assertEqual(cmd.returncode, 0, cmd.stderr[-1100:])
                run_record = json.loads(receipt.read_text(encoding="utf-8"))
                self.assertEqual(run_record["files"][0]["passes"]["pass1-sens8"], 18 if "00000001" in suffix else 17)
                self.assertEqual(run_record["files"][0]["passes"]["pass4-text7-global"], 1)
                packed = payload_out / "original-plus-probe.sens"
                self.assertTrue(packed.is_file())
                self.assertEqual(encode_words(decode_bytes(packed.read_bytes())),
                                 packed.read_bytes())
                observed = process(reader, "eval-core4", packed)
                self.assertEqual(observed.returncode, 0,
                                 "ACTUAL original global call current eval BLOCKED: "
                                 + " FIRST: " + observed.stderr[:1700]
                                 + " LAST: " + observed.stderr[-500:])
                self.assertEqual(observed.stdout.strip().splitlines()[-1], expected)
                self.assertEqual(SOURCE.read_bytes(), self.original)

    def test_historical_nine_case_oracle_is_not_misreported_as_physical(self):
        self.assertEqual(self.old_git_sha, EXPECTED_BLOB)
        self.assertEqual(SOURCE.read_bytes(), self.original)
        self.assertNotIn("independent_current_runtime_oracle_proven",
                         self.audit["files"][0])
        self.assertFalse((ROOT / "lib/machine/block.sens").exists())


if __name__ == "__main__":
    unittest.main()