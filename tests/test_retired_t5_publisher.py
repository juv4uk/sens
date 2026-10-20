#!/usr/bin/env python3
"""Легкі регресії політики: старий Python/T5 не видає .sens.

Це перевірки заборони публікації, НЕ імітація SENS-семантики.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/migrate-selected-lisp.py"
SPEC = importlib.util.spec_from_file_location("sens_retired_t5_cli", SCRIPT)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class LegacyT5PublicationGuard(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="legacy-t5-guard-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / "out"
        self.report = self.root / "report.json"

    def invoke(self, *extra):
        args = [
            "--source", "lib/core3.lisp",
            "--source-blob", "HEAD",
            "--out-root", str(self.output),
            "--report", str(self.report),
            *extra,
        ]
        with contextlib.redirect_stdout(io.StringIO()):
            code = module.main(args)
        data = json.loads(self.report.read_text(encoding="utf-8"))
        return code, data

    def test_python_legacy_publication_is_blocked_without_running_oracle(self):
        code, report = self.invoke()
        self.assertEqual(code, 2)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["files_written"], 0)
        self.assertIn("LEGACY_T5_PUBLICATION_DISABLED", report["reason"])
        self.assertIn("migrate-one-to-sens.py", report["reason"])
        self.assertFalse(list(self.root.rglob("*.sens")))

    def test_retired_source_era_cannot_reanimate_sid8(self):
        for era in ("legacy", "current"):
            with self.subTest(era=era):
                code, report = self.invoke("--dry-run", "--source-era", era)
                self.assertEqual(code, 2)
                self.assertEqual(report["status"], "BLOCKED")
                self.assertIn("RETIRED_SOURCE_ERA", report["reason"])
                self.assertFalse(list(self.root.rglob("*.sens")))


if __name__ == "__main__":
    unittest.main()
