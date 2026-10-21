"""Чинні D3/D1 закони SENS: джерельні свідки та негативні мутації."""
import importlib.util
from pathlib import Path
import re
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
    # Джерела змінюються разом із мовою: історичний Git blob НЕ є оракулом.
    # Зіставляємо поточну українську D3/D1 форму та два негативні мутанти.
    CASES = (
        ("scripts/check-core4-predicate-answer-scale.lisp",
         "core4-predicate-answer-scale-ok",
         "core4-predicate-answer-scale-mismatch"),
        ("experiments/core4-predicate-answer-carrier-matrix.lisp",
         "core4-answer-carrier-matrix-ok",
         "core4-answer-carrier-matrix-mismatch"),
    )

    def test_current_two_field_d1_and_negative_mutants(self):
        for path, success, failure in self.CASES:
            with self.subTest(path=path):
                current = (ROOT / path).read_text(encoding="utf-8")
                predicate = "((атом? (як-є ()))"
                self.assertEqual(current.count(predicate), 1)
                self.assertEqual(current.count("(за-умовою"), 1)
                self.assertIn("(як-є (" + success + "))", current)
                self.assertIn("(як-є " + failure + ")", current)
                self.assertNotIn("(так ", current)
                self.assertEqual(mod.scan_lisp(current, path), [],
                                 "поточна двопольова D3 COND, обчислювана істина D1")

                host_truth = current.replace(predicate, "(t", 1)
                self.assertIn(
                    "COND_HOST_TRUTH",
                    {finding.rule for finding in mod.scan_lisp(host_truth, path)},
                    "старий host-t повинен бути знайдений, не підтверджений",
                )
                malformed = current.replace(
                    predicate, predicate + " (як-є зайве)", 1,
                )
                self.assertIn(
                    "COND_NOT_TWO_FIELDS",
                    {finding.rule for finding in mod.scan_lisp(malformed, path)},
                    "трипольова D3 COND не може пройти позитивним свідком",
                )


if __name__ == "__main__":
    unittest.main()
