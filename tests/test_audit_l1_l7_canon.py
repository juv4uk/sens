"""Regression witnesses for fail-closed owner L1–L7 migration triage."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit-l1-l7-canon.py"


class L1L7CanonicalGateTest(unittest.TestCase):
    def invoke(self, source=None, report=None):
        args = [sys.executable, str(SCRIPT)]
        if source is None:
            args += ["--self-test"]
        else:
            args += [str(source), "--report", str(report)]
        return subprocess.run(args, cwd=ROOT, text=True,
                              capture_output=True, timeout=60, check=False)

    def test_contextual_t_and_retired_semantics(self):
        run = self.invoke()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("L1-L7-PREFLIGHT-SELF-TEST: PASS", run.stdout)

    def test_l7_parse_error_preserves_original(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "broken.lisp"
            r = Path(directory) / "audit.json"
            source = "(cond (t x)"
            p.write_text(source, encoding="utf-8")
            run = self.invoke(p, r)
            self.assertEqual(run.returncode, 2, run.stderr)
            report = json.loads(r.read_text(encoding="utf-8"))
            self.assertEqual(report["summary"].get("UNPARSEABLE_L7"), 1)
            self.assertEqual(report["owner_review_unparseable"], ["broken.lisp"])
            self.assertEqual(p.read_text(encoding="utf-8"), source)
            self.assertFalse(p.with_suffix(".sens").exists())

    def test_l4_unproved_helper_is_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "legacy.lisp"
            r = Path(directory) / "audit.json"
            p.write_text("(equal? x y)", encoding="utf-8")
            run = self.invoke(p, r)
            self.assertEqual(run.returncode, 2, run.stderr)
            report = json.loads(r.read_text(encoding="utf-8"))
            self.assertEqual(report["files"][0]["status"], "BLOCK")
            self.assertEqual(report["files"][0]["blockers"][0]["rule"], "L4")
            self.assertFalse(p.with_suffix(".sens").exists())

    def test_l1_cond_requires_exact_predicate(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "truthy.lisp"
            r = Path(directory) / "audit.json"
            p.write_text("(cond ((car x) (quote ())))", encoding="utf-8")
            run = self.invoke(p, r)
            self.assertEqual(run.returncode, 2, run.stderr)
            report = json.loads(r.read_text(encoding="utf-8"))
            self.assertEqual(report["files"][0]["status"], "BLOCK")
            self.assertEqual(report["files"][0]["blockers"][0]["rule"], "L1")


if __name__ == "__main__":
    unittest.main()
