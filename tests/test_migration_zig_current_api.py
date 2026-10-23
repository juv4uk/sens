#!/usr/bin/env python3
"""One true current three-pass API path into Zig-only T5 publication.

Dry-run keeps source and output untouched; this is not SENS semantic admission.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
DRIVER = ROOT / "scripts/migrate-t5m-batch.py"
INPUT = Path("tests/fixtures/migration-d1-cond-cohort/branch.lisp")



def check_current_resolver_signature(source: str) -> None:
    """Fail if batch reintroduces an obsolete D8 parameter or loses D9 width."""
    tree = ast.parse(source)
    calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "mig"
        and node.func.attr == "Resolver"
    ]
    if len(calls) != 1:
        raise ValueError(
            f"MIGRATION_RESOLVER_API_RED layer=migration "
            f"expected_calls=1 actual_calls={len(calls)}"
        )
    call = calls[0]
    positional = [
        node.id if isinstance(node, ast.Name) else None for node in call.args
    ]
    keywords = [
        (item.arg, item.value.id if isinstance(item.value, ast.Name) else None)
        for item in call.keywords
    ]
    if positional != ["my", "upper"] or keywords != [
        ("d9_residents", "d9_residents")
    ]:
        raise ValueError(
            "MIGRATION_RESOLVER_API_RED layer=migration "
            f"expected=(my,upper,d9_residents) actual={positional!r}/{keywords!r}"
        )


class CurrentThreePassZigCorridorTest(unittest.TestCase):
    def call(self, output: Path, report: Path, *options: str):
        return subprocess.run([
            sys.executable, str(DRIVER), INPUT.as_posix(),
            "--root", str(ROOT), "--out", str(output),
            "--report", str(report), *options,
        ], cwd=ROOT, text=True, capture_output=True, timeout=45, check=False)

    def test_real_ukrainian_source_uses_current_two_map_resolver_in_dry_run(self):
        original = (ROOT / INPUT).read_bytes()
        with tempfile.TemporaryDirectory(prefix="sens-current-zig-api-") as name:
            base = Path(name)
            output = base / "mirror"
            report = base / "receipt.json"
            result = self.call(output, report)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            receipt = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(receipt["summary"]["files_admitted"], 1)
            self.assertEqual(receipt["summary"]["files_blocked"], 0)
            self.assertEqual(receipt["files"][0]["status"], "would-write")
            self.assertEqual(receipt["authority"]["source_era"], "auto")
            self.assertIn("SID8 retired", receipt["authority"]["w8_policy"])
            self.assertFalse(output.exists(), "dry-run cannot publish .sens or view")
        self.assertEqual((ROOT / INPUT).read_bytes(), original)


    def test_current_resolver_api_rejects_stale_d8_and_missing_d9_mutants(self):
        source = DRIVER.read_text(encoding="utf-8")
        check_current_resolver_signature(source)
        live = "mig.Resolver(my, upper, d9_residents=d9_residents)"
        self.assertEqual(source.count(live), 1)
        mutants = {
            "stale-d8-kw": source.replace(
                live,
                "mig.Resolver(my, upper, admitted_d8=admitted_d8, "
                "d9_residents=d9_residents)", 1,
            ),
            "lost-d9-exact-width": source.replace(
                live, "mig.Resolver(my, upper)", 1,
            ),
            "fake-comment-call": source.replace(
                live,
                "mig.Resolver(my, upper, admitted_d8=admitted_d8)\n"
                "        # mig.Resolver(my, upper, d9_residents=d9_residents)", 1,
            ),
        }
        for label, mutant in mutants.items():
            with self.subTest(mutation=label):
                with self.assertRaisesRegex(ValueError, "MIGRATION_RESOLVER_API_RED"):
                    check_current_resolver_signature(mutant)

    def test_explicit_current_d8_ratification_keeps_dry_run_byte_provenance(self):
        original = (ROOT / INPUT).read_bytes()
        with tempfile.TemporaryDirectory(prefix="sens-exact-current-d8-") as name:
            base = Path(name)
            output = base / "mirror"
            report = base / "receipt.json"
            result = self.call(
                output, report, "--source-era", "current"
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            receipt = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(receipt["authority"]["source_era"], "current")
            self.assertEqual(receipt["summary"]["files_admitted"], 1)
            self.assertEqual(receipt["summary"]["files_blocked"], 0)
            row = receipt["files"][0]
            self.assertEqual(row["status"], "would-write")
            self.assertEqual(row["source_sha256"], hashlib.sha256(original).hexdigest())
            self.assertRegex(row["physical_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(row["typed_word_sha256"], r"^[0-9a-f]{64}$")
            self.assertFalse(output.exists(), "current-era dry run must not publish")
        self.assertEqual((ROOT / INPUT).read_bytes(), original)

    def test_retired_sid8_source_era_rejected_before_publication(self):
        with tempfile.TemporaryDirectory(prefix="sens-no-retired-era-") as name:
            base = Path(name)
            output = base / "mirror"
            result = self.call(output, base / "receipt.json", "--source-era", "legacy")
            self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
            self.assertIn("RETIRED_SID8_SOURCE_ERA", result.stderr)
            self.assertFalse(output.exists())

    def test_write_without_zig_is_rejected_before_creating_any_carrier(self):
        with tempfile.TemporaryDirectory(prefix="sens-no-zig-bypass-") as name:
            base = Path(name)
            output = base / "mirror"
            result = self.call(output, base / "receipt.json", "--write")
            self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
            self.assertIn("--write requires --zig-codec", result.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
