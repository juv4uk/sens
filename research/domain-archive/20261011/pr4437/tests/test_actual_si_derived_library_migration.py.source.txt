"""Real application-library regression, not a domain table or kernel fixture.

The current typed carrier MUST NOT claim whole-library migration when it only
accepts Dn:bits debug records. This test is intentional fail-closed coverage.
"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from domain_word_carrier import CarrierError, parse_display


class RealLibraryMigrationBoundaryTest(unittest.TestCase):
    def test_si_derived_is_real_executable_library_and_not_falsely_convertible(self):
        source = (ROOT / "lib/si-derived.lisp").read_text(encoding="utf-8")
        source_without_comments = "\n".join(line.split(";", 1)[0] for line in source.splitlines())
        heads = re.findall(r"\\(\\s*([01]{8})\\b", source_without_comments)
        self.assertEqual(len(heads), 18)
        self.assertEqual(heads.count("00001001"), 7)  # historical DEFINE, D4:0011
        self.assertEqual(heads.count("00001110"), 7)  # historical TIMES, candidate D5:10110
        self.assertEqual(heads.count("00001111"), 4)  # historical DIVIDE, candidate D8:11110110

        # Canonical D7 TEXT DIGIT 2 is not automatically numeric literal 2.
        self.assertEqual(len(re.findall(r"(?<![\\w])2(?![\\w])", source_without_comments)), 3)
        self.assertIn("si:elementary-charge", source_without_comments)
        with self.assertRaises(CarrierError):
            parse_display(source)

    def test_si_derived_is_not_core_or_domain_table(self):
        file = ROOT / "lib/si-derived.lisp"
        self.assertNotIn(file.name, {"core.lisp", "core3.lisp", "d3.lisp"})
        source = file.read_text(encoding="utf-8")
        self.assertIn("si:faraday-constant", source)
        self.assertIn("si:magnetic-flux-quantum", source)


if __name__ == "__main__":
    unittest.main()
