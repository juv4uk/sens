#!/usr/bin/env python3
import hashlib
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "knowledge/migration-nonprogram-schema-manifest-2026-10-08.json"

def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}".encode() + b"\\0"
    return hashlib.sha1(header + data).hexdigest()

def first_code_line(text: str) -> str:
    for raw in text.splitlines():
        line = raw.strip()
        if line and not line.startswith(";"):
            return line
    return ""

class MigrationNonProgramSchemaManifest(unittest.TestCase):
    def test_manifest_is_bounded_and_sources_stay_declarative(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "sens-migration-nonprogram-manifest/1")
        self.assertEqual(data["classification"], "lisp-data-nonprogram")
        self.assertFalse(data["automatic_sens_companion"])
        entries = data["entries"]
        self.assertEqual(len(entries), 21)

        for entry in entries:
            rel = pathlib.PurePosixPath(entry["path"])
            self.assertIn(rel.parts[0], ("contracts", "lib", "tests"))
            self.assertEqual(rel.suffix, ".lisp")
            source = ROOT / rel
            payload = source.read_bytes()
            self.assertEqual(git_blob_sha1(payload), entry["git_blob_sha1"], rel.as_posix())
            self.assertTrue(
                first_code_line(payload.decode("utf-8")).startswith("(schema "),
                rel.as_posix(),
            )
            self.assertFalse(
                source.with_suffix(".sens").exists(),
                f"{rel}: declarative schema/data must not gain executable .sens automatically",
            )

    def test_executable_lisp_is_not_covered_by_the_exemption(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        paths = {entry["path"] for entry in data["entries"]}
        for executable in (
            "lib/core.lisp",
            "lib/core1.lisp",
            "lib/machine/dispatch/native-first.lisp",
        ):
            self.assertNotIn(executable, paths)

if __name__ == "__main__":
    unittest.main()
