"""Core3 checker COND cutover: pinned source and two-field D1-bit law."""
import importlib.util
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts/check-core3-profile-contract.lisp"
OLD_BLOB = "5cc3fc3e4d6496392d2bb302951aefe579ec6f31"
PARSER = ROOT / "scripts/check_d3_legacy_logic.py"

spec = importlib.util.spec_from_file_location("core3_d3_scanner_guard", PARSER)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec and spec.loader
spec.loader.exec_module(mod)


def expected_cutover(source):
    assert source.count("((010 selection) (0)") == 1
    assert source.count("((001 c3-no) c3-no") == 6
    assert source.count("((001 c3-fail) c3-fail") == 1
    assert len(re.findall(r"\)\s+\(1\)\s*\n", source)) == 6
    rewritten = (source.replace("((010 selection) (0)",
                                "((0100 (010 selection))")
                 .replace("((001 c3-no) c3-no", "((010 (001 ()))")
                 .replace("((001 c3-fail) c3-fail", "((010 (001 ()))"))
    return re.sub(r"\)\s+\(1\)\s*\n", ")\n", rewritten)


class Core3SourceCutover(unittest.TestCase):
    def test_exact_source_matches_frozen_original_and_only_predicate_law(self):
        old = subprocess.run(["git", "cat-file", "blob", OLD_BLOB],
                             cwd=ROOT, check=True, capture_output=True).stdout.decode()
        current = TARGET.read_text(encoding="utf-8")
        self.assertEqual(expected_cutover(old), current)
        self.assertIn("((0100 (010 selection))", current)
        self.assertEqual(current.count("((010 (001 ()))"), 7)

    def test_no_wrong_arity_or_host_truth_in_any_cond(self):
        current = TARGET.read_text(encoding="utf-8")
        findings = mod.scan_lisp(current, "scripts/check-core3-profile-contract.lisp")
        self.assertEqual(findings, [])

    def test_negative_controls_detect_host_truth_and_three_field(self):
        good = TARGET.read_text(encoding="utf-8")
        self.assertIn("COND_HOST_TRUTH", {f.rule for f in mod.scan_lisp(
            good.replace("((010 (001 ()))", "((t", 1), "lib/corrupted.lisp")})
        self.assertIn("COND_NOT_TWO_FIELDS", {f.rule for f in mod.scan_lisp(
            good.replace("((010 (001 ()))", "((010 (001 ())) (0)", 1),
            "lib/corrupted.lisp")})


if __name__ == "__main__":
    unittest.main()
