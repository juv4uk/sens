#!/usr/bin/env python3
"""Негативні свідки чинної та історичної provenance Yantra."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
INPUTS = (
    "lib/yantra.lisp",
    "scripts/check-d10-yantra-library-harvest-v1.py",
    "knowledge/d10-yantra-library-harvest-v1.json",
    "knowledge/d10-v1-semantic-inventory.json",
    "knowledge/d10-fill-v1-state.json",
    "knowledge/d1-d9-foundation.json",
)


class CurrentAndHistoricalPins(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="d10-yantra-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in INPUTS:
            dest = self.root / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, dest)

    def metadata(self):
        path = self.root / INPUTS[2]
        return path, json.loads(path.read_text(encoding="utf-8"))

    def save(self, path, data):
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def check(self):
        return subprocess.run(
            [sys.executable, "scripts/check-d10-yantra-library-harvest-v1.py"],
            cwd=self.root, text=True, capture_output=True, check=False
        )

    def blocked(self):
        proc = self.check()
        self.assertNotEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("AssertionError", proc.stderr)

    def rehash_current(self):
        source = self.root / INPUTS[0]
        path, data = self.metadata()
        data["current_observation"]["source_sha"] = subprocess.check_output(
            ["git", "hash-object", "--", str(source)], cwd=self.root, text=True
        ).strip()
        self.save(path, data)

    def test_actual_source_passes(self):
        proc = self.check()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("D10-YANTRA-LIBRARY-HARVEST: PASS", proc.stdout)

    def test_modified_hash_is_rejected(self):
        path, data = self.metadata()
        data["current_observation"]["source_sha"] = "0" * 40
        self.save(path, data)
        self.blocked()

    def test_shifted_source_is_rejected_after_rehash(self):
        path = self.root / INPUTS[0]
        path.write_text("; доданий рядок\n" + path.read_text(encoding="utf-8"), encoding="utf-8")
        self.rehash_current()
        self.blocked()

    def test_duplicate_definition_is_rejected_after_rehash(self):
        path = self.root / INPUTS[0]
        with path.open("a", encoding="utf-8") as stream:
            stream.write("\n(00001001 json-escape-char (00001000 (ch) ch))\n")
        self.rehash_current()
        self.blocked()

    def test_historical_line_is_immutable(self):
        path, data = self.metadata()
        data["rows"][0]["source_line"] += 1
        self.save(path, data)
        self.blocked()

    def test_no_unreviewed_ratification(self):
        path, data = self.metadata()
        data["rows"][0]["ratified_resident"] = True
        self.save(path, data)
        self.blocked()


if __name__ == "__main__":
    unittest.main()
