#!/usr/bin/env python3
"""Незалежні негативні свідки походження D10 Yantra, без зміни законів мови."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CHECKER = "scripts/check-d10-yantra-library-harvest-v1.py"
METADATA = "knowledge/d10-yantra-library-harvest-v1.json"
DONOR = "knowledge/archive/d10-yantra-donor-76460b72.lisp"
SOURCE = "lib/yantra.lisp"
INPUTS = (
    CHECKER,
    METADATA,
    DONOR,
    SOURCE,
    "knowledge/d10-v1-semantic-inventory.json",
    "knowledge/d10-fill-v1-state.json",
    "knowledge/d1-d9-foundation.json",
)


class YantraProvenanceWitnesses(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="d10-yantra-donor-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for name in INPUTS:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)

    def file(self, name):
        return self.root / name

    def read_metadata(self):
        return json.loads(self.file(METADATA).read_text(encoding="utf-8"))

    def write_metadata(self, value):
        self.file(METADATA).write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def execute(self):
        return subprocess.run(
            [sys.executable, CHECKER],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )

    def expect_blocked(self):
        result = self.execute()
        self.assertNotEqual(result.returncode, 0, result.stdout)

    def test_original_donor_and_current_source_pass(self):
        result = self.execute()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("D10-YANTRA-LIBRARY-HARVEST: PASS", result.stdout)

    def test_optimized_python_cannot_bypass_donor_evidence(self):
        result = subprocess.run(
            [sys.executable, "-O", CHECKER],
            cwd=self.root, capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("D10-YANTRA-DONOR: BLOCKED", result.stderr)

    def test_historical_bytes_changed_fail_closed(self):
        path = self.file(DONOR)
        path.write_bytes(path.read_bytes() + b"\n; tamper\n")
        self.expect_blocked()

    def test_historical_blob_sha_changed_fail_closed(self):
        obj = self.read_metadata()
        obj["donor"]["source_sha"] = "0" * 40
        self.write_metadata(obj)
        self.expect_blocked()

    def test_historical_line_changed_fail_closed(self):
        obj = self.read_metadata()
        obj["rows"][0]["source_line"] += 1
        self.write_metadata(obj)
        self.expect_blocked()

    def test_historical_name_changed_fail_closed(self):
        obj = self.read_metadata()
        obj["rows"][0]["source_name"] = "json-escape-char-fake"
        self.write_metadata(obj)
        self.expect_blocked()

    def test_current_source_may_shift_lines_without_forging_provenance(self):
        path = self.file(SOURCE)
        path.write_text(
            "; нешкідливий коментар: чинні рядки зсунулися\n" +
            path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        result = self.execute()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_current_definition_fail_closed(self):
        path = self.file(SOURCE)
        original = path.read_text(encoding="utf-8")
        header = "(00001001 json-escape-char\n"
        self.assertIn(header, original)
        path.write_text(
            original.replace(header, "(00001001 json-escape-char-removed\n", 1),
            encoding="utf-8",
        )
        self.expect_blocked()

    def test_duplicate_current_definition_fail_closed(self):
        path = self.file(SOURCE)
        path.write_text(
            path.read_text(encoding="utf-8") + "\n(00001001 json-escape-char\n",
            encoding="utf-8",
        )
        self.expect_blocked()

    def test_lookalike_current_definition_is_not_the_identity(self):
        path = self.file(SOURCE)
        original = path.read_text(encoding="utf-8")
        header = "(00001001 json-escape-char\n"
        self.assertIn(header, original)
        path.write_text(
            original.replace(header, "(00001001 json-escape-char-extra\n", 1),
            encoding="utf-8",
        )
        self.expect_blocked()

    def test_unratified_coordinate_cannot_be_admitted(self):
        obj = self.read_metadata()
        obj["rows"][0]["ratified_resident"] = True
        self.write_metadata(obj)
        self.expect_blocked()


if __name__ == "__main__":
    unittest.main()
