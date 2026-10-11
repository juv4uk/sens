"""Regression witness for six source-level x86 machine SID8 cutovers.

Does not claim execution parity or certify physical original migration.
Does not rewrite generated machine tables, quoted data or D8 identities.
"""
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
MACHINE = {
    "lib/machine/admission/x86-64.lisp": (18, 19),
    "lib/machine/atoms/x86-64.lisp": (132, 132),
    "lib/machine/encoding/x86-64.lisp": (225, 229),
    "lib/machine/operands/x86-64.lisp": (38, 38),
    "lib/machine/profile/minimal-runtime-x86-64.lisp": (24, 21),
    "lib/machine/projection/x86-64.lisp": (2, 2),
}

class MachineSourceCutover(unittest.TestCase):
    def test_ratified_exact_domain_core_words(self):
        domains = json.loads((ROOT / "knowledge/d1-d9-foundation.json").read_text())["domains"]
        self.assertEqual(domains["D3"]["residents"]["001"], "QUOTE")
        self.assertEqual(domains["D4"]["residents"]["0011"], "DEFINE")
        self.assertEqual(domains["D4"]["residents"]["0010"], "LAMBDA")

    def test_six_machine_sources_have_current_function_heads(self):
        for path, (definitions, lambdas) in MACHINE.items():
            with self.subTest(path=path):
                text = (ROOT / path).read_text(encoding="utf-8")
                self.assertEqual(len(re.findall(r"\(\s*0011(?=\s|\))", text)), definitions)
                self.assertEqual(len(re.findall(r"\(\s*0010(?=\s|\))", text)), lambdas)
                self.assertNotRegex(text, r"\(\s*00001001(?=\s|\))")
                self.assertNotRegex(text, r"\(\s*00001000(?=\s|\))")

    def test_generated_machine_evidence_stays_generated(self):
        for path in (
            "lib/machine/encoding/coverage.lisp",
            "lib/machine/encoding/admitted-iclass-index.lisp",
            "lib/machine/encoding/admission-iclass-projection.lisp",
        ):
            with self.subTest(path=path):
                text = (ROOT / path).read_text(encoding="utf-8")
                self.assertIn("GENERATED", text[:240])

if __name__ == "__main__":
    unittest.main()
