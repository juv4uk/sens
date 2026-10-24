#!/usr/bin/env python3
"""D1–D11 ratified domain tables are DATA, never executable SENS."""
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "knowledge/migration-nonprogram-domain-tables-2026-10-08.json"


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()


def resident_codes(source: str, width: int) -> list[str]:
    """Parse only full top-level table row prefixes, not nested surface data."""
    return re.findall(
        r"^  \(([01]{" + str(width) + r"})(?=\s|\))", source, flags=re.M
    )


class DomainTableNotExecutableTest(unittest.TestCase):
    def test_current_d1_d11_data_classification_is_exact_and_immutable(self):
        m = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(m["schema"], "sens-migration-nonprogram-manifest-1")
        self.assertEqual(m["issue"], 4460)
        self.assertEqual(m["classification"], "lisp-data-nonprogram")
        self.assertIs(m["automatic_sens_companion"], False)
        self.assertIs(m["not_executable_programs"], True)
        self.assertIs(m["not_physical_migration_credit"], True)
        rows = m["entries"]
        self.assertEqual(len(rows), 11)
        self.assertEqual(
            [row["path"] for row in rows],
            [f"lib/domains/d{n}.lisp" for n in range(1, 12)],
        )
        total = 0
        for n, entry in enumerate(rows[:10], start=1):
            path = ROOT / entry["path"]
            with self.subTest(path=entry["path"]):
                self.assertEqual(entry["domain"], f"D{n}")
                self.assertEqual(entry["bit_width"], n)
                self.assertEqual(entry["expected_rows"], 2**n)
                self.assertFalse(path.is_symlink())
                raw = path.read_bytes()
                self.assertEqual(git_blob_sha(raw), entry["git_blob_sha1"])
                self.assertFalse(path.with_suffix(".sens").exists())
                self.assertFalse(path.with_suffix("").exists())
                source = raw.decode("utf-8")
                body = [
                    line.strip() for line in source.splitlines()
                    if line.strip() and not line.lstrip().startswith(";")
                ]
                self.assertTrue(body, path.as_posix())
                # Єдиний чинний заголовок у D1–D11, той самий що у збірці Rust.
                # Не дозволяємо історичний domain-table/1 як відкат джерела.
                self.assertEqual(body[0], "(domain-table-1")
                self.assertEqual(body[-1], ")")
                codes = resident_codes(source, n)
                self.assertEqual(len(codes), entry["expected_rows"])
                self.assertEqual(len(set(codes)), len(codes))
                self.assertTrue(all(len(code) == n for code in codes))
                if n == 7:
                    self.assertIn("0100001", codes)
                    self.assertIn("0101010", codes)
                    self.assertEqual(entry["projection"], "sens.d7.keyboard/v2")
                    self.assertEqual(entry["historical_v1_git_blob_sha1"], "a618f27aeb75c1c2ef1bb6dbdf33c9a10aefb726")
                if n == 10:
                    self.assertEqual(entry["role"], "whole-domain-catalogue")
                total += len(codes)
        self.assertEqual(total, 2046)

        # D11 is the working extension domain (512 selectors derived by
        # selector-suffix-extension of a 2048-capacity domain), NOT a
        # callable Core domain. The retired 43-word testing vocabulary was
        # owner-rejected and archived (lib/domains/archive/d11-rejected-43.lisp).
        entry = rows[10]
        path = ROOT / entry["path"]
        with self.subTest(path=entry["path"]):
            self.assertEqual(entry["domain"], "D11")
            self.assertEqual(entry["bit_width"], 11)
            self.assertEqual(entry["expected_rows"], 512)
            self.assertEqual(entry["role"], "working-extension-domain")
            self.assertFalse(path.is_symlink())
            self.assertFalse(path.with_suffix(".sens").exists())
            self.assertFalse(path.with_suffix("").exists())
            raw = path.read_bytes()
            self.assertEqual(git_blob_sha(raw), entry["git_blob_sha1"])
            source = raw.decode("utf-8")
            body = [
                line.strip() for line in source.splitlines()
                if line.strip() and not line.lstrip().startswith(";")
            ]
            self.assertEqual(body[0], "(domain-table-1")
            self.assertEqual(body[-1], ")")
            codes = resident_codes(source, 11)
            self.assertEqual(len(codes), 512)
            self.assertEqual(len(set(codes)), 512)
            self.assertTrue(all(len(code) == 11 for code in codes))
        total += len(codes)
        self.assertEqual(total, m["total_rows"])
        self.assertEqual(total, 2558)

    def test_no_executable_or_research_paths_are_exempted(self):
        paths = {r["path"] for r in json.loads(MANIFEST.read_text())["entries"]}
        for path in (
            "lib/core1.lisp", "lib/machine/block.lisp",
            "lib/machine/dispatch/native-first.lisp",
            "benchmarks/arithmetic.lisp",
        ):
            self.assertNotIn(path, paths)



if __name__ == "__main__":
    unittest.main()
