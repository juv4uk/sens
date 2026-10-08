#!/usr/bin/env python3
import json
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "knowledge/migration-nonprogram-schema-manifest-2026-10-08.json"

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
            actual_blob = subprocess.run(
                ["git", "rev-parse", f"HEAD:{rel.as_posix()}"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertEqual(actual_blob, entry["git_blob_sha1"], rel.as_posix())
            source_text = payload.decode("utf-8")
            self.assertRegex(
                source_text,
                r"(?ms)^\(\s*\n?\s*\(schema\b",
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
