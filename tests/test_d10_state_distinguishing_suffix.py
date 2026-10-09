"""Independent exact research witnesses for binary DFA suffix law."""
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_d10_state_distinguishing_suffix as law

class StateSuffixTests(unittest.TestCase):
    def test_all_named_cases(self):
        dossier = law.validate_dossier()
        self.assertEqual(len(dossier["witnesses"]), 6)
        for row in dossier["witnesses"]:
            args = (row["transitions"], row["accepting"], row["p"], row["q"])
            self.assertEqual(law.product_bfs(*args), row["expected"])
            self.assertEqual(law.independent_refinement(*args), row["expected"])
            law.assert_exact_witness(*args, row["expected"])

    def test_exhaustive_cross_model_witnesses(self):
        r = law.evidence()
        self.assertEqual(r["exact_exhaustive_2_state_cases"], 256)
        self.assertEqual(r["exact_exhaustive_3_state_seeded_cases"], 128)
        self.assertEqual(r["actual_owner_2034_dfa_state_pairs"], 36)
        self.assertEqual(r["ratified"], 0)
        self.assertEqual(r["selected_delta"], 0)
        self.assertEqual(r["original_executable_migrations_admitted"], 0)

    def test_epsilon_is_a_real_witness(self):
        args = ([[0, 0], [1, 1]], [0, 1], 0, 1)
        self.assertEqual(law.product_bfs(*args), law.result(""))
        self.assertNotEqual(law.result(""), law.result(None))
        with self.assertRaises(law.Blocked):
            law.assert_exact_witness(*args, law.result(None))

    def test_falsified_tables_and_lex_order_block(self):
        for args in [([], [], 0, 0), ([[0]], [0], 0, 0),
                     ([[0, 2]], [0], 0, 0), ([[0, 0]], [True], 0, 0),
                     ([[0, 0]], [2], 0, 0), ([[0, 0]], [0], True, 0)]:
            with self.subTest(args=args), self.assertRaises(law.Blocked):
                law.product_bfs(*args)
        args = ([[2, 3], [3, 2], [2, 2], [3, 3]], [0, 0, 1, 0], 0, 1)
        self.assertEqual(law.product_bfs(*args), law.result("0"))
        for word in ("1", "00", None):
            with self.assertRaises(law.Blocked):
                law.assert_exact_witness(*args, law.result(word))

if __name__ == "__main__":
    unittest.main()
