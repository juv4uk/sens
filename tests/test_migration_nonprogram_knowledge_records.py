#!/usr/bin/env python3
"""Guard 14 immutable KNOWLEDGE DATA records against fake executable SENS migration."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "knowledge/migration-nonprogram-knowledge-records-2026-10-08.json"

EXPECTED = {
    "knowledge/agent-discoveries.lisp": "agent-discoveries",
    "knowledge/canon-authority-inventory.lisp": "schema",
    "knowledge/core4-predicate-record-inventory.lisp": "core4-predicate-record-inventory/2",
    "knowledge/function-table-sculpt-audit.lisp": "function-table-sculpt-audit/1",
    "knowledge/meta-eval-evidence.lisp": "schema",
    "knowledge/repo-tooling-inventory.lisp": "about",
    "knowledge/sanskrit-cyrillic-audit.lisp": "sanskrit-cyrillic-audit",
    "knowledge/sanskrit-cyrillic-keyboard.lisp": "sanskrit-cyrillic-keyboard",
    "knowledge/sanskrit-cyrillic-phoneme-map.lisp": "sound-unit-registry",
    "knowledge/semantic-lineage-core-v1.lisp": "semantic-lineage/1",
    "knowledge/semantic-ownership.lisp": "schema",
    "knowledge/sens-primary.lisp": "sens-primary/2",
    "knowledge/silent-fallback-inventory.lisp": "silent-fallback-inventory",
    "knowledge/structure-not-ontology-inventory.lisp": "structure-not-ontology/1",
}

def source_git_blob_sha(payload: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload).hexdigest()

def first_record_head(source: str) -> str:
    for raw in source.splitlines():
        line = raw.strip()
        if not line or line.startswith(";"):
            continue
        match = re.match(r"^\(([^\s()]+)", line)
        if not match:
            raise AssertionError("expected immutable first top-level Lisp DATA record")
        return match.group(1)
    raise AssertionError("empty knowledge record")

class KnowledgeRecordSources(unittest.TestCase):
    def test_all_pinned_originals_are_data_not_executable_programs(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], "sens-migration-nonprogram-manifest/1")
        self.assertEqual(manifest["issue"], 4460)
        self.assertEqual(manifest["classification"], "lisp-data-nonprogram")
        self.assertIs(manifest["automatic_sens_companion"], False)
        entries = manifest["entries"]
        self.assertEqual(len(entries), len(EXPECTED))
        self.assertEqual([x["path"] for x in entries], sorted(EXPECTED))
        for item in entries:
            path = item["path"]
            self.assertIn(path, EXPECTED, path)
            self.assertEqual(item["record_head"], EXPECTED[path], path)
            rel = Path(path)
            self.assertFalse(rel.is_absolute() or ".." in rel.parts)
            src = ROOT / rel
            self.assertFalse(src.is_symlink(), path)
            payload = src.read_bytes()
            self.assertEqual(source_git_blob_sha(payload), item["git_blob_sha1"], path)
            self.assertEqual(first_record_head(payload.decode("utf-8")), EXPECTED[path], path)
            self.assertFalse(src.with_suffix(".sens").exists(), path)

    def test_executable_and_module_sources_never_get_data_exemption(self):
        for path in (
            "knowledge/astronomy.lisp", "knowledge/family.lisp",
            "knowledge/physics.lisp", "knowledge/guard-fact-policy.lisp",
            "knowledge/guard-runtime-policy.lisp",
            "knowledge/language-detection-probe.lisp",
            "examples/ukrainian-greeting.lisp", "lib/core1.lisp",
        ):
            self.assertNotIn(path, EXPECTED)

    def test_canonical_census_imports_14_reviewed_data_rows(self):
        script = ROOT / "scripts/report_original_migration_candidates.py"
        spec = importlib.util.spec_from_file_location("original_candidates_knowledge_test", script)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        classifications = mod.load_nonprogram_classification(ROOT)
        knowledge = [x for x in classifications.values() if x["cohort"] == "knowledge-record"]
        self.assertEqual(len(knowledge), 14)
        self.assertEqual({x["path"] for x in knowledge}, set(EXPECTED))
        self.assertTrue(all(not x["automatic_sens_companion"] for x in knowledge))
        self.assertTrue(all(x["source_class"] == "NONPROGRAM_DATA_REVIEWED" for x in knowledge))

if __name__ == "__main__":
    unittest.main()
