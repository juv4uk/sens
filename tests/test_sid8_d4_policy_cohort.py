"""Pinned source-only D4 cutover for five legacy D3 policy programs.

This deliberately proves only exact source substitutions. Their historical
COND semantics remain blocked until an independent two-field D3 runtime oracle.
"""
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]

# Blob of the exact original .lisp source, plus the number of admitted
# D4 call-head substitutions. Git history is evidence, not code authority.
SOURCES = {
    "knowledge/guard-reference.lisp": ("f97371fd503075caec9344062847fb7c0e7642e7", 25),
    "knowledge/guard-fact-policy.lisp": ("d137f1b92a060980e0a2696300469ac0e9ec1b90", 6),
    "scripts/enforce-function-table-mechanisms.lisp": ("472fdf97d50a4401302a42a2e56a095794f8c9f6", 2),
    "scripts/enforce-island-math-evidence.lisp": ("eb9ae7d9c1b7a33f4c4cc429d0ee7d0bab701fe4", 2),
    "scripts/semantic-authority-guard-enforce.lisp": ("8e744541cb225f06f47a998204e7fc3d91f9082b", 3),
}

D4_HEAD = re.compile(r"\((\s*)(00001001|00001000)(?=[\s)])")
D3_LEGACY_COND = re.compile(r"\(\s*00000111(?=[\s)])")


class PolicyD4PartialCutover(unittest.TestCase):
    def test_all_five_originals_change_only_exact_d4_call_heads(self):
        self.assertEqual(len(SOURCES), 5)
        total = 0
        for path, (blob, expected_count) in SOURCES.items():
            with self.subTest(path=path):
                original = subprocess.run(
                    ["git", "cat-file", "blob", blob],
                    cwd=ROOT, capture_output=True, check=True,
                ).stdout.decode("utf-8")
                current = (ROOT / path).read_text(encoding="utf-8")

                def replace(match):
                    nonlocal count
                    count += 1
                    return "(" + match.group(1) + (
                        "0011" if match.group(2) == "00001001" else "0010"
                    )

                count = 0
                expected = D4_HEAD.sub(replace, original)
                self.assertEqual(count, expected_count)
                self.assertEqual(current, expected,
                                 "source moved beyond the pinned D4-only proof")
                self.assertNotRegex(current, D4_HEAD)
                self.assertRegex(current, D3_LEGACY_COND)
                total += count
        self.assertEqual(total, 38)


if __name__ == "__main__":
    unittest.main()
