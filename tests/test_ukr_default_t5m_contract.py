#!/usr/bin/env python3
"""Чинний Lisp → точні слова T5M: типовий укр, тотожність без коментарів."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MIGRATOR = ROOT / "scripts/migrate-three-pass.py"


class UkrainianT5MDefaultContract(unittest.TestCase):
    def test_ci_never_treats_human_lisp_as_physical_t5m(self):
        # Структурний guard чинного шляху: .lisp -> Zig T5M -> фізичний
        # .sens -> справжній binary SENS. Це НЕ семантичний Python-оракул.
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        start = workflow.index(
            "      - name: Виконати змінені Lisp через поточний Zig T5M і справжній SENS"
        )
        end = workflow.index("      # Одноразове вимірювання T5M", start)
        execution = workflow[start:end]
        self.assertIn("bash scripts/execute_changed_lisp_t5m.sh", execution)
        self.assertIn('"$binary" "$RUNNER_TEMP/changed-t5m-lisp.txt"', execution)

        runner = (ROOT / "scripts/execute_changed_lisp_t5m.sh").read_text(
            encoding="utf-8"
        )
        # Нормативний шлях — SENS reader + Zig; Python є тільки
        # необов'язковим явно вибраним історичним preview.
        self.assertIn('case "${SENS_NATIVE_T5M:-1}" in', runner)
        self.assertIn('SENS_NATIVE_T5M_INVALID', runner)
        self.assertIn('run_native_t5m_program', runner)
        self.assertIn('if [[ "${SENS_NATIVE_T5M:-1}" == 1 ]]; then', runner)
        self.assertIn('mint_flag=--t5m-mint', runner)
        self.assertIn('mint_flag=--t5m-mint-pair', runner)
        self.assertIn('"$binary" "$mint_flag" "$file" "$physical" "${binding_sources[@]}"', runner)
        self.assertIn('"$native_open" open "$physical"', runner)
        self.assertIn('"$binary" --t5m-pair "$file" "$physical" "${binding_sources[@]}"', runner)
        self.assertLess(runner.index('  binding_sources=()'),
                        runner.index('    run_native_t5m_program\n    continue'))
        # Історичний режим не видалений, але він не є типовим входом.
        self.assertIn('python3 scripts/migrate-three-pass.py "$file"', runner)
        self.assertIn('--codec t5m --source-surface укр', runner)
        self.assertLess(runner.index('    run_native_t5m_program'),
                        runner.index('python3 scripts/migrate-three-pass.py'))
        self.assertIn('pair="$dir/$(basename "$file" .lisp).sens"', runner)
        # --t5m-file читає текстовий Lisp (read_to_string); для створеного
        # фізичного T5M слід викликати окремий .sens ingress, без цього прапорця.
        self.assertIn('if timeout 45s "$binary" "$pair"', runner)
        self.assertNotIn('--t5m-file "$pair"', runner)
        self.assertIn('T5M_COMMITTED_PAIR_DRIFT', runner)
        # Супутній двійковий перегляд звіряється з фізичною парою;
        # сам збіг .sens без перегляду не доводить повної трійки.
        self.assertIn('T5M_MINTED_VIEW_MISSING', runner)
        self.assertIn('T5M_COMMITTED_VIEW_MISSING', runner)
        self.assertIn('T5M_COMMITTED_VIEW_DRIFT', runner)
        self.assertIn('cmp -s "$staged_view" "$committed_view"', runner)
        self.assertIn('T5M_FILE_EXECUTION_FAIL', runner)
        cli = (ROOT / "crates/sens-cli/src/main.rs").read_text(encoding="utf-8")
        self.assertIn('fs::read_to_string(filename)', cli)
        self.assertIn('fs::read(filename)', cli)

    def test_native_binding_sources_load_lisp_dependencies_before_consumers(self):
        # SENS читає й виконує --binding-source у заданому порядку,
        # не через Python/JSON resolver. Зворотний порядок ламав
        # Reason до появи української DEFINE уніфікувати.
        runner = (ROOT / "scripts/execute_changed_lisp_t5m.sh").read_text(encoding="utf-8")
        expected = (
            'binding_sources=(--binding-source lib/unify.lisp --binding-source lib/reason.lisp)',
            'binding_sources=(--binding-source lib/unify.lisp\n'
            '                     --binding-source lib/knowledge.lisp\n'
            '                     --binding-source lib/reason.lisp)',
            'binding_sources=(--binding-source lib/unify.lisp\n'
            '                     --binding-source lib/knowledge.lisp\n'
            '                     --binding-source lib/reason.lisp\n'
            '                     --binding-source lib/world.lisp\n'
            '                     --binding-source lib/yantra.lisp\n'
            '                     --binding-source lib/result-status.lisp)',
        )
        for sequence in expected:
            with self.subTest(sequence=sequence):
                self.assertIn(sequence, runner)
        self.assertIn('mint_flag=--t5m-mint-pair', runner)
        self.assertIn('"$binary" --t5m-pair "$file" "$physical" "${binding_sources[@]}"', runner)
        # Негатив: старий порядок користувача перед визначенням не приймаємо.
        self.assertNotIn(
            'binding_sources=(--binding-source lib/reason.lisp --binding-source lib/unify.lisp)',
            runner,
        )

    def test_changed_executable_lisp_migration_failure_is_not_green(self):
        # Не видавати пропущене виконання за успішний CI: це борг, а не PASS.
        runner = (ROOT / "scripts/execute_changed_lisp_t5m.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("  if (( blocked > 0 )); then", runner)
        blocked_arm = runner.split("  if (( blocked > 0 )); then", 1)[1].split(
            "  if (( not_program > 0 )); then", 1
        )[0]
        self.assertIn("::error::T5M_MIGRATION_UNPROVEN", blocked_arm)
        self.assertIn("mark_file_failed", blocked_arm)
        self.assertIn("continue", blocked_arm)
        self.assertIn("if (( failed_files > 0 )); then\n  exit 2", runner)

    def test_not_supported_d24_physical_is_counted_not_certified(self):
        # Це guard звітності shell, не Python-імітація SENS семантики.
        runner = (ROOT / "scripts/execute_changed_lisp_t5m.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("physical_not_supported=0", runner)
        self.assertIn(
            "physical_not_supported=$((physical_not_supported + 1))", runner
        )
        # Новий журнал рахує три різні факти, не лише D24 unsupported.
        self.assertIn(
            "physical_not_supported=%s native_view_roundtrip=%s "
            "native_paired_executed=%s native_standalone_parity=%s "
            "scope=changed_manifest semantic=NOT_CERTIFIED release=NOT_CERTIFIED",
            runner,
        )
        self.assertIn(
            "T5M_PHYSICAL_PAIRED_D24_PASS source=$file pair=$pair physical=ZIG_VERIFIED",
            runner,
        )
        self.assertIn("T5M_STANDALONE_D24_NOT_SUPPORTED", runner)

    def test_failed_d24_pair_keeps_real_sens_exit_status(self):
        # Shell-механізм: несправний SENS з кодом 37 не стає status=0
        # після завершення if без else. Реальні байти залишаються обов’язковими.
        runner = (ROOT / "scripts/execute_changed_lisp_t5m.sh").read_text(
            encoding="utf-8"
        )
        beginning = 'if timeout 45s "$binary" --t5m-pair "$file" "$pair"'
        self.assertIn(beginning, runner)
        fallback = runner.split(beginning, 1)[1].split(
            "T5M_PHYSICAL_PAIRED_D24_FAIL", 1
        )[0]
        self.assertIn("      else\n        # Код береться з реального невдалого SENS", fallback)
        self.assertIn("        status=$?\n      fi", fallback)
        self.assertNotIn("      fi\n      status=$?", fallback)
        result = subprocess.run(
            ["bash", "-c",
             "if bash -c 'exit 37'; then :; else status=$?; fi; "
             "printf '%s' \"$status\""],
            capture_output=True, text=True, timeout=5,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "37")

    def test_default_ukr_preserves_program_identity_not_source_comments(self):
        with tempfile.TemporaryDirectory(prefix="sens-ukr-t5m-default-") as temp:
            base = Path(temp)
            sources = base / "джерела"
            sources.mkdir()
            (sources / "одна.lisp").write_text(
                "(перше 2,467)\n", encoding="utf-8"
            )
            (sources / "друга.lisp").write_text(
                "; Інший коментар не входить у програму.\n"
                "#| Довільна вкладеність #| теж коментар |# |#\n"
                "(перше 2,467)\n", encoding="utf-8"
            )
            (sources / "змінена.lisp").write_text(
                "(перше 2,468)\n", encoding="utf-8"
            )
            out = base / "пари"
            report_path = base / "результат.json"
            run = subprocess.run(
                [sys.executable, str(MIGRATOR), str(sources),
                 "--out", str(out), "--report", str(report_path),
                 "--dry-run", "--codec", "t5m"],
                capture_output=True, text=True, timeout=90, cwd=ROOT,
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["file_format"]["source_surface"], "укр")
            self.assertEqual(report["summary"]["files_would_write"], 3)
            self.assertEqual(report["summary"]["files_blocked"], 0)
            records = {row["path"]: row for row in report["files"]}
            self.assertEqual(set(records), {"одна.lisp", "друга.lisp", "змінена.lisp"})
            first, comment, mutated = (records[name] for name in
                                       ("одна.lisp", "друга.lisp", "змінена.lisp"))
            self.assertEqual(first["typed_word_sha256"], comment["typed_word_sha256"])
            self.assertEqual(first["physical_sha256"], comment["physical_sha256"])
            self.assertNotEqual(first["typed_word_sha256"], mutated["typed_word_sha256"])
            self.assertFalse(report["semantic_admitted"])
            self.assertFalse(report["migration_complete"])
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
