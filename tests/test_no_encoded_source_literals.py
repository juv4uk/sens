from __future__ import annotations

import hashlib
import importlib.util
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "no_encoded_source_literals", ROOT / "scripts" / "check_no_encoded_source_literals.py"
)
assert SPEC is not None and SPEC.loader is not None
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class EncodedSourceLiteralTests(unittest.TestCase):
    def test_machine_encoder_has_no_numeric_source_literals(self):
        # Суто лексичний свідок; семантику кодувальника перевіряють SENS-тести.
        path = ROOT / "lib/machine/encoding/x86-64.lisp"
        source = path.read_text(encoding="utf-8")
        self.assertEqual(
            CHECK.find_forbidden_literals(source, path="lib/machine/encoding/x86-64.lisp"),
            [],
        )

    def test_function_index_generator_has_no_numeric_source_literals(self):
        # Генератор довідника також є живою українською Lisp-програмою.
        path = ROOT / "scripts/generate-functions-md.lisp"
        source = path.read_text(encoding="utf-8")
        self.assertEqual(
            CHECK.find_forbidden_literals(source, path="scripts/generate-functions-md.lisp"),
            [],
            "проєкція генератора не має числових голів або літералів",
        )

    def test_racket_boot_core_has_no_numeric_source_literals(self):
        # Bootstrap є живою проєкцією; корені чисел названі, приріст — D5-додавання.
        path = ROOT / "racket/boot/core.lisp"
        source = path.read_text(encoding="utf-8")
        self.assertEqual(
            CHECK.find_forbidden_literals(source, path="racket/boot/core.lisp"),
            [],
            "проєкція Racket bootstrap не має числових голів або літералів",
        )

    def test_guard_reference_ranks_are_named_not_numeric(self):
        # Порядок станів збережено; числові ранги мають іменовані D24+ значення.
        path = ROOT / "knowledge/guard-reference.lisp"
        source = path.read_text(encoding="utf-8")
        self.assertEqual(
            CHECK.find_forbidden_literals(source, path="knowledge/guard-reference.lisp"),
            [],
            "проєкція довідника гвардії не має числових голів або літералів",
        )
        for fragment in (
            "((тотожне? стан (як-є confirmed)) гвардія-число-чотири)",
            "((тотожне? стан (як-є partial)) гвардія-число-три)",
            "((тотожне? стан (як-є unresolved)) гвардія-число-два)",
            "((тотожне? стан (як-є broken)) гвардія-число-один)",
            "(так гвардія-число-нуль)",
        ):
            self.assertIn(fragment, source)

    def test_domain_bitness_law_has_no_numeric_source_literals(self):
        # Координати драбини перевіряються як точні текстові ключі, не числа.
        path = ROOT / "scripts/check-domain-bitness-laws.lisp"
        source = path.read_text(encoding="utf-8")
        self.assertEqual(
            CHECK.find_forbidden_literals(source, path="scripts/check-domain-bitness-laws.lisp"),
            [],
            "закон ширини доменів не має числових голів або літералів",
        )

    def test_domain_table_reader_and_logic_laws_have_no_numeric_literals(self):
        # Розміри таблиць та математичні свідки називаються в самій SENS.
        for relative in (
            "scripts/check-domain-table-readable.lisp",
            "scripts/check-domain-logic-laws.lisp",
        ):
            with self.subTest(path=relative):
                path = ROOT / relative
                source = path.read_text(encoding="utf-8")
                self.assertEqual(
                    CHECK.find_forbidden_literals(source, path=relative),
                    [],
                    f"проєкція {relative} не має числових голів або літералів",
                )

    def test_program_symbol_table_has_no_numeric_source_literals(self):
        # Живий український витягувач не містить числових атомів.
        path = ROOT / "scripts/program-symbol-table.lisp"
        source = path.read_text(encoding="utf-8")
        self.assertEqual(
            CHECK.find_forbidden_literals(source, path="scripts/program-symbol-table.lisp"),
            [],
            "проєкція витягувача символів не має цифрових голів або літералів",
        )

    def test_machine_effect_live_source_uses_named_coordinates(self):
        # Лексична перевірка; обчислення маршруту перевіряють нативні тести SENS.
        path = ROOT / "lib/machine/lowering/semantic-effects.lisp"
        source = path.read_text(encoding="utf-8")
        self.assertEqual(
            CHECK.find_forbidden_literals(
                source, path="lib/machine/lowering/semantic-effects.lisp"
            ),
            [],
            "виконувана проєкція машинного зниження не має числових атомів",
        )

    def test_unquoted_numeric_literals_are_rejected(self):
        found = CHECK.find_forbidden_literals("(сума 235 2.1564)\n")
        self.assertEqual(
            [(item.token, item.reason) for item in found],
            [("235", "numeric source literal"), ("2.1564", "numeric source literal")],
        )
        # Quotation prevents execution, but does not make numeric source tokens canonical.
        quoted = CHECK.find_forbidden_literals("(сума (як-є (235 2.1564)))\n")
        self.assertEqual(
            [(item.token, item.reason) for item in quoted],
            [("235", "numeric source literal"), ("2.1564", "numeric source literal")],
        )
        self.assertEqual(
            [item.token for item in CHECK.find_forbidden_literals("(як-є 235)\n")],
            ["235"],
        )

    def test_d24_human_projection_fixture_contains_no_encoded_domain_words(self):
        fixture = ROOT / "tests" / "semantic" / "ukr-d24-existing-functions.lisp"
        source = fixture.read_text(encoding="utf-8")
        self.assertEqual(CHECK.find_forbidden_literals(source, path=fixture), [])

    def test_lisp_projection_names_are_allowed(self):
        source = '(cond ((string-empty? "") (not? (string-empty? "а"))) (T NIL))\n'
        self.assertEqual(CHECK.find_forbidden_literals(source), [])

    def test_typed_domain_wire_words_are_rejected(self):
        source = "(сума #d24:000000000000000000000010 #d1:1 #b101 #q2:1011/1)\n"
        found = CHECK.find_forbidden_literals(source)
        self.assertEqual([item.token for item in found], [
            "#d24:000000000000000000000010", "#d1:1", "#b101", "#q2:1011/1",
        ])

    def test_numeric_call_head_is_rejected_as_encoded_operation(self):
        found = CHECK.find_forbidden_literals("(110 (аргумент))\n")
        self.assertEqual([item.token for item in found], ["110"])

    def test_quote_data_is_not_a_call_but_numeric_tokens_are_still_forbidden(self):
        source = (
            "(визначити x (як-є (1 2 3)))\n"
            "(визначити y (як-є (1 2 . 3)))\n"
            "(визначити z (як-є ((110 a) (1 b))))\n"
        )
        self.assertEqual(
            [item.token for item in CHECK.find_forbidden_literals(source)],
            ["1", "2", "3", "1", "2", "3", "110", "1"],
        )

    def test_quote_scope_keeps_real_numeric_heads_forbidden(self):
        source = "(список (як-є (1 2 3)) (110 (аргумент)))\n"
        self.assertEqual(
            [item.token for item in CHECK.find_forbidden_literals(source)],
            ["1", "2", "3", "110"],
        )
        # A legacy numeric QUOTE head and quoted numeric atoms are all forbidden literals.
        self.assertEqual(
            [item.token for item in CHECK.find_forbidden_literals("(001 (1 2 3))\n")],
            ["001", "1", "2", "3"],
        )
        # Only the single QUOTE operand is data; the extra numeric operand is still invalid.
        self.assertEqual(
            [item.token for item in CHECK.find_forbidden_literals(
                "(як-є (1 2 3) (110 unexpected))\n"
            )],
            ["1", "2", "3", "110"],
        )

    def test_legacy_signature_table_keys_are_metadata_not_calls(self):
        row = (
            '  (00001100 (kind builtin) (arity (at-least 0)) '
            '(surfaces stable) (sig "(+ number ...)") (doc "Sum all arguments"))\n'
        )
        source = "lib/surface/function-signatures.lisp"
        self.assertEqual(CHECK.find_forbidden_literals(row, path=source), [])
        self.assertEqual(
            [v.token for v in CHECK.find_forbidden_literals(row, path="lib/core.lisp")],
            ["00001100", "0"],
        )
        self.assertEqual(
            [v.token for v in CHECK.find_forbidden_literals("(00001100 x)\n", path=source)],
            ["00001100"],
        )
        malformed = row.replace("(kind builtin)", "(kind unknown)")
        self.assertEqual(
            [v.token for v in CHECK.find_forbidden_literals(malformed, path=source)],
            ["00001100", "0"],
        )
        tagged = row + "(сума #d1:1)\n"
        self.assertEqual(
            [v.token for v in CHECK.find_forbidden_literals(tagged, path=source)],
            ["#d1:1"],
        )

    def test_domain_table_key_exemption_is_exact_and_fail_closed(self):
        row = (
            '  (11010 (ук менше?) (укр менше?) (san hīna) '
            '(en lessp?) (LISP LESSP) (sym "менше?"))\n'
        )
        self.assertEqual(CHECK.find_forbidden_literals(row, path="lib/domains/d5.lisp"), [])
        # The same payload elsewhere is still a forbidden operation head.
        found = CHECK.find_forbidden_literals(row, path="lib/example.lisp")
        self.assertEqual([item.token for item in found], ["11010"])
        # Wrong width, malformed row, or another numeric call is not exempt.
        wrong_width = row.replace("(11010 ", "(1101 ", 1)
        self.assertEqual(
            [item.token for item in CHECK.find_forbidden_literals(
                wrong_width, path="lib/domains/d5.lisp"
            )],
            ["1101"],
        )
        nested_call = row + "(110 x)\n"
        self.assertEqual(
            [item.token for item in CHECK.find_forbidden_literals(
                nested_call, path="lib/domains/d5.lisp"
            )],
            ["110"],
        )

    def test_domain_table_exemption_never_allows_encoded_wire_words(self):
        row = (
            '  (11010 (ук менше?) (укр менше?) (san hīna) '
            '(en lessp?) (LISP #d5:11010) (sym "менше?"))\n'
        )
        found = CHECK.find_forbidden_literals(row, path="lib/domains/d5.lisp")
        self.assertEqual(
            [(item.token, item.reason) for item in found],
            [("#d5:11010", "encoded domain/wire word")],
        )

    def test_comments_and_strings_do_not_create_false_positives(self):
        source = '; приклад (#d1:1) та (110 x)\n(пояснити "#d24:10 (110 x)")\n'
        self.assertEqual(CHECK.find_forbidden_literals(source), [])

    def test_diff_parser_checks_every_added_lisp_path(self):
        diff = """diff --git a/lib/a.lisp b/lib/a.lisp
--- a/lib/a.lisp
+++ b/lib/a.lisp
@@ -1,0 +2 @@
+(110 x)
diff --git a/tests/b.lisp b/tests/b.lisp
--- a/tests/b.lisp
+++ b/tests/b.lisp
@@ -0,0 +1 @@
+(сума 235)
"""
        rows = CHECK.added_lisp_lines_from_diff(diff)
        self.assertEqual(rows, [("lib/a.lisp", 2, "(110 x)"), ("tests/b.lisp", 1, "(сума 235)")])

    def test_repository_gate_detects_literal_added_in_any_lisp_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
            (root / "base.lisp").write_text("(сума 235)\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "base.lisp"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "base"], check=True)
            base_sha = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"], check=True,
                text=True, encoding="utf-8", stdout=subprocess.PIPE,
            ).stdout.strip()

            def run_guard(*args: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [
                        "python3", str(ROOT / "scripts" / "check_no_encoded_source_literals.py"),
                        "--root", str(root), *args,
                    ],
                    cwd=ROOT, check=False, text=True, encoding="utf-8",
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )

            elsewhere = root / "deep" / "new.lisp"
            elsewhere.parent.mkdir()
            elsewhere.write_text("(110 x)\n", encoding="utf-8")
            untracked_result = run_guard()
            self.assertEqual(untracked_result.returncode, 1, untracked_result.stderr)
            self.assertIn("deep/new.lisp:1:2", untracked_result.stderr)
            self.assertIn("numeric function/opcode head: 110", untracked_result.stderr)

            subprocess.run(["git", "-C", str(root), "add", "deep/new.lisp"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "bad literal"], check=True)
            committed_result = run_guard("--base", base_sha)
            self.assertEqual(committed_result.returncode, 1, committed_result.stderr)

            elsewhere.write_text("(сума сума)\n", encoding="utf-8")
            valid_result = run_guard()
            self.assertEqual(valid_result.returncode, 0, valid_result.stderr)
            self.assertIn("SOURCE_ENCODED_LITERAL_GUARD_PASS", valid_result.stdout)


    def test_projected_head_preserves_existing_d24_but_not_new_wire_words(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
            subprocess.run(["git", "-C", str(root), "config",
                            "user.email", "test@example.invalid"], check=True)
            path = root / "lib/meta-eval.lisp"
            path.parent.mkdir(parents=True)
            zero = "#d24:000000000000000000000000"
            one = "#d24:000000000000000000000001"

            def commit(message: str, source: str) -> None:
                path.write_text(source, encoding="utf-8")
                subprocess.run(["git", "-C", str(root), "add",
                                "lib/meta-eval.lisp"], check=True)
                subprocess.run(["git", "-C", str(root), "commit", "-qm", message], check=True)

            commit("base", f"((010 params) {zero})\n")
            base = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                check=True, text=True, stdout=subprocess.PIPE,
            ).stdout.strip()
            commit("ukr surface", f"((атом? params) {zero})\n")
            added, findings = CHECK.check(root, base)
            self.assertEqual(added, 1)
            self.assertEqual(findings, [], findings)

            commit("new word", f"((атом? params) {zero} {one})\n")
            _, findings = CHECK.check(root, base)
            self.assertIn(one, [item.token for _, item in findings])

            commit("mutated word", f"((атом? params) {one})\n")
            _, findings = CHECK.check(root, base)
            self.assertIn(one, [item.token for _, item in findings])

            commit("numeric head", f"((110 params) {zero})\n")
            _, findings = CHECK.check(root, base)
            self.assertIn("110", [item.token for _, item in findings])

    def test_base_multiline_quoted_token_cannot_exempt_new_code(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
            subprocess.run(["git", "-C", str(root), "config",
                            "user.email", "test@example.invalid"], check=True)
            path = root / "source.lisp"
            token = "#d24:000000000000000000000001"
            path.write_text(f'(показати "рядок\n{token}")\n', encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "source.lisp"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "base"], check=True)
            base = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                check=True, text=True, stdout=subprocess.PIPE,
            ).stdout.strip()
            path.write_text(f'(показати "рядок")\n(сума {token})\n', encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "source.lisp"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "new code"], check=True)
            _, findings = CHECK.check(root, base)
            self.assertIn(token, [item.token for _, item in findings])


    def test_repository_gate_accepts_domain_rows_but_rejects_numeric_calls(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
            subprocess.run(
                ["git", "-C", str(root), "config", "user.email", "test@example.invalid"],
                check=True,
            )
            domain = root / "lib/domains/d5.lisp"
            domain.parent.mkdir(parents=True)
            domain.write_text("(domain-table-1\n)\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "lib/domains/d5.lisp"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "base"], check=True)
            base_sha = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"], check=True,
                text=True, encoding="utf-8", stdout=subprocess.PIPE,
            ).stdout.strip()

            row = (
                '  (11010 (ук менше?) (укр менше?) (san hīna) '
                '(en lessp?) (LISP LESSP) (sym "менше?"))\n'
            )
            domain.write_text("(domain-table-1\n" + row + ")\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "lib/domains/d5.lisp"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "domain row"], check=True)

            def run_guard():
                return subprocess.run(
                    [
                        "python3", str(ROOT / "scripts" / "check_no_encoded_source_literals.py"),
                        "--root", str(root), "--base", base_sha,
                    ],
                    cwd=ROOT, check=False, text=True, encoding="utf-8",
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )

            accepted = run_guard()
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            self.assertIn("SOURCE_ENCODED_LITERAL_GUARD_PASS", accepted.stdout)

            domain.write_text(domain.read_text(encoding="utf-8") + "(110 x)\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "lib/domains/d5.lisp"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "numeric call regression"], check=True)
            rejected = run_guard()
            self.assertEqual(rejected.returncode, 1, rejected.stderr)
            self.assertIn("numeric function/opcode head: 110", rejected.stderr)

    def test_repository_gate_checks_base_diff_without_a_merge_base(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
            subprocess.run(
                ["git", "-C", str(root), "config", "user.email", "test@example.invalid"],
                check=True,
            )
            (root / "base.lisp").write_text("(сума 235)\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "base.lisp"], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "base"], check=True)
            base_sha = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"], check=True,
                text=True, encoding="utf-8", stdout=subprocess.PIPE,
            ).stdout.strip()

            (root / "new.lisp").write_text("(110 x)\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "new.lisp"], check=True)
            tree = subprocess.run(
                ["git", "-C", str(root), "write-tree"], check=True,
                text=True, encoding="utf-8", stdout=subprocess.PIPE,
            ).stdout.strip()
            unrelated_head = subprocess.run(
                ["git", "-C", str(root), "commit-tree", tree, "-m", "unrelated root"],
                check=True, text=True, encoding="utf-8", stdout=subprocess.PIPE,
            ).stdout.strip()
            subprocess.run(
                ["git", "-C", str(root), "update-ref", "HEAD", unrelated_head],
                check=True,
            )

            result = subprocess.run(
                [
                    "python3", str(ROOT / "scripts" / "check_no_encoded_source_literals.py"),
                    "--root", str(root), "--base", base_sha,
                ],
                cwd=ROOT, check=False, text=True, encoding="utf-8",
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("new.lisp:1:2", result.stderr)
            self.assertIn("numeric function/opcode head: 110", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)


class ResearchBatchUkrProjectionTests(unittest.TestCase):
    """D9/D10 research programs use full Ukrainian peers for exact D3/D4 heads."""

    D10 = ROOT / "research" / "d10-queue-sortcar-mapinto-batch-2026-10-17.lisp"
    D9 = ROOT / "research" / "d9-map-vec-list-batch-2026-10-17.lisp"
    D3 = ROOT / "lib" / "domains" / "d3.lisp"
    D4 = ROOT / "lib" / "domains" / "d4.lisp"
    def _assert_row(self, path: Path, bits: str, ukr: str, english: str, lisp_name: str):
        rows = [
            line for line in path.read_text(encoding="utf-8").splitlines()
            if re.match(rf"^\s*\({re.escape(bits)}\s", line)
        ]
        self.assertEqual(len(rows), 1, f"{bits}: exact-width row must be unique")
        self.assertIn(f"(укр {ukr})", rows[0])
        self.assertIn(f"(en {english})", rows[0])
        self.assertIn(f"(LISP {lisp_name})", rows[0])

    def test_d9_d10_use_ratified_ukr_heads_without_encoded_literals(self):
        # Перевіряємо поточні джерела та чинний доменний закон, а не
        # історичний SHA і сталу кількість викликів після міграцій.
        for bits, ukr, english, lisp_name in (
            ("011", "решта", "cdr", "CDR"),
            ("110", "за-умовою", "cond", "COND"),
        ):
            self._assert_row(self.D3, bits, ukr, english, lisp_name)
        for bits, ukr, english, lisp_name in (
            ("0011", "визначити", "define", "DEFINE"),
            ("0010", "функція", "lambda", "LAMBDA"),
            ("0100", "хибне?", "not?", "NOT"),
            ("0101", "порожній?", "null?", "NULL"),
        ):
            self._assert_row(self.D4, bits, ukr, english, lisp_name)

        for path in (self.D10, self.D9):
            source = path.read_text(encoding="utf-8")
            self.assertIn("(визначити ", source, str(path))
            self.assertIn("(функція ", source, str(path))
            self.assertEqual(
                CHECK.find_forbidden_literals(source, path=str(path.relative_to(ROOT))),
                [],
                str(path),
            )

    def test_reintroduced_binary_call_head_is_detected(self):
        # Негативний контроль відтворює саме заборонений регрес:
        # викличну українську голову замінили сирим словом домену.
        for path in (self.D10, self.D9):
            source = path.read_text(encoding="utf-8")
            mutant = source.replace("(визначити ", "(0011 ", 1)
            self.assertNotEqual(mutant, source)
            self.assertTrue(
                CHECK.find_forbidden_literals(mutant, path=str(path.relative_to(ROOT))),
                str(path),
            )

    def test_batch_consumers_find_projected_or_exact_source_heads(self):
        for name in ("apply-d10-queue-sortcar-mapinto-batch.py", "apply-d9-map-vec-list-batch.py"):
            source = (ROOT / "scripts" / name).read_text(encoding="utf-8")
            self.assertIn("(?:0011|визначити)", source)
            self.assertNotIn('body.find("(0011")', source)
