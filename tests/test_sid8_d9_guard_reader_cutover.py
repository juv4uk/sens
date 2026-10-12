"""Pin the exact source-only guard reader cutover, without asserting runtime parity."""
from pathlib import Path
import json
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = "scripts/semantic-authority-guard-enforce.lisp"
OLD_SHA = "784a033d605c5ad89631a12707f5800ec83fe967"

class GuardD9SourceCutover(unittest.TestCase):
    def test_exact_old_git_blob_to_ratified_d9_source(self):
        historic = subprocess.run(
            ["git", "cat-file", "blob", OLD_SHA], cwd=ROOT,
            capture_output=True, check=True
        ).stdout.decode("utf-8")
        before = '(01001011 (10100110 "tests/semantic-authority-verdict.lisp"))'
        after = '(110101001 (110110111 "tests/semantic-authority-verdict.lisp"))'
        self.assertEqual(historic.count(before), 1)
        self.assertEqual((ROOT / PATH).read_text(encoding="utf-8"),
                         historic.replace(before, after))
    def test_exact_residents_and_independent_existing_peer_usage(self):
        foundation = json.loads((ROOT / "knowledge/d1-d9-foundation.json").read_text())
        self.assertEqual(foundation["domains"]["D9"]["residents"]["110101001"], "READ-ALL")
        self.assertEqual(foundation["domains"]["D9"]["residents"]["110110111"], "READ-FILE")
        self.assertNotEqual(foundation["domains"]["D8"]["residents"]["01001011"], "READ-ALL")
        self.assertNotEqual(foundation["domains"]["D8"]["residents"]["10100110"], "READ-FILE")
        peer = (ROOT / "scripts/semantic-authority-guard.lisp").read_text()
        self.assertIn('(110101001 (110110111 "tests/semantic-authority-changes.lisp"))', peer)

if __name__ == "__main__":
    unittest.main()
