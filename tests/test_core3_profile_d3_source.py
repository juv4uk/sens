"""Core3 checker COND cutover: pinned source and two-field D1-bit law."""
import importlib.util
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts/check-core3-profile-contract.lisp"
PARSER = ROOT / "scripts/check_d3_legacy_logic.py"

spec = importlib.util.spec_from_file_location("core3_d3_scanner_guard", PARSER)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec and spec.loader
spec.loader.exec_module(mod)


PROJECTIONS = (
    ("0011", "визначити", 3),
    ("0010", "функція", 2),
    ("110", "за-умовою", 7),
    ("0100", "хибне?", 1),
    ("010", "атом?", 8),
    ("101", "тотожне?", 6),
    ("100", "перше", 1),
    ("001", "як-є", 28),
)


def deproject_ukr_heads(source):
    # Exact inverse of the approved full-ukr source projection. The selected
    # file's quoted compound result has no numeric heads inside its data.
    for bits, name, expected_count in PROJECTIONS:
        pattern = re.compile(re.escape("(") + re.escape(name) + r"(?=\s)")
        full_count = len(pattern.findall(source))
        if full_count != expected_count:
            raise AssertionError(
                f"unexpected {name} projection count: {full_count}"
            )
        source = pattern.sub("(" + bits, source)
    return source


class Core3SourceCutover(unittest.TestCase):
    def test_current_ukrainian_d6_let_and_two_field_predicate_law(self):
        source = TARGET.read_text(encoding="utf-8")
        self.assertEqual(
            source.count("(нехай ((вибір-механізму (ядро3-маршрут ідентичність-плюса виконавець)))"), 1
        )
        self.assertNotIn("(001000 ", source)
        current = deproject_ukr_heads(source)
        self.assertEqual(current.count("((010 (001 ()))"), 7)
        self.assertEqual(mod.scan_lisp(current, "scripts/check-core3-profile-contract.lisp"), [])

    def test_no_wrong_arity_or_host_truth_in_any_cond(self):
        current = deproject_ukr_heads(TARGET.read_text(encoding="utf-8"))
        findings = mod.scan_lisp(current, "scripts/check-core3-profile-contract.lisp")
        self.assertEqual(findings, [])

    def test_negative_controls_detect_host_truth_and_three_field(self):
        good = deproject_ukr_heads(TARGET.read_text(encoding="utf-8"))
        self.assertIn("COND_HOST_TRUTH", {f.rule for f in mod.scan_lisp(
            good.replace("((010 (001 ()))", "(t", 1), "lib/corrupted.lisp")})
        self.assertIn("COND_NOT_TWO_FIELDS", {f.rule for f in mod.scan_lisp(
            good.replace("((010 (001 ()))", "((010 (001 ())) (0)", 1),
            "lib/corrupted.lisp")})


class Core4ObserverSourceCutover(unittest.TestCase):
    CASES = {
        "scripts/check-core4-predicate-answer-scale.lisp":
            ("cbc2f3e50b28b7d78b52453c7434e9319095efd1", "pas"),
        "experiments/core4-predicate-answer-carrier-matrix.lisp":
            ("84bfc7effc2d378fad201a568763ca1401fe0fb7", "cam"),
    }

    def test_two_observers_have_pinned_bit_predicate_and_literal_d1_fallback(self):
        for path, (blob, prefix) in self.CASES.items():
            with self.subTest(path=path):
                original = subprocess.run(
                    ["git", "cat-file", "blob", blob], cwd=ROOT,
                    capture_output=True, check=True
                ).stdout.decode("utf-8")
                first = (
                    f"((11110111 {prefix}-observed {prefix}-expected)\n"
                    "   (1)\n"
                )
                second = "((11110111 1 1) 1\n"
                self.assertEqual(original.count(first), 1)
                self.assertEqual(original.count(second), 1)
                expected = (original.replace(first, first.replace("   (1)\n", ""))
                            .replace(second, "((010 (001 ()))\n"))
                current = (ROOT / path).read_text(encoding="utf-8")
                self.assertEqual(current, expected)
                self.assertEqual(mod.scan_lisp(current, path), [],
                                 "two-field D3 with exact D1 branch bits")


if __name__ == "__main__":
    unittest.main()
