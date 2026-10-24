"""Guard-скрипти: кожен мусить мати запускача, або бути названим боргом."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check-guards-have-runners.py"


class GuardRunnerTests(unittest.TestCase):
    def run_script(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args],
                              capture_output=True, text=True, timeout=120, check=False)

    def test_no_new_orphan_guards(self):
        r = self.run_script("--check")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("PASS", r.stdout)

    def test_the_d6_and_d10_generators_are_now_wired(self):
        # Було: D5/D9 у CI, а D6/D10 — борг. Тепер D6/D10 підключено
        # (ci-hosted.yml:70-71), тож сиротами вони бути НЕ можуть.
        r = self.run_script()
        for name in ("check-d6-definition-bindings.py", "check-d10-definition-bindings.py"):
            self.assertNotIn(f"{name}: НІХТО не запускає", r.stdout)

    def test_release_gate_is_not_an_orphan(self):
        # Реліз-гейт виглядав сиротою, але його ЗАПУСКАЮТЬ тести
        # (tests/test_check_release_admission_ledger.py:18 будує шлях як
        # ROOT / "scripts" / "..."). Матч мусить бачити цю форму.
        r = self.run_script()
        for name in ("check-release-admission-ledger.py", "check-required-checks.py"):
            self.assertNotIn(f"{name}: НІХТО не запускає", r.stdout)

    def test_wired_guards_are_not_reported(self):
        # D5/D9 мають запускача (workflow) — не можуть бути в боргу.
        r = self.run_script()
        for name in ("check-d5-definition-bindings.py", "check-d9-definition-bindings.py"):
            self.assertNotIn(f"{name}: НІХТО не запускає", r.stdout)


if __name__ == "__main__":
    unittest.main()
