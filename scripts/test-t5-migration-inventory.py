#!/usr/bin/env python3
"""Незалежний негативний свідок для реєстру М0 #5444.

Перевіряє не генератор, а справжній manifest у Git:
- схема й enum-и (role, migration_status) дотримані;
- кожна authority-межа присутня зі статусом T5_REQUIRED;
- живий реєстр (перегенерований з дерева) == закомічений manifest —
  тому нову `.sens`-ланку неможливо непомітно загубити;
- дрейф (штучно прибраний рядок) ДЕТЕКТУЄТЬСЯ як FAIL;
- нова ланка, що згадує `.sens`, справді потрапляє у вибірку.

Жодного запису в файли репозиторію: усе в пам'яті / tmp.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MANIFEST = ROOT / "data" / "t5-migration-inventory.jsonl"

ROLES = {"producer", "consumer", "validator", "projection", "benchmark", "unknown"}
STATUSES = {"T5_REQUIRED", "SENC_RESEARCH", "MIGRATION_CANDIDATE", "BLOCKED"}


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "t5_inventory", HERE / "report_t5_migration_inventory.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


GEN = load_generator()


def read_manifest() -> list[dict]:
    return [json.loads(l) for l in MANIFEST.read_text(encoding="utf-8").splitlines()
            if l.strip()]


class TestT5MigrationInventory(unittest.TestCase):
    def test_manifest_exists_nonempty(self):
        self.assertTrue(MANIFEST.is_file(), "manifest missing")
        rows = read_manifest()
        self.assertGreater(len(rows), 100, "manifest suspiciously small")

    def test_schema_enums_and_unique_paths(self):
        rows = read_manifest()
        seen = set()
        for r in rows:
            for field in ("schema", "repository", "path", "role", "canonical_path",
                          "extension", "codec", "authority", "dependency",
                          "base_sha", "owner_lane", "migration_status"):
                self.assertIn(field, r, f"{r.get('path')}: missing {field}")
            self.assertIn(r["role"], ROLES, r["path"])
            self.assertIn(r["migration_status"], STATUSES, r["path"])
            self.assertNotIn(r["path"], seen, f"duplicate path {r['path']}")
            seen.add(r["path"])

    def test_base_sha_is_one_real_ancestor_commit(self):
        rows = read_manifest()
        pins = {r["base_sha"] for r in rows}
        self.assertEqual(len(pins), 1, "manifest must share one provenance pin")
        pin = next(iter(pins))
        self.assertRegex(pin, r"^[0-9a-f]{40}$")
        exists = subprocess.run(
            ["git", "-C", str(ROOT), "cat-file", "-e", f"{pin}^{{commit}}"],
            capture_output=True, text=True)
        self.assertEqual(exists.returncode, 0, f"base_sha is not a Git commit: {pin}")
        ancestor = subprocess.run(
            ["git", "-C", str(ROOT), "merge-base", "--is-ancestor", pin, "HEAD"],
            capture_output=True, text=True)
        self.assertEqual(ancestor.returncode, 0,
                         f"base_sha is not an ancestor of HEAD: {pin}")

    def test_invalid_base_sha_provenance_fails(self):
        rows = read_manifest()
        for row in rows:
            row["base_sha"] = "0" * 40
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False,
                                         encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\\n")
            tmp = fh.name
        try:
            proc = subprocess.run(
                [sys.executable, str(HERE / "report_t5_migration_inventory.py"),
                 "--check", tmp],
                cwd=str(ROOT), capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0,
                                "nonexistent base_sha provenance was NOT detected")
            self.assertIn("manifest provenance", proc.stderr)
        finally:
            Path(tmp).unlink()

    def test_unknown_role_or_owner_lane_is_blocked(self):
        for row in read_manifest():
            if row["path"] in GEN.T5_AUTHORITY:
                continue
            if row["role"] == "unknown" or row["owner_lane"] == "UNKNOWN":
                self.assertEqual(row["migration_status"], "BLOCKED", row["path"])
                self.assertEqual(row["authority"], "UNKNOWN", row["path"])

    def test_authority_boundaries_present(self):
        rows = {r["path"]: r for r in read_manifest()}
        for path in GEN.T5_AUTHORITY:
            self.assertIn(path, rows, f"authority boundary missing: {path}")
            self.assertEqual(rows[path]["migration_status"], "T5_REQUIRED", path)

    def test_live_registry_matches_manifest(self):
        proc = subprocess.run(
            [sys.executable, str(HERE / "report_t5_migration_inventory.py"),
             "--check", str(MANIFEST)],
            cwd=str(ROOT), capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0,
                         f"live registry != manifest:\n{proc.stderr}")

    def test_drift_is_detected(self):
        """Прибраний рядок = FAIL (негативний контроль)."""
        rows = read_manifest()
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False,
                                         encoding="utf-8") as fh:
            for r in rows[:-1]:
                fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
            tmp = fh.name
        try:
            proc = subprocess.run(
                [sys.executable, str(HERE / "report_t5_migration_inventory.py"),
                 "--check", tmp],
                cwd=str(ROOT), capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0,
                                "drift (removed row) was NOT detected")
        finally:
            Path(tmp).unlink()

    def test_new_sens_link_is_discovered(self):
        """Нова ланка, що згадує .sens, потрапляє у вибірку (не губиться)."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            newfile = root / "scripts" / "fresh_link.py"
            newfile.parent.mkdir(parents=True)
            newfile.write_text("# читає canonical .sens через sens_t5_codec\n",
                               encoding="utf-8")
            self.assertTrue(GEN.is_candidate("scripts/fresh_link.py", root),
                            "new .sens-referencing link was not discovered")

    def test_inventory_gate_cannot_filter_out_new_source_consumers(self):
        """Гвардія має запускатися і для нового .rs/.py producer без зміни *.sens."""
        workflow = (ROOT / ".github" / "workflows" / "t5-migration-inventory.yml")
        lines = workflow.read_text(encoding="utf-8").splitlines()
        start = lines.index("on:") + 1

        def sibling_block(name: str) -> list[str]:
            key = f"  {name}:"
            index = lines.index(key, start)
            block = []
            for line in lines[index + 1:]:
                if line.startswith("  ") and not line.startswith("   ") and line.rstrip().endswith(":"):
                    break
                block.append(line)
            return block

        pull_request_block = sibling_block("pull_request")
        self.assertFalse(
            any(line.lstrip().startswith("paths:") for line in pull_request_block),
            "inventory pull_request trigger must not use a path allowlist",
        )
        push_block = sibling_block("push")
        self.assertTrue(
            any(line.strip() == "branches: [main]" for line in push_block),
            "inventory gate must also run for every push to main",
        )



if __name__ == "__main__":
    unittest.main(verbosity=2)
