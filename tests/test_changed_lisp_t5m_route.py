"""Перевірка CI-маршруту: Lisp — текст, фізичний .sens виконується через окремий SENS-вхід.

Статична перевірка контракту без Python-імітації SENS-eval.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/execute_changed_lisp_t5m.sh"
CI = ROOT / ".github/workflows/ci.yml"

class ChangedLispT5MRouteTests(unittest.TestCase):
    def test_mint_before_execution(self):
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn('scripts/migrate-three-pass.py "$file"', source)
        self.assertIn('--codec t5m --source-surface укр', source)
        self.assertIn('"$binary" "$pair"', source)
        self.assertNotIn('--t5m-file "$pair"', source)
        self.assertLess(source.index('scripts/migrate-three-pass.py'),
                        source.index('"$binary" "$pair"'))

    def test_fail_closed_without_false_release_success(self):
        source = RUNNER.read_text(encoding="utf-8")
        for receipt in ("T5M_MIGRATION_NO_REPORT", "T5M_MIGRATION_INTERNAL_FAILURE",
                        "T5M_COMMITTED_PAIR_DRIFT", "T5M_FILE_EXECUTION_FAIL",
                        "T5M_MIGRATION_UNPROVEN", "semantic=NOT_CERTIFIED"):
            with self.subTest(receipt=receipt):
                self.assertIn(receipt, source)

    def test_ci_uses_one_binary_transport_route(self):
        source = CI.read_text(encoding="utf-8")
        self.assertNotIn('--t5m-file "$file"', source)
        self.assertIn('bash scripts/execute_changed_lisp_t5m.sh', source)
        self.assertIn('python3 -m unittest tests/test_changed_lisp_t5m_route.py -v', source)

    def test_ci_step_name_with_colon_is_yaml_quoted(self):
        source = CI.read_text(encoding="utf-8")
        self.assertIn(
            '- name: "Контроль T5M CLI: позитивна й негативні фізичні межі"',
            source,
        )

if __name__ == "__main__":
    unittest.main()
