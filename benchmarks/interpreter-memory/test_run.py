import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("run.py")
SPEC = importlib.util.spec_from_file_location("interpreter_memory", MODULE_PATH)
memory = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(memory)


class InterpreterMemoryTests(unittest.TestCase):
    def test_report_keeps_raw_samples_and_labels_smoke_scope(self):
        report = memory.render_report(
            [
                {"language": "SENS / T5M", "samples_kib": [1200, 1000, 1100]},
                {"language": "Python", "samples_kib": [900, 800, 850]},
            ],
            repetitions=3,
        )

        self.assertIn("| SENS / T5M | 1100 | 1200, 1000, 1100 |", report)
        self.assertIn("| Python | 850 | 900, 800, 850 |", report)
        self.assertIn("smoke", report.lower())
        self.assertIn("піковий RSS для всього процесу", report)
        self.assertIn("не рейтинг усіх мов", report)

    def test_numeric_report_keeps_shared_and_deep_copy_rss_samples_distinct(self):
        report = memory.render_numeric_report(
            [
                {
                    "strategy": "SENS evaluator / shared clone",
                    "width_bits": 196608,
                    "retained_values": 128,
                    "samples_kib": [21000, 21200, 21100],
                },
                {
                    "strategy": "SENS evaluator / deep-copy control",
                    "width_bits": 196608,
                    "retained_values": 128,
                    "samples_kib": [43000, 43200, 43100],
                },
            ],
            repetitions=3,
        )

        self.assertIn("| SENS evaluator / shared clone | 21,100 | 21,000, 21,200, 21,100 |", report)
        self.assertIn("| SENS evaluator / deep-copy control | 43,100 | 43,000, 43,200, 43,100 |", report)
        self.assertIn("196,608", report)
        self.assertIn("128", report)
        self.assertIn("контроль відтворює копіювання, а не старий бінарник", report)
        self.assertIn("не є міжмовним рейтингом", report)

    def test_numeric_commands_use_identical_width_and_retention_for_both_strategies(self):
        commands = memory.numeric_memory_commands(
            Path("/tmp/sens_numeric_memory_bench"),
            width_bits=196608,
            retained_values=128,
        )

        self.assertEqual([label for label, _ in commands], [
            "SENS evaluator / shared clone",
            "SENS evaluator / deep-copy control",
        ])
        self.assertEqual(
            [command[1:] for _, command in commands],
            [["shared", "196608", "128"], ["deep-copy", "196608", "128"]],
        )

    def test_numeric_report_rejects_mismatched_workloads(self):
        rows = [
            {
                "strategy": "SENS evaluator / shared clone",
                "width_bits": 24,
                "retained_values": 3,
                "samples_kib": [100, 101, 102],
            },
            {
                "strategy": "SENS evaluator / deep-copy control",
                "width_bits": 48,
                "retained_values": 3,
                "samples_kib": [100, 110, 120],
            },
        ]

        with self.assertRaisesRegex(ValueError, "same width and retained count"):
            memory.render_numeric_report(rows, repetitions=3)


if __name__ == "__main__":
    unittest.main()
