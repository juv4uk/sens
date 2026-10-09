#!/usr/bin/env python3
"""#4455/#4430: Ukrainian D4:1000 CAAR projection with unchanged T5 + exact view."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/migrate-three-pass.py"
FIXTURES = ROOT / "tests/fixtures/migration-d4-selector-cohort"
SOURCE = "(п-п (сполучити (сполучити (як-є ()) (як-є ())) (як-є ())))\n"
HISTORICAL_SOURCE = "(CAAR (CONS (CONS (QUOTE ()) (QUOTE ())) (QUOTE ())))\n"
PROJECTION = "10 1000 00 10 111 00 10 111 00 10 001 00 000 01 00 10 001 00 000 01 01 00 10 001 00 000 01 01 01\n"
PHYSICAL = bytes.fromhex("6612c47ec47ec32da42dc32da42ea937a813b1a1")
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"
ARGS = {
    "foundation": FOUNDATION,
    "domain_surfaces": ROOT / "crates/sens/src/domain_surface_registry_generated.rs",
    "semantic_generated": ROOT / "crates/sens/src/semantic_registry_generated.rs",
    "semantic_registry": ROOT / "crates/sens/src/semantic_registry.rs",
    "necessary_forms": ROOT / "crates/sens/src/eval/necessary_forms_generated.rs",
    "historical_map": ROOT / "contracts/core1-historical-sid-map.lisp",
    "text7": ROOT / "crates/sens/src/text7_projection_generated.rs",
}

spec = importlib.util.spec_from_file_location("d4_caar_migrator", SCRIPT)
assert spec and spec.loader
migration = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = migration
spec.loader.exec_module(migration)


class D4CaarT5Canary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.foundation = migration.load_foundation(FOUNDATION)
        cls.legacy, cls.my, cls.upper = migration.build_three_pass_maps(
            cls.foundation, ARGS["domain_surfaces"], ARGS["semantic_generated"],
            ARGS["semantic_registry"], ARGS["necessary_forms"], ARGS["historical_map"]
        )
        cls.text7 = migration.build_text7(cls.foundation, ARGS["text7"])

    def test_ratified_domain_identity_not_legacy_collision(self):
        self.assertEqual(self.foundation["domains"]["D4"]["residents"]["1000"], "CAAR")
        self.assertEqual(self.foundation["domains"]["D3"]["residents"]["111"], "CONS")
        self.assertEqual(self.foundation["domains"]["D3"]["residents"]["001"], "QUOTE")
        self.assertEqual(self.foundation["domains"]["D3"]["residents"]["000"], "EMPTY")
        self.assertEqual(self.upper["CAAR"], ("1000", "D4"))
        self.assertEqual(self.upper["CONS"], ("111", "D3"))
        self.assertEqual(self.upper["QUOTE"], ("001", "D3"))
        self.assertNotEqual("1000", "100")  # D4:1000 is NOT the D3:100 CAR identity.

    def test_ratified_ukrainian_source_and_committed_physical_bytes(self):
        self.assertEqual((FIXTURES / "caar.lisp").read_text(encoding="utf-8"), SOURCE)
        resolver = migration.Resolver(self.legacy, self.my, self.upper)
        projection = migration.migrate_file(SOURCE, resolver, self.text7)
        self.assertEqual(projection, PROJECTION)
        self.assertEqual(resolver.counts["pass2-my-lisp"], 6)
        self.assertEqual(resolver.counts["pass3-lisp15"], 0)
        self.assertEqual(sum(resolver.counts.values()), 6)
        self.assertEqual(migration.encode_projection(projection), PHYSICAL)
        self.assertEqual(migration.decode_bytes(PHYSICAL), PROJECTION.split())
        self.assertEqual((FIXTURES / "caar.sens").read_bytes(), PHYSICAL)
        self.assertNotEqual(PHYSICAL, SOURCE.encode("utf-8"))
        view = (FIXTURES / "caar").read_bytes()
        self.assertEqual(view, PROJECTION.encode("ascii"))
        self.assertEqual(migration.parse_words(view.decode("ascii")), PROJECTION.split())
        self.assertEqual(migration.encode_projection(view.decode("ascii")), PHYSICAL)
        self.assertEqual(migration.decode_bytes(PHYSICAL), PROJECTION.split())
        self.assertEqual(view.count(b"\n"), 1)
        self.assertNotIn(b"2", view)
        self.assertNotIn(b"(", view)
        self.assertNotIn(b"  ", view)

    def test_historical_and_ukrainian_heads_have_the_same_exact_words(self):
        canonical_resolver = migration.Resolver(self.legacy, self.my, self.upper)
        historic_resolver = migration.Resolver(self.legacy, self.my, self.upper)
        self.assertEqual(
            migration.migrate_file(SOURCE, canonical_resolver, self.text7),
            migration.migrate_file(HISTORICAL_SOURCE, historic_resolver, self.text7)
        )
        self.assertEqual(historic_resolver.counts["pass3-lisp15"], 6)
        self.assertEqual(canonical_resolver.counts["pass2-my-lisp"], 6)
        self.assertEqual(migration.encode_projection(PROJECTION), PHYSICAL)

    def test_real_migrator_cli_no_clobber_and_report(self):
        with tempfile.TemporaryDirectory(prefix="sens-d4-caar-") as name:
            folder = Path(name)
            out = folder / "out"
            report = folder / "report.json"
            cmd = [
                sys.executable, str(SCRIPT), str(FIXTURES), "--out", str(out),
                *[part for key, path in ARGS.items()
                  for part in ("--" + key.replace("_", "-"), str(path))],
                "--report", str(report),
            ]
            result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            summary = json.loads(report.read_text(encoding="utf-8"))["summary"]
            self.assertEqual(summary["files_seen"], 1)
            self.assertEqual(summary["files_written"], 1)
            self.assertEqual(summary["files_blocked"], 0)
            self.assertEqual((out / "caar.sens").read_bytes(), PHYSICAL)
            again = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=60)
            self.assertEqual(again.returncode, 2, again.stdout + again.stderr)
            self.assertEqual((out / "caar.sens").read_bytes(), PHYSICAL)
            self.assertEqual((FIXTURES / "caar.lisp").read_text(encoding="utf-8"), SOURCE)

    def test_noncanonical_and_unmapped_head_are_blocked(self):
        with self.assertRaises(migration.SensT5Error):
            migration.decode_bytes(PHYSICAL + b"\xf2")
        with self.assertRaises(migration.SensT5Error):
            migration.encode_projection("10 CAAR 00 000 01")
        resolver = migration.Resolver(self.legacy, self.my, self.upper)
        unknown = migration.migrate_file("(UNKNOWN (QUOTE ()))", resolver, self.text7)
        with self.assertRaises(migration.SensT5Error):
            migration.encode_projection(unknown)


if __name__ == "__main__":
    unittest.main()
