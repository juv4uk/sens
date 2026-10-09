#!/usr/bin/env python3
import hashlib
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "knowledge/migration-nonprogram-print-manifest-2026-10-08.json"
BASELINE = ROOT / "crates/sens/tests/data/english-names-baseline.tsv"

def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

class MigrationNonProgramPrintManifest(unittest.TestCase):
    def test_manifest_has_exact_75_baseline_print_paths(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "sens-migration-nonprogram-manifest/1")
        self.assertEqual(data["classification"], "benchmark-recording-nonprogram")
        self.assertFalse(data["automatic_sens_companion"])

        expected = sorted({
            line.split("\t")[1]
            for line in BASELINE.read_text(encoding="utf-8").splitlines()
            if "\tprint\t" in line
            and line.split("\t")[1].startswith("benchmarks/sens-surface/results/")
            and "/programs/" in line.split("\t")[1]
            and line.split("\t")[1].endswith(".lisp")
        })
        actual = [entry["path"] for entry in data["entries"]]
        self.assertEqual(len(actual), 75)
        self.assertEqual(actual, expected)

        for entry in data["entries"]:
            rel = pathlib.PurePosixPath(entry["path"])
            self.assertTrue(rel.parts[:4] == ("benchmarks","sens-surface","results",rel.parts[3]))
            self.assertEqual(rel.suffix, ".lisp")
            source = ROOT / rel
            payload = source.read_bytes()
            self.assertEqual(git_blob_sha1(payload), entry["git_blob_sha1"], rel.as_posix())
            self.assertFalse(source.with_suffix(".sens").exists(),
                             f"{rel}: benchmark recording must not gain an executable .sens automatically")

    def test_executable_sources_are_not_exempted(self):
        paths = {entry["path"] for entry in json.loads(MANIFEST.read_text(encoding="utf-8"))["entries"]}
        self.assertNotIn("lib/core.lisp", paths)
        self.assertNotIn("lib/core1.lisp", paths)
        self.assertNotIn("lib/machine/dispatch/native-first.lisp", paths)

if __name__ == "__main__":
    unittest.main()
