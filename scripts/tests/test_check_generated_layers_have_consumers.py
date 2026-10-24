"""Шари *_generated.rs: кожен або спожитий, або оголошений даними."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check-generated-layers-have-consumers.py"


class GeneratedLayerTests(unittest.TestCase):
    def run_script(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args],
                              capture_output=True, text=True, timeout=60, check=False)

    def test_no_new_orphan_layers(self):
        r = self.run_script("--check")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("PASS", r.stdout)
        self.assertIn("борг=1", r.stdout)

    def test_the_one_named_debt_is_numeric_domains(self):
        # Єдиний справжній сирота — той самий файл, що ніс закон D12.
        r = self.run_script()
        debt = [l for l in r.stdout.splitlines() if "БОРГ" in l]
        self.assertEqual(len(debt), 1, r.stdout)
        self.assertIn("numeric_domains_generated", debt[0])

    def test_include_based_consumers_are_recognised(self):
        # include! — не рідкість; хибно оголошувати ці шари сиротами.
        r = self.run_script()
        for stem in ("function_signatures_generated", "d10_definition_bindings_generated",
                     "semantic_registry_generated"):
            self.assertIn(stem, r.stdout)
            self.assertNotIn(f"{stem}: БОРГ", r.stdout)


if __name__ == "__main__":
    unittest.main()
