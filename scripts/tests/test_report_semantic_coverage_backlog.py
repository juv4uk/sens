"""Стек семантичного боргу: вимір мусить бути точним і чесним."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "report-semantic-coverage-backlog.py"


class SemanticBacklogTests(unittest.TestCase):
    def run_script(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args],
                              capture_output=True, text=True, timeout=60, check=False)

    def test_backlog_is_measured_and_honest(self):
        r = self.run_script("--check")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("рядків=221", r.stdout)
        # Закон чесноти: жодного COVERED без нативної квитанції.
        self.assertIn("COVERED=0", r.stdout)
        self.assertIn("PASS", r.stdout)

    def test_no_false_receipts(self):
        r = self.run_script()
        self.assertIn("з квитанцією=0", r.stdout)

    def test_readiness_names_the_unmet_requirements(self):
        # 4 рядки з кандидатом; 2 мають .bits (треба .sens), 2 мають .sens але
        # без негатива. Звіт мусить назвати саме це, а не «готово».
        r = self.run_script("--ready")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("UNVERIFIED_NATIVE_PHYSICAL", r.stdout)   # .bits-кандидат (SHA-пришпилений)
        self.assertIn("NEEDS_NATIVE_RUN", r.stdout)             # потрібен запуск
        # Усі 4 рядки тепер мають негативний свідок — блокера немає.
        self.assertNotIn("MISSING_NEGATIVE_SENS", r.stdout)
        self.assertNotIn("готово ✓", r.stdout)

    def test_suggest_gives_hints_but_never_claims_a_match(self):
        # Дослівних збігів НЕМАЄ (перевірено), тож автозаповнення неможливе.
        # Режим дає ПІДКАЗКИ за перетином токенів — і мусить це казати.
        r = self.run_script("--suggest")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("ПІДКАЗКИ, не зіставлення", r.stdout)
        self.assertIn("d3-dotted-pair", r.stdout)   # конкретна підказка
        self.assertIn("~", r.stdout)

    def test_the_three_scopes_are_named(self):
        r = self.run_script()
        for scope in ("BULK_20261009", "EVAL_20261009", "TARGETED_20261009"):
            self.assertIn(scope, r.stdout)


if __name__ == "__main__":
    unittest.main()
