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
        "t5_inventory", HERE / "report_t5m_migration_inventory.py")
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

    def test_base_sha_is_full_hex(self):
        for r in read_manifest():
            self.assertEqual(len(r["base_sha"]), 40, r["path"])
            int(r["base_sha"], 16)  # підніме ValueError якщо не hex

    def test_authority_boundaries_present(self):
        rows = {r["path"]: r for r in read_manifest()}
        for path in GEN.T5_AUTHORITY:
            self.assertIn(path, rows, f"authority boundary missing: {path}")
            self.assertEqual(rows[path]["migration_status"], "T5_REQUIRED", path)

    def test_live_registry_matches_manifest(self):
        proc = subprocess.run(
            [sys.executable, str(HERE / "report_t5m_migration_inventory.py"),
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
                [sys.executable, str(HERE / "report_t5m_migration_inventory.py"),
                 "--check", tmp],
                cwd=str(ROOT), capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0,
                                "drift (removed row) was NOT detected")
        finally:
            Path(tmp).unlink()


    def test_archived_donor_cannot_acquire_active_codec_authority(self):
        """Архів незмінних донорів не є активним кодеком; живі досліди лишаються видимими."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            archived = ("research/domain-archive/20261011/pr1/"
                        "crates/sens/src/legacy_reader.rs")
            p = root / archived
            p.parent.mkdir(parents=True)
            p.write_text("pub fn encode() { /* physical T5 .sens */ }\\n",
                         encoding="utf-8")
            self.assertFalse(GEN.is_candidate(archived, root),
                             "immutable evidence was misclassified as an active producer")
            active = "research/framed3/adaptive_encoder.py"
            q = root / active
            q.parent.mkdir(parents=True)
            q.write_text("# active experimental .senc encoder\\n",
                         encoding="utf-8")
            self.assertTrue(GEN.is_candidate(active, root),
                            "live codec research must remain discoverable")

    def test_new_sens_link_is_discovered(self):
        """Нова ланка, що згадує .sens, потрапляє у вибірку (не губиться)."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            newfile = root / "scripts" / "fresh_link.py"
            newfile.parent.mkdir(parents=True)
            newfile.write_text("# читає canonical .sens через sens_t5_t5m_codec\n",
                               encoding="utf-8")
            self.assertTrue(GEN.is_candidate("scripts/fresh_link.py", root),
                            "new .sens-referencing link was not discovered")

    def test_quarantined_inventory_is_not_a_second_automatic_workflow(self):
        """Тільки один push-свідок: карантин M0 не стає другим CI-гейтом."""
        workflow = ROOT / ".github" / "workflows" / "t5-migration-inventory.yml"
        source = workflow.read_text(encoding="utf-8")
        event_block = source.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]
        self.assertEqual(
            event_block.strip(), "workflow_dispatch:",
            "карантинний реєстр не може запускатися за push/PR/schedule",
        )
        self.assertIn(
            "    if: ${{ false }}", source,
            "карантин не скасований ратифікованим двійковим свідком",
        )

        central = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        central_events = central.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]
        self.assertIn("\n  push:\n", "\n" + central_events)
        self.assertIn("python3 scripts/ci_one_focused_workflow.py", central)
        # Discovery and manifest equality are checked by independent tests;
        # quarantining the workflow does NOT turn registry drift into PASS.



if __name__ == "__main__":
    unittest.main(verbosity=2)
