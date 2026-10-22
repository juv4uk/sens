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
    def test_utf8_named_lisp_is_discovered_by_real_git_diff(self):
        # Git quoting hid Ukrainian .lisp paths from the active SENS/Zig CI
        # manifest; run actual Git instead of simulating filename parsing.
        ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("git -c core.quotePath=false diff --name-only", ci)
        self.assertIn("git -c core.quotePath=false diff-tree --no-commit-id", ci)
        with tempfile.TemporaryDirectory(prefix="sens-ukr-git-path-") as temporary:
            checkout = Path(temporary)
            subprocess.run(["git", "init", "-q"], cwd=checkout, check=True)
            subprocess.run(
                ["git", "-c", "user.name=SENS", "-c", "user.email=sens@example.invalid",
                 "commit", "--allow-empty", "-q", "-m", "empty"],
                cwd=checkout, check=True,
            )
            source = checkout / "lib" / "поміняти-перші-два.lisp"
            source.parent.mkdir()
            source.write_text("(як-є ())\n", encoding="utf-8")
            subprocess.run(["git", "add", "--", str(source.relative_to(checkout))],
                           cwd=checkout, check=True)
            unescaped = subprocess.check_output(
                ["git", "-c", "core.quotePath=false", "diff",
                 "--cached", "--name-only"], cwd=checkout, text=True,
            ).splitlines()
            self.assertEqual(unescaped, ["lib/поміняти-перші-два.lisp"])

    def test_ci_never_treats_human_lisp_as_physical_t5m(self):
        # Застосовується тільки дійсний Zig/T5M + SENS reader/eval.
        # Ні Python preview, ні JSON-звіт не можуть визначати виконуваність.
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        start = workflow.index(
            "      - name: Виконати змінені Lisp через поточний Zig T5M і справжній SENS"
        )
        end = workflow.index("\n      - name:", start + 1)
        execution = workflow[start:end]
        self.assertIn("bash scripts/execute_changed_lisp_t5m.sh", execution)
        self.assertIn('"$binary" "$RUNNER_TEMP/changed-t5m-lisp.txt"', execution)

        runner = (ROOT / "scripts/execute_changed_lisp_t5m.sh").read_text(encoding="utf-8")
        self.assertIn('if [[ "${SENS_NATIVE_T5M:-1}" != 1 ]]; then', runner)
        self.assertIn('SENS_NATIVE_T5M_INVALID', runner)
        self.assertNotIn('python3 scripts/migrate-three-pass.py', runner)
        self.assertNotIn('diagnose_sens_authority_mint', runner)
        self.assertIn('run_native_t5m_program() {', runner)
        self.assertIn('  run_native_t5m_program\ndone < "$manifest"', runner)
        self.assertIn('mint_flag=--t5m-mint', runner)
        self.assertIn('mint_flag=--t5m-mint-pair', runner)
        self.assertIn('"$binary" "$mint_flag" "$file" "$physical" "${binding_sources[@]}"', runner)
        self.assertIn('"$native_open" open "$physical"', runner)
        self.assertIn('"$native_open" verify-view "$physical"', runner)
        self.assertIn('"$binary" --t5m-pair "$file" "$physical" "${binding_sources[@]}"', runner)
        self.assertIn('cmp -s "$dir/native-standalone.stdout" "$dir/native-paired.stdout"', runner)
        self.assertIn('T5M_COMMITTED_PAIR_DRIFT', runner)
        self.assertIn('T5M_COMMITTED_VIEW_MISSING', runner)
        self.assertIn('T5M_COMMITTED_VIEW_DRIFT', runner)
        self.assertIn('T5M_NATIVE_VIEW_ROUNDTRIP_FAILED', runner)
        self.assertNotIn('--t5m-file "$physical"', runner)
        self.assertIn('semantic=NOT_CERTIFIED release=NOT_CERTIFIED', runner)

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
        # Помилки reader, Zig, байтів та реального SENS не замасковано.
        runner = (ROOT / "scripts/execute_changed_lisp_t5m.sh").read_text(encoding="utf-8")
        for marker in (
            'T5M_NATIVE_MINT_FAILED',
            'T5M_NATIVE_VIEW_FAILED',
            'T5M_NATIVE_VIEW_ROUNDTRIP_FAILED',
            'T5M_NATIVE_PAIRED_EXECUTION_FAIL',
            'T5M_NATIVE_EXECUTION_OUTPUT_DRIFT',
            'T5M_NATIVE_STANDALONE_UNEXPECTED_FAIL',
            'T5M_COMMITTED_PAIR_DRIFT',
            'T5M_COMMITTED_VIEW_DRIFT',
        ):
            with self.subTest(marker=marker):
                self.assertIn('::error::' + marker, runner)
        self.assertIn('failed_files=$((failed_files + 1))', runner)
        self.assertIn('if (( failed_files > 0 )); then\n  exit 2', runner)
        self.assertNotIn('T5M_MIGRATION_UNPROVEN', runner)

    def test_known_standalone_limits_do_not_forge_independent_pass(self):
        # Paired-only є точним станом, не підтвердженням автономного
        # виконання, не семантичним PASS і не приводом мовчки гасити RED.
        runner = (ROOT / "scripts/execute_changed_lisp_t5m.sh").read_text(encoding="utf-8")
        self.assertIn('T5M_NATIVE_PAIRED_ONLY source=$file standalone_status=$status', runner)
        self.assertIn('status != 124 && status != 137', runner)
        self.assertIn('unknown Text7 binding:', runner)
        self.assertIn('T5M requires exact source projection to D24+ before transport', runner)
        self.assertIn('T5M_NATIVE_STANDALONE_UNEXPECTED_FAIL', runner)
        self.assertIn('native_view_roundtrip=%s native_paired_executed=%s native_standalone_parity=%s', runner)
        self.assertIn('semantic=NOT_CERTIFIED release=NOT_CERTIFIED', runner)
        self.assertNotIn('physical_not_supported=$((physical_not_supported + 1))', runner)

    def test_failed_native_pair_keeps_real_sens_exit_status(self):
        runner = (ROOT / "scripts/execute_changed_lisp_t5m.sh").read_text(encoding="utf-8")
        start = 'if timeout "$native_timeout" "$binary" --t5m-pair "$file" "$physical"'
        self.assertIn(start, runner)
        segment = runner.split(start, 1)[1].split('T5M_NATIVE_PAIRED_EXECUTION_FAIL', 1)[0]
        self.assertIn('else\n    status=$?', segment)
        self.assertIn('mark_file_failed', runner)
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
