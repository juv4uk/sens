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
        self.assertIn('python3 scripts/migrate-three-pass.py "$file"', runner)
        self.assertIn('--codec t5m --source-surface укр', runner)
        self.assertIn('pair="$dir/$(basename "$file" .lisp).sens"', runner)
        # --t5m-file читає текстовий Lisp (read_to_string); для створеного
        # фізичного T5M слід викликати окремий .sens ingress, без цього прапорця.
        self.assertIn('if timeout 45s "$binary" "$pair"', runner)
        self.assertNotIn('--t5m-file "$pair"', runner)
        self.assertIn('T5M_COMMITTED_PAIR_DRIFT', runner)
        self.assertIn('T5M_FILE_EXECUTION_FAIL', runner)
        cli = (ROOT / "crates/sens-cli/src/main.rs").read_text(encoding="utf-8")
        self.assertIn('fs::read_to_string(filename)', cli)
        self.assertIn('fs::read(filename)', cli)

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
