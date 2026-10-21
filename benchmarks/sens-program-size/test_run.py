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

    def test_annotation_is_compact_and_reports_actual_t5m_byte_size(self):
        line = bench.annotation({
            "forms": 2,
            "source_bytes": 42,
            "ast_nodes": 9,
            "lowered_ast_nodes": 9,
            "exact_words": 3,
            "exact_bits": 29,
            "t5m_bytes": 7,
            "result": "2",
        })
        self.assertIn("AST=9/9", line)
        self.assertIn("words=3 bits=29", line)
        self.assertIn("T5M=7 B", line)
        self.assertIn("result=2", line)


if __name__ == "__main__":
    unittest.main()
