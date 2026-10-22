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


if __name__ == "__main__":
    unittest.main()
