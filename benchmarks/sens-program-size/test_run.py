import importlib.util
import unittest
from pathlib import Path

MODULE = Path(__file__).with_name("run.py")
SPEC = importlib.util.spec_from_file_location("sens_program_size", MODULE)
bench = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bench)


class ProgramSizeTests(unittest.TestCase):
    def test_counts_exact_width_binary_projection_without_assigning_domain_meaning(self):
        words, bits = bench.count_exact_words("10 001 000000000000000000000101")
        self.assertEqual(words, 3)
        self.assertEqual(bits, 29)

    def test_rejects_non_binary_or_empty_projection(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            bench.count_exact_words(" \n")
        with self.assertRaisesRegex(ValueError, "non-binary"):
            bench.count_exact_words("10 01x")

    def test_counts_actual_t5_separator_and_tail_trits(self):
        costs = bench.transport_trit_cost(word_count=3, semantic_bits=29, physical_bytes=7)
        self.assertEqual(costs, {"separators": 2, "tail": 4, "trit2": 6})
        with self.assertRaisesRegex(ValueError, "disagree"):
            bench.transport_trit_cost(word_count=3, semantic_bits=29, physical_bytes=6)

    def test_comparison_annotation_reports_candidate_tradeoff(self):
        before = {
            "eval_visits": 8,
            "lowered_ast_nodes": 8,
            "exact_words": 11,
            "exact_bits": 64,
            "trit2_count": 12,
            "t5m_bytes": 16,
            "result": "24",
        }
        after = {
            "eval_visits": 4,
            "lowered_ast_nodes": 4,
            "exact_words": 7,
            "exact_bits": 49,
            "trit2_count": 8,
            "t5m_bytes": 12,
            "result": "24",
        }
        line = bench.comparison_annotation(before, after)
        self.assertIn("AST=8→4", line)
        self.assertIn("visits=8→4", line)
        self.assertIn("words=11→7", line)
        self.assertIn("bits=64→49", line)
        self.assertIn("trit2=12→8", line)
        self.assertIn("T5M=16→12 B", line)
        self.assertIn("result=24; parity=PASS", line)
        after["result"] = "25"
        with self.assertRaisesRegex(ValueError, "changes result"):
            bench.comparison_annotation(before, after)

if __name__ == "__main__":
    unittest.main()
