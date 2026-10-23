"""Вхідний аудит доменної драбини — не підміна виконання SENS."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/check_semantic_registry.py"
SPEC = importlib.util.spec_from_file_location("check_semantic_registry", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def domain(width: int):
    path = ROOT / f"lib/domains/d{width}.lisp"
    roots = MODULE.parse_all(MODULE.tokens(path.read_text(encoding="utf-8")))
    assert len(roots) == 1
    return roots[0]


class RatifiedDomainRegistryTests(unittest.TestCase):
    def test_all_ten_domain_sources_are_exact_and_complete(self):
        self.assertEqual(sum(MODULE.check(domain(w), w)[0] for w in range(1, 11)), 2046)

    def test_current_registry_reads_native_domain_ladder(self):
        text = (ROOT / "lib/surface/semantic-registry.lisp").read_text(encoding="utf-8")
        self.assertEqual(MODULE.parse_all(MODULE.tokens(text)),
                         [["прочитати-семантичний-реєстр"]])

    def test_legacy_eight_bit_registry_is_not_current_authority(self):
        with self.assertRaisesRegex(ValueError, "domain-table-1"):
            MODULE.check([["00000000", ["en", "quote"]]], 8)

    def test_bit_width_and_identity_swap_are_rejected(self):
        rows = domain(3)
        rows[1][0] = "00000001"
        with self.assertRaisesRegex(ValueError, "ширина"):
            MODULE.check(rows, 3)
        rows = domain(3)
        rows[1][0] = "010"
        with self.assertRaisesRegex(ValueError, "перестановка"):
            MODULE.check(rows, 3)

    def test_duplicate_and_missing_rows_are_rejected(self):
        rows = domain(3)
        rows[1] = rows[2]
        with self.assertRaisesRegex(ValueError, "перестановка"):
            MODULE.check(rows, 3)
        rows = domain(3)
        rows.pop()
        with self.assertRaisesRegex(ValueError, "резидентів"):
            MODULE.check(rows, 3)

    def test_malformed_ukrainian_surface_is_rejected(self):
        rows = domain(3)
        rows[1][2][0] = "english"
        with self.assertRaisesRegex(ValueError, "укр"):
            MODULE.check(rows, 3)

    def test_d7_cannot_create_callable_lisp_function(self):
        rows = domain(7)
        rows[0][5][1] = "FAKE-EXEC"
        with self.assertRaisesRegex(ValueError, "не можуть визначати Lisp"):
            MODULE.check(rows, 7)

    def test_semicolon_inside_quoted_string_is_data(self):
        source = '(domain-table-1 (0 (ук "а;б") (укр а) (san а) (en a) (LISP ()) (sym ()))\n' + \
                 '(1 (ук б) (укр б) (san б) (en b) (LISP ()) (sym ()))) ; after'
        self.assertEqual(MODULE.check(MODULE.parse_all(MODULE.tokens(source))[0], 1)[0], 2)


if __name__ == "__main__":
    unittest.main()
