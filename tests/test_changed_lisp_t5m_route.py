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

    def test_w24_is_executed_only_from_a_verified_physical_pair(self):
        # Структурний свідок маршруту; реальне SENS-eval перевіряє Rust CLI.
        source = RUNNER.read_text(encoding="utf-8")
        physical = source.index('if timeout 45s "$binary" "$pair"')
        marker = source.index("T5M_STANDALONE_D24_NOT_SUPPORTED", physical)
        paired_runtime = source.index('timeout 45s "$binary" --t5m-pair "$file" "$pair"', marker)
        paired_pass = source.index("T5M_PHYSICAL_PAIRED_D24_PASS", paired_runtime)
        paired_fail = source.index("T5M_PHYSICAL_PAIRED_D24_FAIL", paired_pass)
        self.assertLess(physical, marker)
        self.assertLess(marker, paired_runtime)
        self.assertLess(paired_runtime, paired_pass)
        self.assertLess(paired_pass, paired_fail)
        branch = source[marker:paired_fail]
        self.assertIn('Фізичне T5M-декодування зберегло точні ширини слів', source)
        self.assertIn('адаптер BinarySourceWord приймає лише W1–W9', source)
        # Новий SENS більше не зобов'язаний друкувати текст старого
        # адаптера W1–W9. На обидва точні D24 повідомлення спробуємо
        # реально парний Zig/SENS-вхід, не видаючи саму спробу за PASS.
        self.assertIn('T5M requires exact source projection to D24+ before transport', source)
        self.assertIn('physical=ZIG_VERIFIED', branch)
        self.assertIn('semantic=NOT_CERTIFIED', branch)
        self.assertIn('release=NOT_CERTIFIED', branch)
        self.assertNotIn('--t5m-file "$file"', branch)
        self.assertNotIn('T5M_FILE_EXECUTION PASS', branch)
        self.assertIn('failed_files=$((failed_files + 1))', source[paired_fail:])

    def test_text7_binding_needs_real_paired_execution_and_stays_red_on_failure(self):
        # Це тест оркестрації Bash, не Python-емуляція семантики SENS.
        # Сам точний транспорт, reader і eval виконує лише виклик "$binary".
        source = RUNNER.read_text(encoding="utf-8")
        marker = source.index("T5M_STANDALONE_D7_NEEDS_SOURCE_AUTHORITY")
        before = source.rfind("if grep -Fq 'unknown Text7 binding:'", 0, marker)
        paired = source.index('timeout 45s "$binary" --t5m-pair "$file" "$pair"', marker)
        passed = source.index("T5M_PHYSICAL_PAIRED_D7_PASS", paired)
        failed = source.index("T5M_PHYSICAL_PAIRED_D7_FAIL", passed)
        self.assertGreaterEqual(before, 0)
        self.assertLess(before, marker)
        self.assertLess(marker, paired)
        self.assertLess(paired, passed)
        self.assertLess(passed, failed)
        branch = source[paired:failed]
        self.assertIn("physical=ZIG_VERIFIED", branch)
        self.assertIn("semantic=NOT_CERTIFIED", branch)
        self.assertIn("release=NOT_CERTIFIED", branch)
        self.assertIn("status=$?", branch)
        # Прозора відмова не перетворюється на успіх і не глушить RED.
        self.assertIn('failed_files=$((failed_files + 1))', source[failed:failed+160])
        self.assertIn('if (( failed_files > 0 )); then\\n  exit 2', source)

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
            # Осиротілий extensionless перегляд теж належить видалити:
            # DATA не перетворюється на колишній executable через старий артефакт.
            (root / "module").write_text("stale bits\\n", encoding="utf-8")
            orphan = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertEqual(orphan.returncode, 2, orphan.stdout + orphan.stderr)
            self.assertIn("T5M_NONPROGRAM_STALE_PAIR", orphan.stderr)
            self.assertIn("view=./module", orphan.stderr)
            self.assertFalse((root / "executed.marker").exists())
            (root / "module").unlink()
            cleaned = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertEqual(cleaned.returncode, 0, cleaned.stdout + cleaned.stderr)
            self.assertIn("T5M_NOT_PROGRAM path=module.lisp", cleaned.stdout)
            self.assertFalse((root / "executed.marker").exists())

    def test_committed_physical_pair_must_be_regular_not_symlink_or_directory(self):
        # Перевіряємо лише shell-межу перевірки пар, не Python-SENS
        # evaluator. Обидва шкідливі об'єкти відхиляються до runtime.
        with tempfile.TemporaryDirectory(prefix="sens-t5m-nonregular-pair-") as td:
            root = Path(td)
            (root / "scripts").mkdir()
            (root / "module.lisp").write_text("(як-є ())\n", encoding="utf-8")
            (root / "changed.txt").write_text("module.lisp\n", encoding="utf-8")
            (root / "module").write_text("10 001 00 000 01\n", encoding="utf-8")
            (root / "real.sens").write_bytes(b"synthetic-pair")
            migrator = root / "scripts/migrate-three-pass.py"
            migrator.write_text(
                "import json, pathlib, sys\n"
                "source = pathlib.Path(sys.argv[1])\n"
                "out = pathlib.Path(sys.argv[sys.argv.index('--out') + 1])\n"
                "report = pathlib.Path(sys.argv[sys.argv.index('--report') + 1])\n"
                "out.mkdir(parents=True, exist_ok=True)\n"
                "(out / (source.stem + '.sens')).write_bytes(b'synthetic-pair')\n"
                "(out / source.stem).write_text('10 001 00 000 01\\n')\n"
                "report.write_text(json.dumps({'summary': {'files_written': 1, "
                "'files_blocked': 0, 'files_not_program': 0}, 'files': []}))\n",
                encoding="utf-8",
            )
            binary = root / "must-not-run-sens"
            binary.write_text(
                "#!/bin/sh\nprintf invoked > executed.marker\nexit 0\n",
                encoding="utf-8",
            )
            binary.chmod(0o755)
            command = ["bash", str(RUNNER), str(binary), "changed.txt", "evidence"]
            committed = root / "module.sens"
            for fixture in ("symlink", "directory"):
                with self.subTest(fixture=fixture):
                    if fixture == "symlink":
                        committed.symlink_to(root / "real.sens")
                    else:
                        committed.mkdir()
                    result = subprocess.run(
                        command, cwd=root, capture_output=True, text=True,
                        timeout=20,
                    )
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn("T5M_COMMITTED_PAIR_NOT_REGULAR", result.stderr)
                    self.assertIn("files_failed=1", result.stdout)
                    self.assertFalse((root / "executed.marker").exists())
                    if fixture == "symlink":
                        committed.unlink()
                    else:
                        committed.rmdir()

    def test_stale_regular_companion_still_executes_fresh_physical_t5m(self):
        # Це лише тест маршрутизації: stub тут не виконує семантику SENS.
        # Старий фізичний супутник лишає RED, але свіжий Zig-кандидат
        # усе одно доходить до реального SENS-входу в production script.
        with tempfile.TemporaryDirectory(prefix="sens-t5m-stale-live-") as td:
            root = Path(td)
            (root / "scripts").mkdir()
            (root / "module.lisp").write_text("(як-є ())\n", encoding="utf-8")
            (root / "changed.txt").write_text("module.lisp\n", encoding="utf-8")
            (root / "scripts/migrate-three-pass.py").write_text(
                "import json, pathlib, sys\n"
                "source = pathlib.Path(sys.argv[1])\n"
                "out = pathlib.Path(sys.argv[sys.argv.index('--out') + 1])\n"
                "report = pathlib.Path(sys.argv[sys.argv.index('--report') + 1])\n"
                "out.mkdir(parents=True, exist_ok=True)\n"
                "(out / (source.stem + '.sens')).write_bytes(b'\\x01')\n"
                "(out / source.stem).write_text('10 001 00 000 01\\n')\n"
                "report.write_text(json.dumps({'summary': {'files_written': 1, "
                "'files_blocked': 0, 'files_not_program': 0}, 'files': []}))\n",
                encoding="utf-8",
            )
            binary = root / "record-physical-ingress"
            binary.write_text(
                "#!/bin/sh\nprintf '%s\\n' \"$1\" >> executed.marker\n"
                "printf 'transport stub only\\n'\n",
                encoding="utf-8",
            )
            binary.chmod(0o755)
            pair = root / "module.sens"
            view = root / "module"
            for kind, expected_error in [
                ("pair", "T5M_COMMITTED_PAIR_DRIFT"),
                ("view", "T5M_COMMITTED_VIEW_DRIFT"),
                ("missing-view", "T5M_COMMITTED_VIEW_MISSING"),
            ]:
                with self.subTest(kind=kind):
                    pair.write_bytes(b"\x02" if kind == "pair" else b"\x01")
                    if kind == "missing-view":
                        view.unlink(missing_ok=True)
                    else:
                        view.write_text(
                            "застарілий перегляд\n" if kind == "view"
                            else "10 001 00 000 01\n", encoding="utf-8",
                        )
                    (root / "executed.marker").unlink(missing_ok=True)
                    result = subprocess.run(
                        ["bash", str(RUNNER), str(binary), "changed.txt", "evidence"],
                        cwd=root, capture_output=True, text=True, timeout=20,
                    )
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn(expected_error, result.stderr)
                    self.assertIn("T5M_FILE_EXECUTION PASS", result.stdout)
                    self.assertIn("release=NOT_CERTIFIED", result.stdout)
                    self.assertIn("module.sens", (root / "executed.marker").read_text())
                    self.assertNotIn("--t5m-file", (root / "executed.marker").read_text())

            # .sens немає, але перегляд залишився: відмова без пропуску
            # виконання нової фізичної Zig-пари через production runner.
            pair.unlink()
            view.write_text("осиротілі біти\\n", encoding="utf-8")
            (root / "executed.marker").unlink(missing_ok=True)
            result = subprocess.run(
                ["bash", str(RUNNER), str(binary), "changed.txt", "evidence"],
                cwd=root, capture_output=True, text=True, timeout=20,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("T5M_ORPHAN_VIEW", result.stderr)
            self.assertIn("files_failed=1", result.stdout)
            self.assertIn("T5M_FILE_EXECUTION PASS", result.stdout)
            self.assertIn("module.sens", (root / "executed.marker").read_text())

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
