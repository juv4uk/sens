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
from sens_t5_t5m_codec import decode_bytes, typed_sha256
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
        self.assertEqual(source_blob(SOURCE), "44c4e8cad5442d74bcecef6f115fa1e14c68a5c0")
        self.assertEqual(self.orig.decode(), "(перше-першого (сполучити (сполучити (як-є ()) (як-є ())) (як-є ())))\n")
        self.assertEqual((ROOT / SOURCE).read_bytes(), self.orig)

    def test_bad_blob_blocks_even_before_conversion(self):
        code, state = self.call(blob="0" * 40, dry=True)
        self.assertEqual((code, state["status"]), (2, "BLOCKED"))
        self.assertIn("source changed", state["reason"])
        self.assertFalse(list(self.output.rglob("*.sens")))

    def test_unproven_original_inspection_is_syntax_only_and_never_publishes(self):
        code, state = self.call(LEGACY_UNPROVEN, inspect=True)
        self.assertEqual((code, state["status"]), (0, "SYNTAX_ONLY_UNVERIFIED"))
        self.assertEqual(state["oracle"], "NOT_VERIFIED")
        self.assertEqual(state["files_written"], 0)
        self.assertFalse(list(self.output.rglob("*.sens")))

    def test_unverified_oracle_never_writes(self):
        code, state = self.call(oracle=False, dry=True)
        self.assertEqual((code, state["status"]), (2, "BLOCKED"))
        self.assertFalse(list(self.output.rglob("*.sens")))

    def test_unverified_rust_reader_never_writes(self):
        code, state = self.call(reader=False, dry=True)
        self.assertEqual((code, state["status"]), (2, "BLOCKED"))
        self.assertFalse(list(self.output.rglob("*.sens")))

    def test_path_traversal_is_rejected(self):
        code, state = self.call(source="../outside.lisp", blob="0" * 40, dry=True)
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

    def test_retired_source_eras_are_rejected_before_projection(self):
        # Historical interpretation is provenance, not an execution switch.
        # No native reader/semantic oracle is needed for this negative law.
        for era in ("legacy", "current"):
            with self.subTest(era=era):
                code, receipt = self.call(era=era, oracle=False, reader=False)
                self.assertEqual((code, receipt["status"]), (2, "BLOCKED"))
                self.assertEqual(receipt["source_era"], era)
                self.assertIn("RETIRED_SOURCE_ERA", receipt["reason"])
                self.assertEqual(receipt["files_written"], 0)
                self.assertFalse(list(self.output.rglob("*.sens")))

    def test_one_file_resolver_uses_current_ukr_and_rejects_ambiguous_w8(self):
        # Historical SID8 bytes are not a source of ratified D8 callability.
        migration = app.load_migrator()
        foundation = migration.load_foundation(ROOT / "knowledge/d1-d11-foundation.json")
        self.assertEqual(foundation["current_domains"], [f"D{i}" for i in range(1, 12)])
        self.assertEqual(len(foundation["domains"]["D10"]["residents"]), 1024)
        # D11 is a testing inventory: residency must not imply callability.
        self.assertEqual(len(foundation["domains"]["D11"]["residents"]), 43)
        my, upper, bridge = migration.build_three_pass_maps(
            foundation,
            ROOT / "crates/sens/src/domain_surface_registry_generated.rs",
            ROOT / "crates/sens/src/semantic_registry_generated.rs",
            ROOT / "crates/sens/src/semantic_registry.rs",
            ROOT / "crates/sens/src/eval/necessary_forms_generated.rs",
        )
        self.assertFalse(bridge)
        text7 = migration.build_text7(
            foundation, ROOT / "knowledge/d7-keyboard-v2-ratified.json")
        current = migration.Resolver(my, upper)
        original = "(перше-першого (сполучити (сполучити (як-є ()) (як-є ())) (як-є ())))\n"
        projected = migration.migrate_file(
            original, current, text7, source_surface="укр", codec="t5")
        self.assertTrue(projected.startswith("10 1000 00 "), projected)
        # Восьмибітне слово тут неоднозначне між SID8 та D8.
        # Його не можна прирівняти ні до викличного D8, ні до
        # математичних даних D24+. Точна відмова — W8-неоднозначність.
        self.assertEqual(
            app.ambiguous_eight_bit_atoms(migration, "(01001000 000)\n"),
            ["01001000"],
        )
        ambiguous_head = migration.Resolver(my, upper)
        with self.assertRaisesRegex(
            migration.MigrationError, r"ambiguous eight-bit SID8/D8 call head"
        ):
            migration.migrate_file(
                "(01001000 000)\n", ambiguous_head, text7,
                source_surface="укр", codec="t5")

    def test_preloaded_lisp_d9_resident_keeps_d7_identifier_without_callability(self):
        # The D9 table fixes identity but does not create a native call mechanism.
        # The current SENS reader preserves the lexical function as D7 words.
        migration = app.load_migrator()
        foundation = migration.load_foundation(ROOT / "knowledge/d1-d11-foundation.json")
        my, upper, _retired = migration.build_three_pass_maps(
            foundation,
            ROOT / "crates/sens/src/domain_surface_registry_generated.rs",
            ROOT / "crates/sens/src/semantic_registry_generated.rs",
            ROOT / "crates/sens/src/semantic_registry.rs",
            ROOT / "crates/sens/src/eval/necessary_forms_generated.rs",
        )
        text7 = migration.build_text7(
            foundation, ROOT / "knowledge/d7-keyboard-v2-ratified.json")
        program = "(модуль-відомий? (як-є зоря))\n"
        without = migration.Resolver(my, upper)
        without_words = migration.migrate_file(
            program, without, text7, codec="t5m", source_surface="укр")
        self.assertEqual(my["модуль-відомий?"], ("101010010", "D9"))
        self.assertNotIn("101010010", without_words.split())
        self.assertEqual(without_words.split()[1], "10")
        self.assertEqual(without.counts["pass4-text7-global"], 1)
        imported_source = (ROOT / "lib/knowledge.lisp").read_text(encoding="utf-8")
        forms = migration.Parser(migration.tokenize(
            migration.strip_comments(imported_source),
            source_surface="укр",
        )).parse_program()
        imported = migration.collect_global_bindings(
            forms, migration.Resolver(my, upper)
        )
        self.assertIn("модуль-відомий?", {name for name, _ in imported})
        with_preload = migration.Resolver(my, upper)
        words = migration.migrate_file(
            program, with_preload, text7, codec="t5m", source_surface="укр",
            imported_bindings=imported,
        )
        self.assertNotIn("101010010", words.split())
        self.assertEqual(with_preload.counts["pass4-text7-global"], 1)
        self.assertEqual(words, without_words)

    def test_reason_keeps_unification_as_lexical_d7_not_unadmitted_d9_call(self):
        # D9 ratification is retained, but native callability is not inferred.
        # The actual Lisp definition is resolved as contextual D7 by SENS.
        migration = app.load_migrator()
        foundation = migration.load_foundation(ROOT / "knowledge/d1-d11-foundation.json")
        my, upper, _retired = migration.build_three_pass_maps(
            foundation,
            ROOT / "crates/sens/src/domain_surface_registry_generated.rs",
            ROOT / "crates/sens/src/semantic_registry_generated.rs",
            ROOT / "crates/sens/src/semantic_registry.rs",
            ROOT / "crates/sens/src/eval/necessary_forms_generated.rs",
        )
        text7 = migration.build_text7(
            foundation, ROOT / "knowledge/d7-keyboard-v2-ratified.json")
        program = "(уніфікувати (як-є a) (як-є a) (як-є ()))\n"
        without = migration.Resolver(my, upper)
        words_without = migration.migrate_file(
            program, without, text7, codec="t5m", source_surface="укр",
        )
        self.assertEqual(my["уніфікувати"], ("101010000", "D9"))
        self.assertNotIn("101010000", words_without.split())
        self.assertEqual(words_without.split()[1], "10")
        self.assertEqual(without.counts["pass4-text7-global"], 1)
        source = (ROOT / "lib/unify.lisp").read_text(encoding="utf-8")
        forms = migration.Parser(migration.tokenize(
            migration.strip_comments(source), source_surface="укр"
        )).parse_program()
        binding = migration.collect_global_bindings(
            forms, migration.Resolver(my, upper)
        )
        self.assertIn("уніфікувати", {name for name, _ in binding})
        resolver = migration.Resolver(my, upper)
        words = migration.migrate_file(
            program, resolver, text7, codec="t5m",
            source_surface="укр", imported_bindings=binding,
        )
        self.assertNotIn("101010000", words.split())
        self.assertEqual(resolver.counts["pass4-text7-global"], 1)
        self.assertEqual(words, words_without)
        runner = (ROOT / "scripts/execute_changed_lisp_t5m.sh").read_text(encoding="utf-8")
        self.assertIn('binding_sources=(--binding-source lib/unify.lisp)', runner)
        self.assertIn('"${binding_sources[@]}"', runner)

    def test_real_unpaired_original_files_are_audited_not_converted(self):
        # These are tracked old files, not fabricated canaries or newly authored
        # snapshots. They include local binding, Text7 and machine-data issues.
        for old in ("benchmarks/closures.lisp", "benchmarks/parser.lisp",
                    "lib/machine/block.lisp"):
            with self.subTest(source=old):
                original = (ROOT / old).read_bytes()
                code, state = self.call(old, blob="HEAD", era="auto",
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
        code, state = self.call(dry=True)
        self.assertEqual((code, state["status"]), (2, "BLOCKED"))
        self.assertIn("observations differ", state["reason"])
        self.assertFalse(list(self.output.rglob("*.sens")))

    def test_legacy_t5_inspection_never_publishes_even_with_oracle(self):
        if not self.reader.is_file():
            self.fail("build the real Rust sens-trit opener before this test")
        code, state = self.call(dry=True)
        self.assertEqual(code, 0, state)
        self.assertEqual(state["status"], "VERIFIED_DRY_RUN")
        self.assertEqual(state["binary_bytes"], 20)
        self.assertEqual(state["syntax"], "PASS_D2_SYNTAX_ONLY")
        self.assertEqual(state["oracle"], "PASS_HISTORICAL_CURRENT")
        self.assertFalse(list(self.output.rglob("*.sens")))

        # Once the historical witness has passed, publishing it through the
        # obsolete Python T5 adapter must still be impossible.
        code, state = self.call()
        self.assertEqual((code, state["status"]), (2, "BLOCKED"))
        self.assertIn("LEGACY_T5_PUBLICATION_DISABLED", state["reason"])
        self.assertIn("migrate-one-to-sens.py", state["reason"])
        self.assertEqual((ROOT / SOURCE).read_bytes(), self.orig)
        self.assertFalse(list(self.output.rglob("*.sens")))

    def test_existing_symlink_is_rejected(self):
        fake = self.folder / "elsewhere"
        fake.mkdir()
        leaf = self.output / "tests/fixtures/migration-d4-selector-cohort"
        leaf.mkdir(parents=True)
        (leaf / "caar.sens").symlink_to(fake, target_is_directory=True)
        code, state = self.call(dry=True)
        self.assertEqual((code, state["status"]), (2, "BLOCKED"))

if __name__ == "__main__":
    unittest.main()
