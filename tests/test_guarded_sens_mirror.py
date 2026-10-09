#!/usr/bin/env python3
"""No partial T5 .sens files may be published from a mixed source batch."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import os

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/guarded_sens_mirror.py"
spec = importlib.util.spec_from_file_location("guarded_mirror_under_test", SCRIPT)
assert spec and spec.loader
mirror = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mirror)

# Fake driver deliberately reproduces legacy bug: it writes some .sens
# but still reports exit code 0 when other .lisp files cannot be migrated.
FAKE_DRIVER = r"""
import argparse, hashlib, json, os, sys
from pathlib import Path
sys.path.insert(0, os.environ["SENS_SCRIPTS"])
from sens_t5_codec import encode_projection, typed_sha256, decode_bytes
p=argparse.ArgumentParser()
p.add_argument("root", type=Path)
p.add_argument("--foundation")
p.add_argument("--sens-mirror", type=Path)
p.add_argument("--report", type=Path)
a=p.parse_args()
rows=[]
written=blocked=0
for src in sorted(a.root.rglob("*.lisp")):
    rel=src.relative_to(a.root)
    name=rel.as_posix()
    target=rel.with_suffix(".sens")
    content=src.read_text()
    if content.startswith("BLOCK"):
        rows.append({"path":name, "status":"blocked",
                     "blockers":[{"reason":"unmapped domain"}]})
        blocked+=1
        continue
    raw=encode_projection(content)
    destination=a.sens_mirror/target
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_bytes(raw)
    row={"path":name, "output":target.as_posix(),
         "status":"sens-written", "physical_sha256":hashlib.sha256(raw).hexdigest(),
         "typed_word_sha256":typed_sha256(decode_bytes(raw))}
    rows.append(row)
    written+=1
report={"summary":{"files_seen":len(rows), "files_written":written,
                   "files_blocked":blocked}, "files":rows}
a.report.parent.mkdir(parents=True,exist_ok=True)
a.report.write_text(json.dumps(report))
sys.exit(0)
"""


class GuardedMirrorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.root = self.work / "src"
        self.root.mkdir()
        self.output = self.work / "out"
        self.driver = self.work / "fake" / "driver.py"
        self.driver.parent.mkdir()
        self.driver.write_text(FAKE_DRIVER)
        self.foundation = self.work / "d1-d9.json"
        self.foundation.write_text("{}")
        self.previous = os.environ.get("SENS_SCRIPTS")
        os.environ["SENS_SCRIPTS"] = str(ROOT / "scripts")
        self.addCleanup(self.restore_env)

    def restore_env(self):
        if self.previous is None:
            os.environ.pop("SENS_SCRIPTS", None)
        else:
            os.environ["SENS_SCRIPTS"] = self.previous

    def migrate(self):
        return mirror.transaction(root=self.root, out=self.output,
                                  driver=self.driver,
                                  foundation=self.foundation)

    def test_two_sources_publish_all_together_as_binary_t5(self):
        (self.root / "one.lisp").write_text("10 01")
        (self.root / "nested").mkdir()
        (self.root / "nested" / "two.lisp").write_text("000")
        result = self.migrate()
        self.assertEqual(result["summary"]["physical_files"], 2)
        self.assertEqual(result["summary"]["semantic_oracle_verified"], 0)
        self.assertEqual((self.output / "one.sens").read_bytes(), b"\x64")
        self.assertEqual((self.output / "nested" / "two.sens").read_bytes(), b"\x08")
        self.assertFalse((self.output / "one").exists())
        self.assertFalse((self.output / "one.lisp").exists())
        self.assertEqual((self.root / "one.lisp").read_text(), "10 01")
        receipt = json.loads((self.output / "_physical-migration-report.json").read_text())
        self.assertEqual(receipt["semantics"], "NOT_VERIFIED")
        self.assertEqual(receipt["summary"]["sources"], 2)
        self.assertFalse(list(self.work.glob(".t5-transaction-*")))

    def test_mixed_good_and_blocked_publish_nothing_even_on_exit_zero(self):
        (self.root / "good.lisp").write_text("10 01")
        (self.root / "unmapped.lisp").write_text("BLOCK bad-domain")
        with self.assertRaisesRegex(mirror.TransactionBlocked, "non-atomic batch"):
            self.migrate()
        self.assertFalse(self.output.exists())
        self.assertEqual(sorted(p.name for p in self.root.iterdir()),
                         ["good.lisp", "unmapped.lisp"])
        self.assertFalse(list(self.work.glob(".t5-transaction-*")))

    def test_existing_output_never_overwritten(self):
        (self.root / "good.lisp").write_text("10 01")
        self.output.mkdir()
        (self.output / "valuable").write_text("KEEP")
        with self.assertRaisesRegex(mirror.TransactionBlocked, "already exists"):
            self.migrate()
        self.assertEqual((self.output / "valuable").read_text(), "KEEP")

    def test_second_run_refuses_to_replace_successful_batch(self):
        (self.root / "good.lisp").write_text("000")
        self.migrate()
        first = (self.output / "good.sens").read_bytes()
        with self.assertRaisesRegex(mirror.TransactionBlocked, "already exists"):
            self.migrate()
        self.assertEqual((self.output / "good.sens").read_bytes(), first)

    def test_noncanonical_raw_t5_fails_before_visibility(self):
        (self.root / "bad.lisp").write_text("10 01")
        self.driver.write_text(self.driver.read_text().replace(
            "destination.write_bytes(raw)",
            "destination.write_bytes(bytes([243]))"
        ))
        with self.assertRaisesRegex(mirror.TransactionBlocked, "invalid physical T5"):
            self.migrate()
        self.assertFalse(self.output.exists())

    def test_empty_input_cannot_be_marked_complete(self):
        with self.assertRaisesRegex(mirror.TransactionBlocked, "empty migration corpus"):
            self.migrate()
        self.assertFalse(self.output.exists())

    def test_unsafe_report_path_is_refused(self):
        for bad in ["../escaped.lisp", "/root.lisp", r"sub\path.lisp"]:
            with self.subTest(path=bad), self.assertRaises(mirror.TransactionBlocked):
                mirror.checked_relative(bad)

    def test_input_output_nesting_is_forbidden(self):
        (self.root / "ok.lisp").write_text("000")
        with self.assertRaisesRegex(mirror.TransactionBlocked, "separate"):
            mirror.transaction(root=self.root, out=self.root/"out",
                               driver=self.driver, foundation=self.foundation)

    def test_symlink_input_fails_before_conversion(self):
        (self.root / "ok.lisp").write_text("000")
        (self.root / "link.lisp").symlink_to(self.root / "ok.lisp")
        with self.assertRaisesRegex(mirror.TransactionBlocked, "unsafe original"):
            self.migrate()
        self.assertFalse(self.output.exists())

    def test_never_claim_unverified_semantic_oracle(self):
        (self.root / "ok.lisp").write_text("000")
        result = self.migrate()
        for entry in result["files"]:
            self.assertEqual(entry["admission"],
                             "PHYSICAL_ONLY_NOT_SEMANTIC_ORACLE")


if __name__ == "__main__":
    unittest.main()
