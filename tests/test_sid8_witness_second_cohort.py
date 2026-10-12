"""Independent lexical witness for 12 more in-place SID8 -> domain Lisp files.

Audit source AST against immutable pre-migration Git blobs, including explicit
preservation of 20 historical quoted call-shaped data in the x86-64 case.
No claims about runtime parity or independent physical file admission.
"""
from pathlib import Path
import importlib.util
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "sens_sid8_second_audit", ROOT / "scripts" / "audit_lisp_migration_edits.py"
)
assert spec and spec.loader
audit = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = audit
spec.loader.exec_module(audit)

COHORT = {
    "tests/fixtures/machine-register-width-witness.lisp": ("882e0f74e7e276e75e42add7c7d1d793ef8e4d56", 77),
    "tests/fixtures/x86-64-instruction-set-witness.lisp": ("a5551fc94d9e1d68900009d424c37e911d8504a2", 40),
    "tests/fixtures/structural-observation-contract-witness.lisp": ("6e9f54d513052ae39e18e70571bb14fa39e78c28", 184),
    "tests/fixtures/native-first-coverage-ledger-witness.lisp": ("573631c421a9f00db85af1055759b794ec9c497a", 240),
    "tests/fixtures/native-first-dispatch-witness.lisp": ("1fce83fa91b0af40d108d5f52874648480d65cb0", 22),
    "tests/fixtures/native-first-execution-witness.lisp": ("10da52de43829fbf27afc714dd2a7c6e5f3522fd", 20),
    "tests/fixtures/native-first-parity-witness.lisp": ("20dc71a12a239ee1d2851abfcb0916a562c039f6", 18),
    "tests/fixtures/native-first-totality-witness.lisp": ("1d5cb2f71e126b46c3475a2c5f90e463882312df", 14),
    "tests/fixtures/mechanism-selector-1047-witness.lisp": ("d4d35c29bd802aba82e5bb28647b6de87e097c9f", 48),
    "tests/fixtures/mathematical-result-taxonomy-witness.lisp": ("d82fb203b0bb24dd35b0e72f603a27d8204bea8c", 143),
    "tests/fixtures/machine-current-gpr-atoms-witness.lisp": ("7bf5d0012c7d7a22bb3738efe018157b3a232192", 432),
    "tests/fixtures/translation-symbol-boundary-witness.lisp": ("7b4c22154e7df08c1794e596db7ef199638ddd36", 63),
}


class SecondWitnessCohort(unittest.TestCase):
    def test_exact_lisp_ast_context_and_identity_count(self):
        total = 0
        for path, (blob, expected) in COHORT.items():
            with self.subTest(path=path):
                source = subprocess.check_output(
                    ["git", "cat-file", "blob", blob], cwd=ROOT
                ).decode("utf-8")
                migrated = (ROOT / path).read_text(encoding="utf-8")
                verdict = audit.audit_edit(source, migrated)
                self.assertEqual(verdict["status"], "LEXICAL_CONTEXT_ONLY")
                self.assertEqual(verdict["semantic_parity"], "NOT_CHECKED")
                parser = audit.parser
                a = [t.text for t in parser.tokenize(parser.strip_comments(source))]
                b = [t.text for t in parser.tokenize(parser.strip_comments(migrated))]
                self.assertEqual(len(a), len(b))
                count = sum(x != y for x, y in zip(a, b))
                self.assertEqual(count, expected)
                total += count
        self.assertEqual(len(COHORT), 12)
        self.assertEqual(total, 1301)

    def test_quoted_x86_machine_data_retained(self):
        path = "tests/fixtures/x86-64-instruction-set-witness.lisp"
        old, _expected = COHORT[path]
        before = subprocess.check_output(["git", "cat-file", "blob", old], cwd=ROOT).decode("utf-8")
        after = (ROOT / path).read_text(encoding="utf-8")
        # Historical machine datum is preserved as part of the AST, not renamed:
        self.assertEqual(audit.audit_edit(before, after)["semantic_parity"], "NOT_CHECKED")
        self.assertIn("(0011 ", after)
        self.assertNotIn("(00001001 ", after)


if __name__ == "__main__":
    unittest.main()
