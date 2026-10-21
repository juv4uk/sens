"""Перевірка керування міграційним shell-драйвером, не семантики SENS."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
DRIVER = ROOT / "scripts/migrate-active-lib-exact.sh"


class ActiveLibDriverTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory(prefix="sens-driver-control-")
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name)
        for directory in ("scripts", "lib", "bin"):
            (self.root / directory).mkdir()
        shutil.copyfile(DRIVER, self.root / "scripts/migrate-active-lib-exact.sh")
        for name in ("first", "second"):
            (self.root / f"lib/{name}.lisp").write_text("NEEDS\n", encoding="utf-8")
        self.mock = self.root / "bin/sens-to-sens-mock"
        self.mock.write_text(
            '#!/usr/bin/env bash\n'
            'set -euo pipefail\n'
            'if [ "$1" = "--check" ]; then\n'
            '  shift\n'
            '  if [ "$1" = "--language" ]; then shift; fi\n'
            '  for file in "$@"; do\n'
            '    if grep -q NEEDS "$file"; then value=1; else value=0; fi\n'
            '    echo "$file: convertible=$value blocked-unratified=0"\n'
            '  done\n'
            'else\n'
            '  if [ "$1" = "--language" ]; then shift; fi\n'
            '  sed -i s/NEEDS/DONE/ "$1"\n'
            'fi\n', encoding="utf-8")
        self.mock.chmod(0o755)
        for name in ("public_api_inventory.py", "generate-encoder-coverage-input.py"):
            (self.root / "scripts" / name).write_text("", encoding="utf-8")
        self.cargo = self.root / "bin/cargo"
        self.cargo.write_text(
            '#!/usr/bin/env bash\n'
            'echo once >> "$MOCK_CARGO_LOG"\n'
            '[ "$MOCK_CARGO_FAIL" != 1 ]\n', encoding="utf-8")
        self.cargo.chmod(0o755)
        self.log = self.root / "cargo-calls.log"
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "add", "lib"], check=True)
        subprocess.run(["git", "-C", str(self.root), "-c", "user.name=Перевірка",
                        "-c", "user.email=checks@example.invalid", "commit", "-qm", "base"],
                       check=True)

    def run_driver(self, mode, *, fail_cargo=False):
        env = os.environ.copy()
        env.update({
            "SENS_TO_SENS": str(self.mock),
            "MOCK_CARGO_LOG": str(self.log),
            "MOCK_CARGO_FAIL": "1" if fail_cargo else "0",
            "PATH": str(self.root / "bin") + os.pathsep + env.get("PATH", ""),
        })
        return subprocess.run(
            ["bash", str(self.root / "scripts/migrate-active-lib-exact.sh"), mode],
            cwd=self.root, env=env, text=True, capture_output=True, timeout=15,
        )

    def test_check_mode_does_not_run_cargo_or_claim_completion(self):
        for name in ("first", "second"):
            (self.root / f"lib/{name}.lisp").write_text("DONE\n", encoding="utf-8")
        run = self.run_driver("--check")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("EXACT_SOURCE_SCAN_PASS:", run.stdout)
        self.assertIn("consumers=NOT_CHECKED", run.stdout)
        self.assertIn("SENS/T5M=NOT_CERTIFIED", run.stdout)
        self.assertFalse(self.log.exists())
        self.assertNotIn("MIGRATION_COMPLETE", run.stdout)

    def test_empty_library_cannot_report_clean_scan(self):
        # Відсутній корпус не повинен перетворюватися на фальшивий зелений висновок.
        for name in ("first", "second"):
            (self.root / f"lib/{name}.lisp").unlink()
        run = self.run_driver("--check")
        self.assertNotEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("SOURCE_SCAN_ERROR: no active executable Lisp sources", run.stderr)
        self.assertNotIn("EXACT_SOURCE_SCAN_PASS", run.stdout)
        self.assertFalse(self.log.exists())

    def test_scanner_nonzero_cannot_be_reported_as_green(self):
        # A truncated/crashed native tool can print convertible=0 before
        # exiting with a failure. A green-looking row is not a clean scan.
        for name in ("first", "second"):
            (self.root / f"lib/{name}.lisp").write_text("DONE\n", encoding="utf-8")
        self.mock.write_text(
            '#!/usr/bin/env bash\n'
            'set -euo pipefail\n'
            'if [[ "$1" == "--check" ]]; then\n'
            '  shift\n'
            '  for file in "$@"; do\n'
            '    echo "$file: convertible=0 blocked-unratified=0"\n'
            '  done\n'
            '  exit 23\n'
            'fi\n'
            'exit 23\n', encoding="utf-8",
        )
        run = self.run_driver("--check")
        self.assertEqual(run.returncode, 23, run.stdout + run.stderr)
        self.assertIn("SOURCE_SCAN_ERROR: scanner exit=23", run.stderr)
        self.assertNotIn("EXACT_SOURCE_SCAN_PASS:", run.stdout)
        self.assertFalse(self.log.exists())
        for name in ("first", "second"):
            self.assertEqual((self.root / f"lib/{name}.lisp").read_text(), "DONE\n")

    def test_apply_converts_both_files_and_checks_consumers_only_once(self):
        run = self.run_driver("--apply")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        for name in ("first", "second"):
            self.assertEqual((self.root / f"lib/{name}.lisp").read_text(), "DONE\n")
        self.assertEqual(self.log.read_text().splitlines(), ["once"])
        self.assertIn("source-rewritten: 2", run.stdout)
        self.assertIn("MIGRATION_SOURCE_CONSUMERS_PASS:", run.stdout)
        self.assertIn("SENS/T5M=NOT_CERTIFIED", run.stdout)

    def test_red_consumer_keeps_changes_and_fails_visibly(self):
        run = self.run_driver("--apply", fail_cargo=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(self.log.read_text().splitlines(), ["once"])
        self.assertIn("REPAIR_REQUIRED: consumer failure", run.stdout)
        self.assertIn("MIGRATION_INCOMPLETE:", run.stdout)
        for name in ("first", "second"):
            self.assertEqual((self.root / f"lib/{name}.lisp").read_text(), "DONE\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
