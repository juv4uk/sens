#!/usr/bin/env python3
"""CLI security/provenance checks. Fake oracle exercises protocol, NOT semantics.

True D4 semantic oracle separately runs via Cargo in the same GitHub workflow.
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/migrate-selected-lisp.py"
spec = importlib.util.spec_from_file_location("one_file_t5_admission", SCRIPT)
assert spec and spec.loader
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

SOURCE = "tests/fixtures/migration-d4-selector-cohort/caar.lisp"
LEGACY_UNPROVEN = "benchmarks/closures.lisp"
EXPECTED_PHYSICAL = bytes.fromhex("6612c47ec47ec32da42dc32da42ea937a813b1a1")

def source_blob(path):
    data = (ROOT / path).read_bytes()
    return app.git_blob(data)

def fake_oracle(path: Path, *, disagreement=False):
    # The test double makes no claim to independent historical Lisp execution.
    # Positive tests prove only the admission tool's JSON / file-I/O mechanics.
    program = """#!/usr/bin/env python3
import hashlib, json, pathlib, sys
src, physical = (pathlib.Path(p) for p in sys.argv[1:3])
root = pathlib.Path(__file__).resolve().parents[5] if False else None
raw = src.read_bytes()
wire = physical.read_bytes()
from pathlib import Path
repo = Path(%r)
sys.path.insert(0,str(repo / "scripts"))
from sens_t5_codec import decode_bytes, typed_sha256
words = decode_bytes(wire)
d = {
 "schema":"sens-historical-current-oracle/v1", "status":"PASS",
 "source_blob_sha":hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\\0"+raw).hexdigest(),
 "physical_sha256":hashlib.sha256(wire).hexdigest(),
 "typed_word_sha256":typed_sha256(words),
 "historical_observable":"Nil", "current_observable":%r,
 "evidence":"TEST DOUBLE only; CI runs real Rust D4 oracle separately"
}
print(json.dumps(d))
""" % (str(ROOT), "NotNil" if disagreement else "Nil")
    path.write_text(program, encoding="utf-8")
    path.chmod(0o755)

class SelectedOriginalT5(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="sens-selected-test-")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.reader = ROOT / "target/debug/sens-trit"
        self.report = self.folder / "report.json"
        self.output = self.folder / "output"
        self.verifier = self.folder / "oracle"
        fake_oracle(self.verifier)
        self.orig = (ROOT / SOURCE).read_bytes()

    def call(self, source=SOURCE, *, blob=None, era="auto", oracle=True,
             reader=True, dry=False, inspect=False, out=None):
        args = [
            "--source", source,
            "--source-blob", source_blob(source) if blob is None else blob,
            "--source-era", era,
            "--out-root", str(out or self.output),
            "--report", str(self.report),
        ]
        if oracle:
            args.extend(["--oracle", str(self.verifier)])
        if reader:
            args.extend(["--reader", str(self.reader)])
        if dry:
            args.append("--dry-run")
        if inspect:
            args.append("--inspect")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = app.main(args)
        payload = json.loads(self.report.read_text(encoding="utf-8"))
        self.assertEqual(json.loads(output.getvalue())["status"], payload["status"])
        return code, payload

    def test_pinned_original_not_fake_new_file(self):
        self.assertEqual(source_blob(SOURCE), "407685130e53a0129b8d1b86e8e20b36270965ba")
        self.assertEqual(self.orig.decode(), "(п-п (сполучити (сполучити (як-є ()) (як-є ())) (як-є ())))\n")
        self.assertEqual((ROOT / SOURCE).read_bytes(), self.orig)

    def test_bad_blob_blocks_even_before_conversion(self):
        code, state = self.call(blob="0" * 40)
        self.assertEqual((code, state["status"]), (2, "BLOCKED"))
        self.assertIn("source changed", state["reason"])
        self.assertFalse(list(self.output.rglob("*.sens")))

    def test_unknown_original_dynamic_binding_blocks(self):
        code, state = self.call(LEGACY_UNPROVEN)
        self.assertEqual((code, state["status"]), (2, "BLOCKED"))
        self.assertTrue(state["reason"])
        self.assertFalse(list(self.output.rglob("*.sens")))

    def test_unverified_oracle_never_writes(self):
        code, state = self.call(oracle=False)
        self.assertEqual((code, state["status"]), (2, "BLOCKED"))
        self.assertFalse(list(self.output.rglob("*.sens")))

    def test_unverified_rust_reader_never_writes(self):
        code, state = self.call(reader=False)
        self.assertEqual((code, state["status"]), (2, "BLOCKED"))
        self.assertFalse(list(self.output.rglob("*.sens")))

    def test_path_traversal_is_rejected(self):
        code, state = self.call(source="../outside.lisp", blob="0" * 40)
        self.assertEqual((code, state["status"]), (2, "BLOCKED"))
        self.assertIn("relative", state["reason"])

    def test_inspect_requires_no_oracle_and_never_writes(self):
        if not self.reader.is_file():
            self.fail("build real Rust sens-trit opener before inspection")
        # HEAD is pinned to a committed Git blob, never a mutable workspace
        # shortcut. This route MUST NOT fake a semantic PASS.
        code, state = self.call(blob="HEAD", inspect=True, oracle=False)
        self.assertEqual(code, 0, state)
        self.assertEqual(state["status"], "SYNTAX_ONLY_UNVERIFIED")
        self.assertEqual(state["syntax"], "PASS_D2_SYNTAX_ONLY")
        self.assertEqual(state["oracle"], "NOT_VERIFIED")
        self.assertEqual(state["files_written"], 0)
        self.assertEqual(state["source_blob_sha"], source_blob(SOURCE))
        self.assertEqual(len(state["source_commit"]), 40)
        self.assertFalse(list(self.output.rglob("*.sens")))
        self.assertEqual((ROOT / SOURCE).read_bytes(), self.orig)

    def test_one_file_resolver_uses_owner_audited_w8_and_explicit_era(self):
        # No oracle is bypassed here: this inspects only canonical head mapping,
        # never publishes an original executable SENS artifact.
        migration = app.load_migrator()
        foundation = migration.load_foundation(ROOT / "knowledge/d1-d9-foundation.json")
        legacy, my, upper = migration.build_three_pass_maps(
            foundation,
            ROOT / "crates/sens/src/domain_surface_registry_generated.rs",
            ROOT / "crates/sens/src/semantic_registry_generated.rs",
            ROOT / "crates/sens/src/semantic_registry.rs",
            ROOT / "crates/sens/src/eval/necessary_forms_generated.rs",
            ROOT / "contracts/core1-historical-sid-map.lisp",
            ROOT / "knowledge/sens8-current-coverage-v1.json",
        )
        self.assertEqual(legacy["01001000"][:2], ("11011011", "D8"))
        self.assertNotIn("00001010", migration.parse_audited_legacy_successors(
            ROOT / "knowledge/sens8-current-coverage-v1.json", foundation))
        admitted_d8 = foundation["domains"]["D8"]["residents"]
        text7 = migration.build_text7(
            foundation, ROOT / "crates/sens/src/text7_projection_generated.rs")
        original = "(01001000 000)\n"
        old = migration.Resolver(
            legacy, my, upper, source_era="legacy", admitted_d8=admitted_d8)
        now = migration.Resolver(
            legacy, my, upper, source_era="current", admitted_d8=admitted_d8)
        self.assertTrue(migration.migrate_file(original, old, text7).startswith(
            "10 11011011 00 "))
        self.assertEqual(old.counts["pass1-sens8"], 1)
        self.assertTrue(migration.migrate_file(original, now, text7).startswith(
            "10 01001000 00 "))
        self.assertEqual(now.counts["already-exact"], 1)
        automatic = migration.Resolver(
            legacy, my, upper, source_era="auto", admitted_d8=admitted_d8)
        with self.assertRaisesRegex(migration.MigrationError, "ambiguous W8"):
            migration.migrate_file(original, automatic, text7)

    def test_real_unpaired_original_files_are_audited_not_converted(self):
        # These are tracked old files, not fabricated canaries or newly authored
        # snapshots. They include local binding, Text7 and machine-data issues.
        for old in ("benchmarks/closures.lisp", "benchmarks/parser.lisp",
                    "lib/machine/block.lisp"):
            with self.subTest(source=old):
                original = (ROOT / old).read_bytes()
                code, state = self.call(old, blob="HEAD", era="legacy",
                                        inspect=True, oracle=False)
                self.assertIn(state["status"], {"BLOCKED", "SYNTAX_ONLY_UNVERIFIED"})
                self.assertIn(code, (0, 2))
                self.assertFalse(list(self.output.rglob("*.sens")))
                self.assertEqual(original, (ROOT / old).read_bytes())
                self.assertFalse(state["original_491_reduced"])
                if state["status"] == "BLOCKED":
                    self.assertTrue(state["reason"])
                else:
                    self.assertEqual(state["oracle"], "NOT_VERIFIED")
                    self.assertEqual(state["files_written"], 0)

    def test_corrupt_oracle_claim_is_rejected(self):
        if not self.reader.is_file():
            self.fail("build the real Rust sens-trit opener before running this test")
        fake_oracle(self.verifier, disagreement=True)
        code, state = self.call()
        self.assertEqual((code, state["status"]), (2, "BLOCKED"))
        self.assertIn("observations differ", state["reason"])
        self.assertFalse(list(self.output.rglob("*.sens")))

    def test_exact_physical_file_then_immutability_and_no_clobber(self):
        if not self.reader.is_file():
            self.fail("build the real Rust sens-trit opener before running this test")
        code, state = self.call(dry=True)
        self.assertEqual(code, 0, state)
        self.assertEqual(state["status"], "VERIFIED_DRY_RUN")
        self.assertEqual(state["binary_bytes"], 20)
        self.assertEqual(state["syntax"], "PASS_D2_SYNTAX_ONLY")
        self.assertEqual(state["oracle"], "PASS_HISTORICAL_CURRENT")
        self.assertFalse(list(self.output.rglob("*.sens")))
        code, state = self.call()
        self.assertEqual(code, 0, state)
        self.assertEqual(state["status"], "WRITTEN")
        self.assertFalse(state["original_491_reduced"])
        target = self.output / "tests/fixtures/migration-d4-selector-cohort/caar.sens"
        self.assertEqual(target.read_bytes(), EXPECTED_PHYSICAL)
        self.assertEqual(state["physical_sha256"], hashlib.sha256(EXPECTED_PHYSICAL).hexdigest())
        self.assertEqual((ROOT / SOURCE).read_bytes(), self.orig)
        again_code, again = self.call()
        self.assertEqual((again_code, again["status"]), (2, "BLOCKED"))
        self.assertIn("already exists", again["reason"])
        self.assertEqual(target.read_bytes(), EXPECTED_PHYSICAL)

    def test_existing_symlink_is_rejected(self):
        fake = self.folder / "elsewhere"
        fake.mkdir()
        leaf = self.output / "tests/fixtures/migration-d4-selector-cohort"
        leaf.mkdir(parents=True)
        (leaf / "caar.sens").symlink_to(fake, target_is_directory=True)
        code, state = self.call()
        self.assertEqual((code, state["status"]), (2, "BLOCKED"))

if __name__ == "__main__":
    unittest.main()
