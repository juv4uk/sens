"""Перевірка CI-маршруту: Lisp — текст, фізичний .sens виконується через окремий SENS-вхід.

Статична перевірка контракту без Python-імітації SENS-eval.
"""
from pathlib import Path
import unittest
import subprocess
import tempfile
import os
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/execute_changed_lisp_t5m.sh"
CI = ROOT / ".github/workflows/ci.yml"

class ChangedLispT5MRouteTests(unittest.TestCase):
    def setUp(self):
        # Історичні fixtures нижче перевіряють тільки явний preview,
        # а не типовий native SENS/T5M. Повертаємо env після тесту.
        legacy = patch.dict(os.environ, {"SENS_NATIVE_T5M": "0"})
        legacy.start()
        self.addCleanup(legacy.stop)

    def test_default_path_requires_no_python_or_json(self):
        script = RUNNER.read_text(encoding="utf-8")
        self.assertEqual(script.count('${SENS_NATIVE_T5M:-1}'), 2)
        self.assertLess(script.index('run_native_t5m_program'),
                        script.index('python3 scripts/migrate-three-pass.py'))

    def test_invalid_mode_cannot_fall_back_to_python_or_json(self):
        # Помилка змінної середовища — реальна відмова ДО будь-якого
        # запуску виконавця; вона не обирає історичний Python-проєктор.
        with tempfile.TemporaryDirectory(prefix="sens-mode-fail-closed-") as td:
            root = Path(td)
            (root / "one.lisp").write_text("(як-є ())\n", encoding="utf-8")
            (root / "changed.txt").write_text("one.lisp\n", encoding="utf-8")
            binary = root / "sens-fake"
            binary.write_text(
                "#!/bin/sh\nprintf called > invoked\n", encoding="utf-8"
            )
            binary.chmod(0o755)
            env = dict(os.environ, SENS_NATIVE_T5M="python-by-accident")
            result = subprocess.run(
                ["bash", str(RUNNER), str(binary), "changed.txt", "evidence"],
                cwd=root, env=env, capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("SENS_NATIVE_T5M_INVALID", result.stderr)
            self.assertFalse((root / "invoked").exists())
            self.assertFalse(list((root / "evidence").rglob("*.sens")))

    def test_native_route_without_python_or_json_and_true_red_propagation(self):
        # Це тест ТІЛЬКИ shell-оркестрації. Семантику виконує CI через
        # реальний sens --t5m-pair, а не цей замінник командного інтерфейсу.
        import os
        ci = CI.read_text(encoding="utf-8")
        self.assertIn("SENS_NATIVE_T5M=1", ci)
        self.assertIn("cargo build --locked -p sens-cli --bin sens --bin sens-trit", ci)
        with tempfile.TemporaryDirectory(prefix="sens-native-t5m-shell-") as td:
            root = Path(td)
            (root / "module.lisp").write_text("(як-є ())\n", encoding="utf-8")
            (root / "changed.txt").write_text("module.lisp\n", encoding="utf-8")
            binary = root / "sens-entry"
            binary.write_text(
                "#!/bin/sh\n"
                "if [ \"$1\" = --t5m-mint ]; then printf 'physical' > \"$3\"; exit 0; fi\n"
                "if [ \"$1\" = --t5m-pair ] && [ -f reject-pair ]; then\n"
                "  echo 'real paired failure' >&2; exit 19; fi\n"
                "if [ -f reject-standalone ] && [ \"$1\" != --t5m-pair ]; then\n"
                "  echo 'unexpected standalone panic' >&2; exit 23; fi\n"
                "if [ -f reject-d24 ] && [ \"$1\" != --t5m-pair ]; then\n"
                "  echo 'T5M requires exact source projection to D24+ before transport' >&2; exit 3; fi\n"
                "printf 'SENS_RESULT\\n'\n",
                encoding="utf-8",
            )
            binary.chmod(0o755)
            opener = root / "sens-trit"
            opener.write_text(
                "#!/bin/sh\n"
                "if [ \"$1\" = verify-view ] && [ -f reject-view ]; then\n"
                "  echo 'noncanonical view' >&2; exit 31; fi\n"
                "printf '10 001 01\\n'\n", encoding="utf-8")
            opener.chmod(0o755)
            environment = dict(os.environ, SENS_NATIVE_T5M="1",
                               SENS_T5M_OPEN=str(opener))
            cmd = ["bash", str(RUNNER), str(binary), "changed.txt", "evidence"]
            ok = subprocess.run(cmd, cwd=root, env=environment,
                                capture_output=True, text=True, timeout=20)
            self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
            self.assertIn("T5M_NATIVE_STANDALONE_AND_PAIRED_PASS", ok.stdout)
            self.assertIn("native_view_roundtrip=1 native_paired_executed=1 native_standalone_parity=1", ok.stdout)
            self.assertIn("scope=changed_manifest semantic=NOT_CERTIFIED", ok.stdout)
            # При невстановленому SENS_NATIVE_T5M справжнім типовим шляхом
            # лишається той самий native SENS, без виклику Python/JSON.
            default_env = dict(environment)
            default_env.pop("SENS_NATIVE_T5M", None)
            default = subprocess.run(cmd, cwd=root, env=default_env,
                                     capture_output=True, text=True, timeout=20)
            self.assertEqual(default.returncode, 0, default.stdout + default.stderr)
            self.assertIn("T5M_NATIVE_STANDALONE_AND_PAIRED_PASS", default.stdout)
            self.assertNotIn("T5M_MIGRATION_NO_REPORT", default.stderr)
            self.assertNotIn("T5M_MIGRATION_NO_REPORT", ok.stderr)
            self.assertTrue(list((root / "evidence").glob("*/module.sens")))
            (root / "reject-view").touch()
            invalid_inverse = subprocess.run(
                cmd, cwd=root, env=environment, capture_output=True,
                text=True, timeout=20,
            )
            self.assertEqual(invalid_inverse.returncode, 2,
                             invalid_inverse.stdout + invalid_inverse.stderr)
            self.assertIn("T5M_NATIVE_VIEW_ROUNDTRIP_FAILED", invalid_inverse.stderr)
            self.assertIn("native_view_roundtrip=0 native_paired_executed=0 native_standalone_parity=0", invalid_inverse.stdout)
            self.assertIn("files_checked=1 files_failed=1", invalid_inverse.stdout)
            (root / "reject-view").unlink()
            (root / "reject-pair").touch()
            red = subprocess.run(cmd, cwd=root, env=environment,
                                 capture_output=True, text=True, timeout=20)
            self.assertEqual(red.returncode, 2, red.stdout + red.stderr)
            self.assertIn("T5M_NATIVE_PAIRED_EXECUTION_FAIL", red.stderr)
            self.assertIn("native_view_roundtrip=1 native_paired_executed=0 native_standalone_parity=0", red.stdout)
            self.assertIn("files_checked=1 files_failed=1", red.stdout)
            self.assertNotIn("T5M_NATIVE_STANDALONE_AND_PAIRED_PASS", red.stdout)
            # Лише Bash-контрольний потік: не Python-оракул семантики.
            (root / "reject-pair").unlink()
            (root / "reject-standalone").touch()
            unexpected = subprocess.run(cmd, cwd=root, env=environment,
                                        capture_output=True, text=True, timeout=20)
            self.assertEqual(unexpected.returncode, 2, unexpected.stdout + unexpected.stderr)
            self.assertIn("T5M_NATIVE_STANDALONE_UNEXPECTED_FAIL", unexpected.stderr)
            self.assertIn("native_view_roundtrip=1 native_paired_executed=1 native_standalone_parity=0", unexpected.stdout)
            self.assertIn("files_checked=1 files_failed=1", unexpected.stdout)
            self.assertNotIn("T5M_NATIVE_PAIRED_ONLY", unexpected.stdout)

            (root / "reject-standalone").unlink()
            (root / "reject-d24").touch()
            d24 = subprocess.run(cmd, cwd=root, env=environment,
                                 capture_output=True, text=True, timeout=20)
            self.assertEqual(d24.returncode, 0, d24.stdout + d24.stderr)
            self.assertIn("T5M_NATIVE_PAIRED_ONLY", d24.stdout)
            self.assertIn("native_view_roundtrip=1 native_paired_executed=1 native_standalone_parity=0", d24.stdout)
            self.assertIn("release=NOT_CERTIFIED", d24.stdout)

    def test_native_sens_mint_is_primary_ci_path_and_python_is_optional_tooling(self):
        source = RUNNER.read_text(encoding="utf-8")
        ci = CI.read_text(encoding="utf-8")
        self.assertIn('SENS_NATIVE_T5M=1 SENS_T5M_OPEN=', ci)
        self.assertIn('run_native_t5m_program', source)
        self.assertIn('mint_flag=--t5m-mint', source)
        self.assertIn('mint_flag=--t5m-mint-pair', source)
        self.assertIn('"$binary" "$mint_flag" "$file" "$physical" "${binding_sources[@]}"', source)
        self.assertIn('"$binary" --t5m-pair "$file" "$physical" "${binding_sources[@]}"', source)
        self.assertLess(source.index('  binding_sources=()'),
                        source.index('    run_native_t5m_program\n    continue'))
        self.assertIn('"$native_open" open "$physical"', source)
        self.assertIn('"$native_open" verify-view "$physical"', source)
        # Опційний Python-мігратор не може передувати SENS у робочому CI.
        self.assertLess(source.index('    run_native_t5m_program\n    continue'),
                        source.index('scripts/migrate-three-pass.py'))
        self.assertNotIn('--t5m-file "$pair"', source)

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
                self.assertIn('mark_file_failed', arm)
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
        self.assertIn('mark_file_failed', source[paired_fail:])

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
        self.assertIn('mark_file_failed', source[failed:failed+160])
        self.assertIn('if (( failed_files > 0 )); then\n  exit 2', source)

    def test_new_standalone_diagnostic_still_tries_real_zig_pair_without_false_pass(self):
        # Лише маршрут Bash. Семантику засвідчує реальний SENS CLI у CI.
        source = RUNNER.read_text(encoding="utf-8")
        standalone = source.index('if timeout 45s "$binary" "$pair"')
        old_d7 = source.index("T5M_PHYSICAL_PAIRED_D7_FAIL", standalone)
        generic = source.index("T5M_STANDALONE_UNCLASSIFIED_FAILURE", old_d7)
        paired = source.rfind(
            'timeout 45s "$binary" --t5m-pair "$file" "$pair"',
            old_d7, generic,
        )
        self.assertGreater(paired, old_d7)
        self.assertLess(paired, generic)
        branch = source[paired:source.index("T5M_FILE_EXECUTION_FAIL", generic)]
        self.assertIn('standalone_status=$status', source[old_d7:generic])
        self.assertIn('cp "$stderr" "$dir/standalone.stderr"', source[old_d7:generic])
        self.assertIn("physical=ZIG_VERIFIED", branch)
        self.assertIn("semantic=NOT_CERTIFIED", branch)
        self.assertIn("release=NOT_CERTIFIED", branch)
        self.assertIn("standalone_status=$standalone_status paired_status=0", branch)
        self.assertIn("mark_file_failed", branch)
        self.assertNotIn("T5M_PHYSICAL_PAIRED_GENERIC_PASS", source)
        self.assertIn("paired_status=$status", source[generic:])
        self.assertIn("mark_file_failed", source[generic:])
        self.assertNotIn("T5M_FILE_EXECUTION PASS", branch)

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

    def test_nonprogram_report_cannot_hide_migrator_failure(self):
        # Тестуємо лише fail-closed Bash-маршрут, не симулюємо SENS-eval.
        with tempfile.TemporaryDirectory(prefix="sens-t5m-nonprogram-exit-") as td:
            root = Path(td)
            (root / "scripts").mkdir()
            (root / "module.lisp").write_text("; коментар як дані\n", encoding="utf-8")
            (root / "changed.txt").write_text("module.lisp\n", encoding="utf-8")
            (root / "scripts/migrate-three-pass.py").write_text(
                "import json, pathlib, sys\n"
                "report = pathlib.Path(sys.argv[sys.argv.index('--report') + 1])\n"
                "report.write_text(json.dumps({'summary': {'files_written': 0, "
                "'files_blocked': 0, 'files_not_program': 1}, 'files': []}))\n"
                "raise SystemExit(1)\n",
                encoding="utf-8",
            )
            binary = root / "must-not-run-sens"
            binary.write_text("#!/bin/sh\nprintf invoked > executed.marker\nexit 0\n", encoding="utf-8")
            binary.chmod(0o755)
            result = subprocess.run(
                ["bash", str(RUNNER), str(binary), "changed.txt", "evidence"],
                cwd=root, capture_output=True, text=True, timeout=20,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("T5M_MIGRATION_FAILED", result.stderr)
            self.assertIn("status=1", result.stderr)
            self.assertIn("files_checked=1 files_failed=1", result.stdout)
            self.assertFalse((root / "executed.marker").exists())

    def test_one_source_cannot_claim_both_program_and_data(self):
        # Лише контроль класифікації оркестратора, не Python-обчислювач SENS.
        with tempfile.TemporaryDirectory(prefix="sens-t5m-report-counts-") as td:
            root = Path(td)
            (root / "scripts").mkdir()
            (root / "module.lisp").write_text("(як-є ())\n", encoding="utf-8")
            (root / "changed.txt").write_text("module.lisp\n", encoding="utf-8")
            (root / "scripts/migrate-three-pass.py").write_text(
                "import json, pathlib, sys\n"
                "report = pathlib.Path(sys.argv[sys.argv.index('--report') + 1])\n"
                "report.write_text(json.dumps({'summary': {'files_written': 1, "
                "'files_blocked': 0, 'files_not_program': 1}, 'files': []}))\n",
                encoding="utf-8",
            )
            binary = root / "must-not-run-sens"
            binary.write_text("#!/bin/sh\nprintf invoked > executed.marker\nexit 0\n",
                              encoding="utf-8")
            binary.chmod(0o755)
            result = subprocess.run(
                ["bash", str(RUNNER), str(binary), "changed.txt", "evidence"],
                cwd=root, capture_output=True, text=True, timeout=20,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("T5M_MIGRATION_REPORT_COUNTS_INVALID", result.stderr)
            self.assertIn("written=1 blocked=0 not_program=1", result.stderr)
            self.assertIn("files_checked=1 files_failed=1", result.stdout)
            self.assertFalse((root / "executed.marker").exists())

    def test_invalid_json_counters_never_become_bash_success(self):
        # Суто перевірка звіту мігратора, без Python-емуляції SENS.
        with tempfile.TemporaryDirectory(prefix="sens-t5m-invalid-counters-") as td:
            root = Path(td)
            (root / "scripts").mkdir()
            (root / "module.lisp").write_text("(як-є ())\n", encoding="utf-8")
            (root / "changed.txt").write_text("module.lisp\n", encoding="utf-8")
            binary = root / "must-not-run-sens"
            binary.write_text("#!/bin/sh\nprintf invoked > executed.marker\nexit 0\n",
                              encoding="utf-8")
            binary.chmod(0o755)
            for name, counters in (
                ("negative", {"files_written": 1, "files_blocked": -1,
                              "files_not_program": 1}),
                ("boolean", {"files_written": True, "files_blocked": 0,
                             "files_not_program": 0}),
                ("fraction", {"files_written": 1.0, "files_blocked": 0,
                              "files_not_program": 0}),
            ):
                with self.subTest(name=name):
                    (root / "scripts/migrate-three-pass.py").write_text(
                        "import json, pathlib, sys\n"
                        "report = pathlib.Path(sys.argv[sys.argv.index('--report') + 1])\n"
                        "report.write_text(json.dumps({'summary': " +
                        repr(counters) + ", 'files': []}))\n",
                        encoding="utf-8",
                    )
                    (root / "executed.marker").unlink(missing_ok=True)
                    result = subprocess.run(
                        ["bash", str(RUNNER), str(binary), "changed.txt", "evidence"],
                        cwd=root, capture_output=True, text=True, timeout=20,
                    )
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn("T5M_MIGRATION_REPORT_INVALID", result.stderr)
                    self.assertIn("files_checked=1 files_failed=1", result.stdout)
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
                ("pair-and-view", "T5M_COMMITTED_PAIR_DRIFT"),
            ]:
                with self.subTest(kind=kind):
                    pair.write_bytes(b"\x02" if kind in ("pair", "pair-and-view") else b"\x01")
                    if kind == "missing-view":
                        view.unlink(missing_ok=True)
                    else:
                        view.write_text(
                            "застарілий перегляд\n" if kind in ("view", "pair-and-view")
                            else "10 001 00 000 01\n", encoding="utf-8",
                        )
                    (root / "executed.marker").unlink(missing_ok=True)
                    result = subprocess.run(
                        ["bash", str(RUNNER), str(binary), "changed.txt", "evidence"],
                        cwd=root, capture_output=True, text=True, timeout=20,
                    )
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn(expected_error, result.stderr)
                    if kind == "pair-and-view":
                        self.assertIn("T5M_COMMITTED_VIEW_DRIFT", result.stderr)
                    # У файлі може бути два дефекти; files_failed рахує
                    # джерела, а не кількість надрукованих помилок.
                    self.assertIn("files_checked=1 files_failed=1", result.stdout)
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


    def test_standalone_pass_requires_real_paired_invocation(self):
        # Тільки контроль маршруту Bash: stub фіксує виклики, не виконує SENS.
        # У production обидва входи викликають справжній бінарник.
        with tempfile.TemporaryDirectory(prefix="sens-t5m-paired-pass-") as td:
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
            binary = root / "record-sens-ingress"
            binary.write_text(
                "#!/bin/sh\nprintf '%s\\n' \"$*\" >> invoked.marker\n"
                "if [ \"$1\" = --t5m-mint ]; then\n"
                "  if [ -e fail-paired ]; then printf '\\002' > \"$3\";\n"
                "  else printf '\\001' > \"$3\"; fi\n  exit 0\nfi\n"
                "if [ \"$1\" = --t5m-pair ] && [ -e fail-paired ]; then\n"
                "  case \"$3\" in *sens-authority.sens) printf 'stub transport only\\n'; exit 0;; esac\n"
                "  echo T5M_PHYSICAL_PAIR_MISMATCH >&2\n  exit 19\nfi\n"
                "if [ \"$1\" = --t5m-pair ] && [ -e alter-paired ]; then\n"
                "  printf 'different paired result\\n'\n  exit 0\nfi\n"
                "printf 'stub transport only\\n'\n",
                encoding="utf-8",
            )
            binary.chmod(0o755)
            cmd = ["bash", str(RUNNER), str(binary), "changed.txt", "evidence"]
            # Успіх обох входів потрібен навіть коли прямий .sens уже виконався.
            passed = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=20)
            self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)
            self.assertIn("T5M_FILE_EXECUTION PASS", passed.stdout)
            self.assertIn("physical=ZIG_VERIFIED", passed.stdout)
            calls = (root / "invoked.marker").read_text(encoding="utf-8")
            self.assertIn("--t5m-pair module.lisp", calls)
            self.assertIn("module.sens", calls)
            # Невдале джерельне зіставлення не може успадкувати прямий PASS.
            (root / "fail-paired").touch()
            (root / "invoked.marker").unlink()
            failed = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=20)
            self.assertEqual(failed.returncode, 2, failed.stdout + failed.stderr)
            self.assertIn("T5M_PAIRED_SOURCE_EXECUTION_FAIL", failed.stderr)
            self.assertIn("T5M_INDEPENDENT_PROJECTION_DIVERGENCE", failed.stderr)
            self.assertIn("status=19", failed.stderr)
            self.assertIn("--t5m-mint module.lisp", (root / "invoked.marker").read_text())
            self.assertTrue(any((root / "evidence").rglob("sens-authority.sens")))
            self.assertIn("files_checked=1 files_failed=1", failed.stdout)
            self.assertNotIn("T5M_FILE_EXECUTION PASS", failed.stdout)
            calls = (root / "invoked.marker").read_text(encoding="utf-8")
            self.assertIn("--t5m-pair module.lisp", calls)

            # Обидва SENS-входи можуть повернути exit=0, але різні результати.
            # Це є реальна розбіжність, а не підстава друкувати PASS.
            (root / "fail-paired").unlink()
            (root / "alter-paired").touch()
            (root / "invoked.marker").unlink()
            mismatch = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=20)
            self.assertEqual(mismatch.returncode, 2, mismatch.stdout + mismatch.stderr)
            self.assertIn("T5M_PAIRED_RESULT_MISMATCH", mismatch.stderr)
            self.assertIn("standalone_sha256=", mismatch.stderr)
            self.assertIn("paired_sha256=", mismatch.stderr)
            self.assertIn("files_checked=1 files_failed=1", mismatch.stdout)
            self.assertNotIn("T5M_FILE_EXECUTION PASS", mismatch.stdout)
            calls = (root / "invoked.marker").read_text(encoding="utf-8")
            self.assertIn("--t5m-pair module.lisp", calls)

    def test_export_catalog_is_verified_as_data_not_fake_executable_lisp(self):
        # Реальний cml-export виконує producer parity; schema-теги en/sa
        # не перетворюються на D7:укр викличні імена.
        ci = CI.read_text(encoding="utf-8")
        self.assertIn('not name.endswith(".lisp")', ci)
        self.assertIn("sens-cml-export[.]contract", ci)
        self.assertNotIn("mylisp-cml-export.lisp", ci)
        self.assertIn("cml_export_tests=true", ci)
        self.assertIn(
            "cargo test --locked -p sens-cli --bin cml-export "
            "committed_artifact_matches_producer_output", ci,
        )

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
