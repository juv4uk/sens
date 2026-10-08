#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import subprocess
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"migrate-three-pass.py"
SPEC=importlib.util.spec_from_file_location("three_pass",SCRIPT)
assert SPEC and SPEC.loader
mod=importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name]=mod
SPEC.loader.exec_module(mod)

FOUNDATION=ROOT/"knowledge"/"d1-d9-foundation.json"
COVERAGE=ROOT/"knowledge"/"sens8-current-coverage-v1.json"
DOMAIN_SURFACES=ROOT/"crates"/"sens"/"src"/"domain_surface_registry_generated.rs"
SEMANTIC_GENERATED=ROOT/"crates"/"sens"/"src"/"semantic_registry_generated.rs"
SEMANTIC_REGISTRY=ROOT/"crates"/"sens"/"src"/"semantic_registry.rs"
NECESSARY=ROOT/"crates"/"sens"/"src"/"eval"/"necessary_forms_generated.rs"
HISTORICAL=ROOT/"contracts"/"core1-historical-sid-map.lisp"
TEXT7=ROOT/"crates"/"sens"/"src"/"text7_projection_generated.rs"

class ThreePassMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data=mod.load_foundation(FOUNDATION)
        cls.legacy,cls.my,cls.upper=mod.build_three_pass_maps(
            data,DOMAIN_SURFACES,SEMANTIC_GENERATED,SEMANTIC_REGISTRY,NECESSARY,HISTORICAL,
            COVERAGE
        )
        cls.text7=mod.build_text7(data,TEXT7)

    def migrate(self,source,source_era="legacy"):
        # Direct unit fixtures are historical unless a test explicitly asks
        # for current/auto semantics. Production CLI default is tested below.
        resolver=mod.Resolver(self.legacy,self.my,self.upper,source_era=source_era)
        return mod.migrate_file(source,resolver,self.text7),resolver

    def test_empty_list_is_compact_d3_empty(self):
        out,_=self.migrate("()\n")
        self.assertEqual(out,"000\n")

    def test_nonempty_list_uses_d2_structure(self):
        out,_=self.migrate("(CAR x)\n")
        self.assertTrue(out.startswith("10 100 00 "))
        self.assertTrue(out.endswith(" 01\n"))

    def test_pass1_legacy_sid8_car(self):
        out,resolver=self.migrate("(00000101 x)\n")
        self.assertTrue(out.startswith("10 100 00 "))
        self.assertEqual(resolver.counts["pass1-sens8"],1)

    def test_pass2_my_lisp_car(self):
        out,resolver=self.migrate("(car x)\n")
        self.assertTrue(out.startswith("10 100 00 "))
        self.assertEqual(resolver.counts["pass2-my-lisp"],1)

    def test_pass2_my_lisp_predicate_alias(self):
        out,resolver=self.migrate("(atom? x)\n")
        self.assertTrue(out.startswith("10 010 00 "))
        self.assertEqual(resolver.counts["pass2-my-lisp"],1)

    def test_pass2_def_normalizes_to_define(self):
        out,resolver=self.migrate("(def f (lambda (x) x))\n")
        self.assertTrue(out.startswith("10 0011 00 "))
        self.assertGreaterEqual(resolver.counts["pass2-my-lisp"],2)

    def test_owner_uk_define_and_lambda_have_same_candidate_wire_as_exact_heads(self):
        ukrainian="(визначити foo (функція (x) x))\n(foo так)\n"
        exact="(0011 foo (0010 (x) x))\n(foo 1)\n"
        uk_words,uk_resolver=self.migrate(ukrainian,source_era="auto")
        exact_words,_=self.migrate(exact,source_era="auto")
        self.assertEqual(uk_words,exact_words)
        self.assertEqual(uk_resolver.counts["pass4-text7-global"],1)
        self.assertTrue(all(1 <= len(w) <= 9 and set(w) <= {"0","1"}
                            for w in uk_words.split()))
        self.assertNotIn("foo",uk_words)
        self.assertNotIn("x",uk_words)


    def test_pass3_lisp15_car(self):
        out,resolver=self.migrate("(CAR x)\n")
        self.assertTrue(out.startswith("10 100 00 "))
        self.assertEqual(resolver.counts["pass3-lisp15"],1)

    def test_pass3_lisp15_arithmetic(self):
        out,resolver=self.migrate("(PLUS x y)\n")
        self.assertTrue(out.startswith("10 01010 00 "))
        self.assertEqual(resolver.counts["pass3-lisp15"],1)

    def test_comments_disappear(self):
        a,_=self.migrate("; top\n(CAR #| nested #| inner |# body |# x)\n")
        b,_=self.migrate("(CAR x)\n")
        self.assertEqual(a,b)

    def test_unknown_function_passes_through_verbatim(self):
        out,resolver=self.migrate("(totally-unknown-function x)\n")
        self.assertEqual(out,"10 totally-unknown-function 00 x 01\n")
        self.assertEqual(resolver.counts["passthrough-head"],1)

    def test_unresolved_sid8_blocks_instead_of_becoming_text(self):
        with self.assertRaisesRegex(mod.MigrationError,"legacy-unmapped SID8/Sens8"):
            self.migrate("(11111111 x)\n")

    def test_proven_old_print_sid8_and_surface_project_to_current_d8(self):
        for form,passname in (("(01001000 x)\n","pass1-sens8"),
                               ("(print x)\n","pass2-my-lisp")):
            out,resolver=self.migrate(form)
            self.assertTrue(out.startswith("10 11011011 00 "),form)
            self.assertEqual(resolver.counts[passname],1)

    def test_proven_lisp15_equal_is_current_exact_d8(self):
        out,resolver=self.migrate("(EQUAL a b)\n")
        self.assertTrue(out.startswith("10 11110111 00 "),out)
        self.assertEqual(resolver.counts["pass3-lisp15"],1)

    def test_one_exact_identity_d4_d8_d9_from_audited_legacy(self):
        for code,bits in (("00100010","11110111"),
                          ("00101111","1001"),
                          ("00111010","110011110"),
                          ("01001011","110101001")):
            with self.subTest(code=code):
                out,resolver=self.migrate(f"({code} x)\n")
                self.assertTrue(out.startswith(f"10 {bits} "),out)
                self.assertEqual(resolver.counts["pass1-sens8"],1)

    def test_ambiguous_or_compound_audited_successors_fail_closed(self):
        data=mod.load_foundation(FOUNDATION)
        approved=mod.parse_audited_legacy_successors(COVERAGE,data)
        self.assertNotIn("00001010",approved)  # MACRO + DEFINE, not one identity
        self.assertNotIn("00110111",approved)  # current D6 MAP or D8 MAP ambiguous
        self.assertNotIn("11111111",approved)  # historical unallocated
        self.assertEqual(approved["01001000"][:2],("11011011","D8"))
        # A historical identity cannot be silently passed off as current D8.
        with self.assertRaisesRegex(mod.MigrationError,"ambiguous"):
            self.migrate("(01001000 x)\n",source_era="auto")

    def test_old_functions_with_current_successors_move_by_semantic_role(self):
        cases=[
            ("(00100001 x)\n","0100","pass1-sens8"),   # NOT
            ("(00101000 x)\n","000000","pass1-sens8"), # LENGTH
            ("(00110111 f xs)\n","101000","pass1-sens8"), # MAP
            ("(00111001 f z xs)\n","101110","pass1-sens8"), # REDUCE
            ("(10011100 ((x 1)) x)\n","001000","pass1-sens8"), # LET
            ("(10011101 ((x 1)) x)\n","001001","pass1-sens8"), # LET*
        ]
        for source,bits,counter in cases:
            out,resolver=self.migrate(source)
            self.assertTrue(out.startswith(f"10 {bits} "),source)
            self.assertEqual(resolver.counts[counter],1,source)

    def test_my_lisp_functions_with_current_successors_are_not_legacy_unmapped(self):
        for source,bits in [
            ("(not? x)\n","0100"),
            ("(length xs)\n","000000"),
            ("(map f xs)\n","101000"),
            ("(reduce f z xs)\n","101110"),
            ("(let ((x 1)) x)\n","001000"),
            ("(let* ((x 1)) x)\n","001001"),
        ]:
            out,resolver=self.migrate(source)
            self.assertTrue(out.startswith(f"10 {bits} "),source)
            self.assertEqual(resolver.counts["pass2-my-lisp"],1,source)

    def test_d1_head_may_pass_but_d2_head_is_reserved_for_structure(self):
        out1,resolver1=self.migrate("(1 x)\n")
        self.assertEqual(out1,"10 1 00 x 01\n")
        self.assertEqual(resolver1.counts["passthrough-head"],1)
        with self.assertRaisesRegex(mod.MigrationError,"D2 word 10 is structural control only"):
            self.migrate("(10 x)\n")

    def test_d2_words_cannot_survive_as_ordinary_data(self):
        for word in ("00","01","10","11"):
            with self.assertRaisesRegex(mod.MigrationError,"structural control only"):
                self.migrate(f"(CONS {word} x)\n")

    def test_numeric_literal_passes_through_verbatim(self):
        out,_=self.migrate("(CAR 25)\n")
        self.assertEqual(out,"10 100 00 25 01\n")

    def test_quote_of_empty_is_quote_plus_000(self):
        out,_=self.migrate("'()\n")
        self.assertEqual(out,"10 001 00 000 01\n")

    def test_dotted_pair_uses_d2_dot_and_preserves_unknown_data(self):
        out,_=self.migrate("'(a . b)\n")
        self.assertEqual(out,"10 001 00 10 a 11 b 01 01\n")

    def test_known_structure_and_function_convert_while_unknown_data_stays_visible(self):
        out,_=self.migrate("(CONS x y)\n")
        self.assertEqual(out,"10 111 00 x 00 y 01\n")

    def test_all_emitted_structural_control_is_d2_and_empty_is_d3_value(self):
        out,_=self.migrate("(CONS () (a . b))\n")
        words=out.split()
        controls=[word for word in words if len(word)==2]
        self.assertTrue(controls)
        self.assertTrue(all(word in {"00","01","10","11"} for word in controls))
        self.assertIn("000",words)
        self.assertEqual(out.count("000"),1)

    def test_same_basename_gets_sens_extension_without_directory_collision(self):
        self.assertEqual(str(mod.sens_destination(Path("tasks.lisp"))), "tasks.sens")
        self.assertEqual(str(mod.sens_destination(Path("tasks/pending.lisp"))),
                         "tasks/pending.sens")
        self.assertEqual(str(mod.sens_destination(Path("lib/sse4.1.lisp"))),
                         "lib/sse4.1.sens")
        self.assertEqual(str(mod.sens_destination(Path("foo.lisp"))), "foo.sens")

    def test_legacy_unmapped_name_is_not_valid_t5_binary_output(self):
        projection,_ = self.migrate("(totally-unknown-function x)\n")
        with self.assertRaises(mod.SensT5Error):
            mod.encode_projection(projection)
        self.assertEqual(mod.decode_bytes(mod.encode_projection("000\n")), ["000"])

    def test_main_writes_actual_sens_bytes_and_blocks_leftover_names(self):
        with tempfile.TemporaryDirectory() as td:
            temp = Path(td)
            root = temp / "inputs"
            root.mkdir()
            (root / "tasks").mkdir()
            (root / "good.lisp").write_text("()\n", encoding="utf-8")
            (root / "tasks.lisp").write_text("()\n", encoding="utf-8")
            (root / "tasks" / "more.lisp").write_text("()\n", encoding="utf-8")
            (root / "unresolved.lisp").write_text(
                "(totally-unknown-function x)\n", encoding="utf-8"
            )
            out = temp / "artifacts"
            report = temp / "report.json"
            args = [
                sys.executable, str(SCRIPT), str(root), "--out", str(out),
                "--foundation", str(FOUNDATION),
                "--domain-surfaces", str(DOMAIN_SURFACES),
                "--semantic-generated", str(SEMANTIC_GENERATED),
                "--semantic-registry", str(SEMANTIC_REGISTRY),
                "--necessary-forms", str(NECESSARY),
                "--historical-map", str(HISTORICAL),
                "--text7", str(TEXT7),
                "--report", str(report),
            ]
            subprocess.run(args, check=True, capture_output=True, text=True)
            self.assertTrue((out / "good.sens").is_file())
            self.assertTrue((out / "tasks.sens").is_file())
            self.assertTrue((out / "tasks" / "more.sens").is_file())
            self.assertFalse((out / "unresolved.sens").exists())
            self.assertFalse((out / "good").exists())
            self.assertFalse((out / "good.lisp").exists())
            self.assertEqual(mod.decode_bytes((out / "good.sens").read_bytes()),
                             ["000"])
            self.assertEqual((root / "good.lisp").read_text(), "()\n")
            result = json.loads(report.read_text())
            self.assertEqual(result["summary"]["files_written"], 3)
            self.assertEqual(result["summary"]["files_blocked"], 1)
            self.assertTrue(result["file_format"]["physical"].startswith("binary"))
            self.assertEqual(result["naming_law"].split(" -> ")[1].split(";")[0],
                             "OUT/name.sens")
            # Never silently overwrite the exact .sens target on rerun.
            again = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(again.returncode, 2)
            self.assertEqual((out / "good.sens").read_bytes(),
                             mod.encode_projection("000\n"))
            # Explicitly return to source/manifest workflow before a rerun.
            self.assertTrue((root / "tasks.lisp").exists())

    def test_dry_run_produces_report_without_any_binary_file(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            src = base / "in"
            src.mkdir()
            (src / "one.lisp").write_text("()\n", encoding="utf-8")
            dst = base / "out"
            report = base / "report.json"
            process = subprocess.run([
                sys.executable, str(SCRIPT), str(src),
                "--out", str(dst), "--foundation", str(FOUNDATION),
                "--domain-surfaces", str(DOMAIN_SURFACES),
                "--semantic-generated", str(SEMANTIC_GENERATED),
                "--semantic-registry", str(SEMANTIC_REGISTRY),
                "--necessary-forms", str(NECESSARY),
                "--historical-map", str(HISTORICAL),
                "--text7", str(TEXT7), "--report", str(report), "--dry-run",
            ], capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertFalse(dst.exists())
            state = json.loads(report.read_text())
            self.assertEqual(state["summary"]["files_would_write"], 1)
            self.assertEqual(state["summary"]["files_written"], 0)


    def test_w8_source_era_is_explicit_and_never_guessed(self):
        # Same W8 word is historical CAR in SID8 but a distinct ratified D8
        # resident today; the CLI must never silently choose one.
        authority = mod.load_foundation(ROOT / "knowledge" / "d1-d9-foundation.json")
        d8 = authority["domains"]["D8"]["residents"]
        self.assertIn("00000101", d8)
        source = "(00000101 ())\\n".replace("\\n", "\n")
        with self.assertRaisesRegex(mod.MigrationError, "ambiguous W8 executable"):
            mod.migrate_file(
                source, mod.Resolver(self.legacy, self.my, self.upper,
                                     source_era="auto", admitted_d8=d8),
                self.text7,
            )
        legacy = mod.Resolver(self.legacy, self.my, self.upper, source_era="legacy")
        self.assertEqual(mod.migrate_file(source, legacy, self.text7),
                         "10 100 00 000 01\n")
        current = mod.Resolver(self.legacy, self.my, self.upper,
                               source_era="current", admitted_d8=d8)
        self.assertEqual(mod.migrate_file(source, current, self.text7),
                         "10 00000101 00 000 01\n")
        self.assertEqual(current.counts["already-exact"], 1)
        with self.assertRaisesRegex(mod.MigrationError, "owner-ratified D8"):
            mod.Resolver(self.legacy, self.my, self.upper, source_era="current")

    def test_single_lisp_file_cli_and_w8_current_authority(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "one.lisp"
            original = "(00000101 ())\n"
            source.write_text(original, encoding="utf-8")
            def run(era, foundation):
                dst = base / ("out-" + era)
                report = base / (era + ".json")
                command = [
                    sys.executable, str(SCRIPT), str(source),
                    "--out", str(dst), "--foundation", str(foundation),
                    "--domain-surfaces", str(DOMAIN_SURFACES),
                    "--semantic-generated", str(SEMANTIC_GENERATED),
                    "--semantic-registry", str(SEMANTIC_REGISTRY),
                    "--necessary-forms", str(NECESSARY),
                    "--historical-map", str(HISTORICAL),
                    "--text7", str(TEXT7),
                    "--report", str(report), "--source-era", era,
                ]
                process = subprocess.run(command, capture_output=True, text=True)
                return process, dst, json.loads(report.read_text(encoding="utf-8"))
            current_foundation = ROOT / "knowledge" / "d1-d9-foundation.json"
            blocked, blocked_out, blocked_report = run("auto", current_foundation)
            self.assertEqual(blocked.returncode, 2, blocked.stderr)
            self.assertEqual(blocked_report["summary"]["files_seen"], 1)
            self.assertEqual(blocked_report["summary"]["files_blocked"], 1)
            self.assertIn("ambiguous W8", blocked_report["files"][0]["reason"])
            self.assertFalse((blocked_out / "one.sens").exists())
            legacy, legacy_out, legacy_report = run("legacy", FOUNDATION)
            self.assertEqual(legacy.returncode, 0, legacy.stderr)
            self.assertEqual(mod.decode_bytes((legacy_out / "one.sens").read_bytes()),
                             ["10", "100", "00", "000", "01"])
            current, current_out, current_report = run("current", current_foundation)
            self.assertEqual(current.returncode, 0, current.stderr)
            binary = current_out / "one.sens"
            self.assertEqual(mod.decode_bytes(binary.read_bytes()),
                             ["10", "00000101", "00", "000", "01"])
            self.assertEqual(current_report["summary"]["files_seen"], 1)
            self.assertEqual(current_report["summary"]["files_written"], 1)
            self.assertEqual(current_report["source_era"], "current")
            self.assertEqual(source.read_text(encoding="utf-8"), original)
            again, _, _ = run("current", current_foundation)
            self.assertEqual(again.returncode, 2)  # write-new-only never clobbers


    def test_unpaired_only_ignores_preexisting_sens_pairs(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "src"
            source.mkdir()
            (source / "old.lisp").write_text("()\\n".replace("\\n", "\n"), encoding="utf-8")
            (source / "paired.lisp").write_text("()\\n".replace("\\n", "\n"), encoding="utf-8")
            already = mod.encode_projection("000")
            (source / "paired.sens").write_bytes(already)
            out = base / "mirror"
            report = base / "report.json"
            result = subprocess.run([
                sys.executable, str(SCRIPT), str(source),
                "--out", str(out), "--foundation", str(FOUNDATION),
                "--domain-surfaces", str(DOMAIN_SURFACES),
                "--semantic-generated", str(SEMANTIC_GENERATED),
                "--semantic-registry", str(SEMANTIC_REGISTRY),
                "--necessary-forms", str(NECESSARY),
                "--historical-map", str(HISTORICAL),
                "--text7", str(TEXT7), "--report", str(report),
                "--source-era", "legacy", "--unpaired-only",
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((out / "old.sens").read_bytes(), already)
            self.assertFalse((out / "paired.sens").exists())
            self.assertEqual((source / "paired.sens").read_bytes(), already)
            self.assertEqual((source / "old.lisp").read_text(), "()\n")
            summary = json.loads(report.read_text())
            self.assertTrue(summary["only_unpaired"])
            self.assertEqual(summary["skipped_paired_paths"], ["paired.lisp"])
            self.assertEqual(summary["summary"]["files_seen"], 1)
            self.assertEqual(summary["summary"]["files_skipped_paired"], 1)
            self.assertEqual(summary["summary"]["files_written"], 1)


    def test_minimal_cli_defaults_to_current_ratified_foundation(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "old.lisp"
            source.write_text("()\n", encoding="utf-8")
            out = base / "mirror"
            done = subprocess.run(
                [sys.executable, str(SCRIPT), str(source), "--out", str(out)],
                cwd=base, text=True, capture_output=True,
            )
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertEqual((out / "old.sens").read_bytes(),
                             mod.encode_projection("000"))
            report = base / "mirror.report.json"
            self.assertTrue(report.is_file())
            state = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(state["summary"]["files_written"], 1)
            self.assertEqual(state["summary"]["files_seen"], 1)
            self.assertEqual(source.read_text(), "()\n")


    def test_default_source_era_blocks_ambiguous_w8_without_guessing(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "ambiguous.lisp"
            source.write_text("(00000101 ())\n", encoding="utf-8")
            out = base / "mirror"
            report = base / "report.json"
            process = subprocess.run([
                sys.executable, str(SCRIPT), str(source),
                "--out", str(out),
                "--report", str(report),
                "--foundation", str(ROOT / "knowledge" / "d1-d9-foundation.json"),
                "--domain-surfaces", str(DOMAIN_SURFACES),
                "--semantic-generated", str(SEMANTIC_GENERATED),
                "--semantic-registry", str(SEMANTIC_REGISTRY),
                "--necessary-forms", str(NECESSARY),
                "--historical-map", str(HISTORICAL),
                "--text7", str(TEXT7),
            ], capture_output=True, text=True)
            self.assertEqual(process.returncode, 2, process.stderr)
            self.assertFalse((out / "ambiguous.sens").exists())
            state = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(state["source_era"], "auto")
            self.assertEqual(state["summary"]["files_blocked"], 1)
            self.assertIn("ambiguous W8", state["files"][0]["reason"])



    def test_global_text7_call_head_uses_same_frame_as_define_target(self):
        # Use ratified D4 identities; W8 provenance is tested independently.
        source = (
            "(0011 foo\n"
            "  (0010 ()\n"
            "    1))\n"
            "(foo)\n"
        )
        projection,resolver=self.migrate(source)
        frame=mod.frame_text7(
            mod.text7_encode("foo",self.text7,mod.Tok("ATOM","foo",0)),
            mod.Tok("ATOM","foo",0),
        )
        frame_text=" ".join(frame)
        self.assertIn("foo", resolver.global_binding_words, f"global DEFINE collection failed: {projection!r}")
        self.assertGreaterEqual(
            projection.count(frame_text), 2,
            f"frame={frame_text!r}; projection={projection!r}; globals={resolver.global_binding_words!r}",
        )
        self.assertEqual(resolver.counts["pass4-text7-global"],1)
        self.assertTrue(all(set(word) <= {"0","1"} for word in projection.split()))
        payload=mod.encode_projection(projection)
        self.assertEqual(mod.decode_bytes(payload),projection.split())


    def test_real_machine_block_closes_all_global_and_local_symbolic_words(self):
        source=(ROOT/"lib"/"machine"/"block.lisp").read_text(encoding="utf-8")
        projection,resolver=self.migrate(source)
        words=projection.split()
        self.assertTrue(words)
        self.assertTrue(
            all(set(word) <= {"0","1"} for word in words),
            "the real machine-block source must reach an all-binary candidate",
        )
        self.assertEqual(resolver.counts["pass1-sens8"],17)

        for name in (
            "machine-block",
            "machine-block-empty",
            "machine-block-one",
            "machine-block-append",
            "machine-block-concat",
            "machine-block-forms",
        ):
            frame=mod.frame_text7(
                mod.text7_encode(name,self.text7,mod.Tok("ATOM",name,0)),
                mod.Tok("ATOM",name,0),
            )
            self.assertIn(
                " ".join(frame),
                projection,
                f"missing canonical global Text7 frame for {name}",
            )

        forms_frame=mod.frame_text7(
            mod.text7_encode("forms",self.text7,mod.Tok("ATOM","forms",0)),
            mod.Tok("ATOM","forms",0),
        )
        self.assertGreaterEqual(
            projection.count(" ".join(forms_frame)),
            2,
            "lambda binder and local reference must share one Text7 binding frame",
        )

        payload=mod.encode_projection(projection)
        self.assertEqual(mod.decode_bytes(payload),words)
        self.assertTrue(payload, "physical T5 candidate must contain bytes")



    def test_let_and_let_star_bindings_use_contextual_text7_without_treating_binding_lists_as_calls(self):
        for source, head, expected_env in (
            ("(let ((x 1)) x)\n", "001000", 1),
            ("(let* ((x 1) (y x)) y)\n", "001001", 1),
        ):
            projection, resolver = self.migrate(source)
            words = projection.split()
            self.assertIn(head, words)
            x_frame = " ".join(
                mod.frame_text7(
                    mod.text7_encode("x", self.text7, mod.Tok("ATOM", "x", 0)),
                    mod.Tok("ATOM", "x", 0),
                )
            )
            self.assertIn(x_frame, projection)
            self.assertEqual(resolver.counts["pass2-my-lisp"], expected_env)
            self.assertNotIn(" x ", " " + projection + " ")

    def test_machine_block_local_callable_shadows_builtin_surface(self):
        # Exercise lexical shadowing, not historical W8 lookup.
        source = (
            "(0011 first\n"
            "  (0010 (first)\n"
            "    (first)))\n"
        )
        projection,resolver=self.migrate(source)
        words=projection.split()
        self.assertTrue(
            all(set(word) <= {"0","1"} for word in words),
            f"nonbinary words in {words!r}; globals={resolver.global_binding_words!r}",
        )
        first_frame=mod.frame_text7(
            mod.text7_encode("first",self.text7,mod.Tok("ATOM","first",0)),
            mod.Tok("ATOM","first",0),
        )
        self.assertGreaterEqual(projection.count(" ".join(first_frame)),2)


if __name__=="__main__":
    unittest.main()