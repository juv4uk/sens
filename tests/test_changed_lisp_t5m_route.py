"""Перевірка CI-маршруту: Lisp — текст, фізичний .sens виконується через окремий SENS-вхід.

Статична перевірка контракту без Python-імітації SENS-eval.
"""
from pathlib import Path
import unittest
import subprocess
import tempfile

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

    def test_batch_reports_every_file_without_greenwashing(self):
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn('failed_files=0', source)
        self.assertIn('checked_files=$((checked_files + 1))', source)
        self.assertIn('T5M_CHANGED_SUMMARY files_checked=%s files_failed=%s', source)
        # Кожна адресна відмова має не обривати весь перелік.
        for receipt in ('T5M_CHANGED_SOURCE_INVALID', 'T5M_MIGRATION_NO_REPORT',
                        'T5M_MIGRATION_REPORT_INVALID', 'T5M_MIGRATION_UNPROVEN',
                        'T5M_COMMITTED_VIEW_DRIFT', 'T5M_FILE_EXECUTION_FAIL'):
            with self.subTest(receipt=receipt):
                arm = source.split('::error::' + receipt, 1)[1].split('continue', 1)[0]
                self.assertIn('failed_files=$((failed_files + 1))', arm)
        self.assertIn('if (( failed_files > 0 )); then\n  exit 2', source)

    def test_w24_uses_explicit_domain_source_runtime_without_fake_physical_pass(self):
        # Це контроль маршрутів, а не Python-обчислення Lisp.
        source = RUNNER.read_text(encoding="utf-8")
        physical = source.index('if timeout 45s "$binary" "$pair"')
        marker = source.index("T5M_PHYSICAL_D24_NOT_EXECUTED", physical)
        source_runtime = source.index('timeout 45s "$binary" --t5m-file "$file"', marker)
        source_pass = source.index("T5M_DOMAIN_SOURCE_RUNTIME_PASS", source_runtime)
        source_fail = source.index("T5M_DOMAIN_SOURCE_RUNTIME_FAIL", source_pass)
        self.assertLess(physical, marker)
        self.assertLess(marker, source_runtime)
        self.assertLess(source_runtime, source_pass)
        self.assertLess(source_pass, source_fail)
        branch = source[marker:source_fail]
        self.assertIn('точні ширини слів [24]', source)
        self.assertIn('адаптер BinarySourceWord приймає лише W1–W9', source)
        self.assertIn('physical=NOT_SUPPORTED', branch)
        self.assertIn('release=NOT_CERTIFIED', branch)
        self.assertNotIn('T5M_FILE_EXECUTION PASS', branch)
        self.assertIn('failed_files=$((failed_files + 1))', source[source_fail:])

    def test_nonprogram_cannot_hide_obsolete_committed_sens(self):
        # Перевірка самого Bash-маршруту на синтетичному звіті мігратора:
        # тут НЕ виконується і НЕ підмінюється обчислювач SENS.
        with tempfile.TemporaryDirectory(prefix="sens-t5m-stale-pair-") as td:
            root = Path(td)
            (root / "scripts").mkdir()
            (root / "module.lisp").write_text("; це більше не програма\n", encoding="utf-8")
            (root / "changed.txt").write_text("module.lisp\n", encoding="utf-8")
            (root / "module.sens").write_bytes(b"\x01")
            migrator = root / "scripts/migrate-three-pass.py"
            migrator.write_text(
                "import json, pathlib, sys\n"
                "out = pathlib.Path(sys.argv[sys.argv.index('--report') + 1])\n"
                "out.parent.mkdir(parents=True, exist_ok=True)\n"
                "out.write_text(json.dumps({'summary': {'files_written': 0, "
                "'files_blocked': 0, 'files_not_program': 1}, 'files': []}))\n",
                encoding="utf-8",
            )
            binary = root / "never-call-sens"
            binary.write_text(
                "#!/bin/sh\necho invoked > executed.marker\nexit 99\n",
                encoding="utf-8",
            )
            binary.chmod(0o755)
            command = [
                "bash", str(RUNNER), str(binary), "changed.txt", "evidence",
            ]
            stale = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertEqual(stale.returncode, 2, stale.stdout + stale.stderr)
            self.assertIn("T5M_NONPROGRAM_STALE_PAIR", stale.stderr)
            self.assertIn("module.sens", stale.stderr)
            self.assertFalse((root / "executed.marker").exists())
            # Після справжнього вилучення застарілого фізичного носія
            # дані лишаються даними: нема фальшивого виконання і RED.
            (root / "module.sens").unlink()
            cleaned = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertEqual(cleaned.returncode, 0, cleaned.stdout + cleaned.stderr)
            self.assertIn("T5M_NOT_PROGRAM path=module.lisp", cleaned.stdout)
            self.assertFalse((root / "executed.marker").exists())

    def test_shell_parses(self):
        import subprocess
        subprocess.run(['bash', '-n', str(RUNNER)], check=True)

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
