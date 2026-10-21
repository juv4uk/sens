import importlib.util
import unittest
from pathlib import Path

MODULE = Path(__file__).with_name("run.py")
SPEC = importlib.util.spec_from_file_location("sens_program_size", MODULE)
bench = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bench)


class ProgramSizeTests(unittest.TestCase):
    def test_reads_metrics_reported_by_physical_sens_execution(self):
        stats = bench.parse_binary_metrics(
            "SENS_BINARY_BENCH AST_NODES=6 EVAL_VISITS=4 RESULT=()"
        )
        self.assertEqual(stats, {"ast_nodes": 6, "eval_visits": 4, "result": "()"})

    def test_rejects_missing_physical_execution_metrics(self):
        with self.assertRaisesRegex(ValueError, "missing binary metrics"):
            bench.parse_binary_metrics("()")

    def test_binary_annotation_reports_one_real_sens_program(self):
        stats = {
            "ast_nodes": 6,
            "eval_visits": 4,
            "exact_words": 5,
            "exact_bits": 17,
            "trit2_count": 2,
            "t5m_bytes": 4,
            "result": "()",
        }
        line = bench.binary_annotation("lib/example.sens", stats)
        self.assertIn("path=lib/example.sens", line)
        self.assertIn("AST=6", line)
        self.assertIn("visits=4", line)
        self.assertIn("words=5 bits=17", line)
        self.assertIn("T5M=4 B", line)
        self.assertIn("result=()", line)

    def test_loads_only_regular_sens_binary_paths_from_manifest(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / "program.sens"
            binary.write_bytes(b"\x00\x01")
            manifest = root / "binaries.txt"
            manifest.write_text("program.sens\n", encoding="utf-8")
            self.assertEqual(bench.load_binary_manifest(manifest, root), [binary])
            manifest.write_text("program.lisp\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "expected a .sens binary"):
                bench.load_binary_manifest(manifest, root)

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

if __name__ == "__main__":
    unittest.main()
