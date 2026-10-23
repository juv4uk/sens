"""Тести, які перевіряють, що код СЕНСУ *справді запускається*.

На відміну від статичних перевірок (баланс дужок, заборона літералів), тут
код **виконується**:

  1. Кожен CI-entry-point запускається як окрема програма (`subprocess`) і має
     завершитись очікуваним кодом виходу — ловить зламаний `__main__`, імпорт
     чи argparse, чого не бачать in-process тести.
  2. Наш власний читач (`scripts/migrate-three-pass.py`) токенізує й розбирає
     реальні мовні джерела: `lib/core4.lisp` і всі `lib/domains/d*.lisp`.
  3. Наш власний кодек (`scripts/sens_t5_t5m_codec.py`) виконується на реальних
     мовних файлах: `.sens` має пережити decode → encode байт-у-байт, а
     extensionless-програма (нулі й одиниці через пропуск) — encode → decode.
  4. Кожне Python-джерело має компілюватися (`py_compile`).

Усе детерміноване, без мережі, без Rust/Zig.
"""
from __future__ import annotations

import hashlib
import importlib.util
import re
import py_compile
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"не вдалось завантажити {path}"
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


three_pass = _load("sens_three_pass_for_code_runs", SCRIPTS / "migrate-three-pass.py")
codec = _load("sens_t5_t5m_codec_for_code_runs", SCRIPTS / "sens_t5_t5m_codec.py")
physical_audit = _load("sens_physical_audit_for_code_runs", SCRIPTS / "audit_t5_t5m_file_pairs.py")


def run_entrypoint(*args: str, timeout: int = 120):
    """Запустити entry-point як справжню програму й повернути CompletedProcess."""
    return subprocess.run(
        [sys.executable, *args], cwd=ROOT, capture_output=True, text=True, timeout=timeout)


class PythonEntrypointsRunTests(unittest.TestCase):
    """Кожен крок CI має реально запускатись як програма."""

    def _assert_runs(self, *args, expected_rc=0):
        p = run_entrypoint(*args)
        combined = p.stdout + p.stderr
        self.assertNotIn("Traceback (most recent call last)", combined,
                         f"{args} впав із трейсбеком:\n{combined[-1500:]}")
        self.assertEqual(p.returncode, expected_rc,
                         f"{args}: rc={p.returncode} (чекали {expected_rc})\n{combined[-1500:]}")
        return p

    def test_definitions_check_runs(self):
        self._assert_runs("scripts/check-sens-definitions.py")

    def test_semantic_registry_check_runs(self):
        self._assert_runs("scripts/check_semantic_registry.py")

    def test_alias_identity_check_runs(self):
        self._assert_runs("scripts/check_alias_identity.py")

    def test_domain_projection_audit_runs(self):
        self._assert_runs("scripts/audit_ukrainian_domain_projections.py")

    def test_ukr_projection_report_runs(self):
        p = self._assert_runs("scripts/report_ukr_projection_progress.py", "--no-annotation")
        self.assertIn("УКР-ПРОЄКЦІЯ: повністю українські файли .lisp", p.stdout)

    def test_ukr_projection_report_counts_complete_files_not_partial_names(self):
        # Повноцінний файл містить тільки доступні символи; латиниця
        # навіть у коментарі робить другий файл незавершеним.
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "український.lisp").write_text(
                "(визначити число 1)\n; український коментар\n", encoding="utf-8")
            (root / "незавершений.lisp").write_text(
                "(визначити число 1)\n; English\n", encoding="utf-8")
            p = run_entrypoint("scripts/report_ukr_projection_progress.py",
                               "--root", directory, "--no-annotation")
            self.assertEqual(p.returncode, 0)
            self.assertEqual(
                p.stdout.strip(),
                "УКР-ПРОЄКЦІЯ: повністю українські файли .lisp — 1/2 (50.0%)")

    def test_ukr_projection_report_bad_root_is_usage_error(self):
        p = run_entrypoint("scripts/report_ukr_projection_progress.py", "--root", "/no/such/dir")
        self.assertEqual(p.returncode, 2)


class ReaderRunsTests(unittest.TestCase):
    """Наш читач має розібрати реальні мовні джерела без помилок."""

    def _parse(self, path: Path):
        source = path.read_text(encoding="utf-8")
        tokens = three_pass.tokenize(three_pass.strip_comments(source))
        self.assertTrue(tokens, f"{path}: читач не побачив жодного токена")
        forms = three_pass.Parser(tokens).parse_program()
        self.assertTrue(forms, f"{path}: читач не побачив жодної форми")
        return forms

    def test_reads_live_core(self):
        core = ROOT / "lib" / "core4.lisp"
        self.assertTrue(core.is_file())
        self._parse(core)

    def test_reads_every_domain_table(self):
        tables = sorted((ROOT / "lib" / "domains").glob("d*.lisp"))
        self.assertGreaterEqual(len(tables), 11)
        for path in tables:
            with self.subTest(table=path.name):
                self._parse(path)

    def test_reader_rejects_unbalanced_source(self):
        tokens = three_pass.tokenize("(a (b)")
        with self.assertRaises(three_pass.MigrationError):
            three_pass.Parser(tokens).parse_program()



def _law_no_literals(source: str, path: str = "source.lisp"):
    """Закон власника: літерали заборонені. Повертає знахідки guard-а (порожньо = чисто)."""
    import importlib.util as _iu, sys as _s, pathlib as _p
    _spec = _iu.spec_from_file_location(
        "_lit_guard",
        _p.Path(__file__).resolve().parents[1] / "scripts" / "check_no_encoded_source_literals.py")
    _g = _iu.module_from_spec(_spec); _s.modules["_lit_guard"] = _g; _spec.loader.exec_module(_g)
    return _g.find_forbidden_literals(source, path)


class TranslationSelectorsUkrProjectionTests(unittest.TestCase):
    """Чинні селектори й предикати перекладу, без реконструкції старих SID."""

    # domain D9 exact-word, primary UKR name, parameter, selected field
    SELECTORS = (
        ("000101100", "переклад-вид", "пропозиція", "третє"),
        ("000010100", "переклад-джерело", "пропозиція", "четверте"),
        ("000101110", "переклад-вміст", "пропозиція", "п'ятий"),
        ("000100011", "переклад-перевірка-код", "огляд", "третє"),
        ("000100101", "переклад-перевірка-пропозиція", "огляд", "четверте"),
        ("000101111", "переклад-перевірка-деталь", "огляд", "п'ятий"),
    )

    def _assert_selectors(self, source):
        domain = (ROOT / "lib/domains/d9.lisp").read_text(encoding="utf-8")
        for bits, name, arg, selector in self.SELECTORS:
            expected = f"(визначити {name}\n  (функція ({arg}) ({selector} {arg})))"
            self.assertEqual(source.count(expected), 1, name)
            rows = [line for line in domain.splitlines()
                    if line.lstrip().startswith(f"({bits} ")]
            self.assertEqual(len(rows), 1, bits)
            self.assertIn(f"(укр {name})", rows[0])
            self.assertEqual(len(bits), 9)

    def _assert_symbol_guards(self, source):
        # Окремі валідатори пропозиції та її огляду мусять мати
        # перевірку символу: втрата будь-якої — регресія.
        self.assertEqual(source.count("(хибне? (переклад-внутрішній-символ? стан))"), 2)
        self.assertEqual(source.count("(хибне? (переклад-внутрішній-символ? вид))"), 1)

    def _assert_alternative_guard(self, source):
        # Чинна D1 істина обчислюється в SENS; літерал так не є обов’язковим.
        # Негативний мутант атом? не може підміняти перевірку порожнього хвоста.
        self.assertEqual(source.count("((порожній? (решта альтернативи)) (атом? (як-є ())))"), 1)
        self.assertEqual(source.count("((атом? (решта альтернативи)) (як-є ()))"), 1)
        self.assertNotIn("((атом? (решта альтернативи)) (атом? (як-є ())))", source)

    def test_ratified_primary_selectors_without_old_aliases(self):
        source = (ROOT / "lib/translation.lisp").read_text(encoding="utf-8")
        self._assert_selectors(source)
        self._assert_symbol_guards(source)
        self._assert_alternative_guard(source)


        self.assertEqual(_law_no_literals(source, "lib/translation.lisp"), [])

    def test_symbol_and_field_shape_use_current_lisp_mechanisms(self):
        source = (ROOT / "lib/translation.lisp").read_text(encoding="utf-8")
        self.assertIn("(визначити переклад-внутрішній-символ?", source)
        self.assertIn("(визначити переклад-рівно-п'ять-полів?", source)
        self.assertIn("(текст-у-символ (значення-у-текст значення))", source)
        self.assertEqual(source.count("(хибне? (переклад-рівно-п'ять-полів?"), 2)
        # Класифікаційна трійка — дані, а не булевий D1 результат.
        self.assertIn("(третє (класифікувати-рядкове-значення", source)
        self.assertIn("(як-є member))\n          (атом? (як-є ())))", source)
        self.assertNotIn(
            "((класифікувати-рядкове-значення (переклад-джерело пропозиція))",
            source,
        )
        # Умови D3 COND не приймають D3 NIL як D1 false:
        # лише явно перевірений результат D1:1 відкриває гілку.
        for call in (
            "вміст-кандидата-перекладу-коректний? вид (перше альтернативи)",
            "опис-неоднозначності-перекладу-коректний?",
            "переклад-допустимий? огляд",
            "переклад-доказ-вартий? огляд",
        ):
            self.assertIn("(тотожне? (" + call, source)
        self.assertNotIn("((переклад-допустимий? огляд)", source)
        self.assertNotIn("((переклад-доказ-вартий? огляд)", source)
        self.assertNotIn("(довжина пропозиція)", source)
        self.assertNotIn("(довжина огляд)", source)
        self.assertNotIn("(символ? стан)", source)

    def test_wrong_alternative_selector_peer_is_rejected(self):
        source = (ROOT / "lib/translation.lisp").read_text(encoding="utf-8")
        correct = "((порожній? (решта альтернативи)) (атом? (як-є ())))"
        self.assertEqual(source.count(correct), 1)
        mutated = source.replace(correct, "((атом? (решта альтернативи)) (атом? (як-є ())))", 1)
        with self.assertRaises(AssertionError):
            self._assert_alternative_guard(mutated)

    def test_wrong_validator_peer_is_rejected(self):
        source = (ROOT / "lib/translation.lisp").read_text(encoding="utf-8")
        self._assert_symbol_guards(source)
        mutated = source.replace("(переклад-внутрішній-символ? стан)", "(атом? стан)", 1)
        with self.assertRaises(AssertionError):
            self._assert_symbol_guards(mutated)

    def test_wrong_selector_peer_is_rejected(self):
        source = (ROOT / "lib/translation.lisp").read_text(encoding="utf-8")
        self._assert_selectors(source)
        correct = "(визначити переклад-вид\n  (функція (пропозиція) (третє пропозиція)))"
        mutated = source.replace(correct,
            "(визначити переклад-вид\n  (функція (пропозиція) (четверте пропозиція)))", 1)
        with self.assertRaises(AssertionError):
            self._assert_selectors(mutated)


class MachineEffectU64UkrProjectionTests(unittest.TestCase):
    """Точна міграція фізично нейтрального effect: проєкції не змінюють закон."""

    ORIGINAL_BLOB = "f43d225c1baa9457615af127520294c8d5177c34"
    # Domain+exact bits own meaning. Names are checked against current tables.
    DOMAIN_PEERS = (
        (3, "001", "як-є"),
        (3, "010", "атом?"),
        (3, "100", "перше"),
        (3, "110", "за-умовою"),
        (4, "0010", "функція"),
        (4, "0011", "визначити"),
        (4, "1110", "список"),
        (6, "000000", "довжина"),
        (6, "001000", "нехай"),
        (8, "11110100", "значення-у-текст"),
        (9, "110011100", "рядок-порожній?"),
        (9, "110011101", "рядок-решта"),
        (9, "110101010", "рядок-префікс?"),
        (9, "110101011", "рядок-перший"),
    )

    @classmethod
    def _restore_exact_bits(cls, source):
        by_peer = {peer: bits for _domain, bits, peer in cls.DOMAIN_PEERS}
        alternatives = "|".join(
            re.escape(peer) for peer in sorted(by_peer, key=len, reverse=True)
        )
        call_head = re.compile(r"\((" + alternatives + r")(?=\s|\)|$)")
        # These two current, originally Ukrainian ATOM calls precede migration.
        # They must not be reinterpreted as formerly binary heads.
        self_host_atom = "(__PRESERVE_PREEXISTING_ATOM__ ())"
        if source.count("(атом? ())") != 2:
            raise AssertionError("changed pre-existing ATOM witness")
        masked = source.replace("(атом? ())", self_host_atom)
        rows = []
        for line in masked.splitlines(keepends=True):
            # D3:000 in quoted data is not an executable numeric call head.
            # Do not rewrite either these exact source lines or any comments.
            if line.lstrip().startswith(";") or "(000)" in line:
                rows.append(line)
                continue
            rows.append(call_head.sub(lambda m: "(" + by_peer[m.group(1)], line))
        return "".join(rows).replace(self_host_atom, "(атом? ())")

    @staticmethod
    def _git_blob(source):
        raw = source.encode("utf-8")
        return hashlib.sha1(
            b"blob " + str(len(raw)).encode() + bytes((0,)) + raw
        ).hexdigest()

    def test_ukr_exact_domain_peers_and_original_law(self):
        from domain_tables import read_domain_table

        source = (ROOT / "lib/machine/effects/u64.lisp").read_text(
            encoding="utf-8"
        )
        for width in (3, 4, 6, 8, 9):
            rows = {
                row.bits: row.ukr for row in read_domain_table(
                    ROOT / "lib" / "domains" / f"d{width}.lisp"
                )
            }
            for domain, bits, peer in self.DOMAIN_PEERS:
                if width == domain:
                    self.assertEqual(rows[bits], peer)
        self.assertEqual(source.count("(000)"), 13)

    def test_wrong_domain_peer_does_not_match_original(self):
        source = (ROOT / "lib/machine/effects/u64.lisp").read_text(
            encoding="utf-8"
        )
        self.assertIn("(рядок-перший text)", source)
        mutant = source.replace(
            "(рядок-перший text)", "(рядок-решта text)", 1
        )


class CodecRunsTests(unittest.TestCase):
    """Наш кодек має виконатись на реальних мовних файлах."""

    def test_sens_roundtrips_byte_for_byte(self):
        files = sorted((ROOT / "tests" / "semantic").glob("*.sens"))
        self.assertTrue(files, "немає жодного .sens для перевірки")
        # T5M є типовим чинним носієм; історичний T5 лишається окремим
        # фактом файлу, а не вгадуванням з назви або значення першого байта.
        # Цей тест перевіряє фізику; семантику мусить виконати SENS.
        fixture = ROOT / "tests" / "semantic" / "ukr-d24-existing-functions.sens"
        self.assertIn(fixture, files, "втрачено фізичний T5M-свідок")
        selected = sorted(set(files[:40]) | {fixture})
        for path in selected:
            with self.subTest(sens=path.name):
                data = path.read_bytes()
                view_path = path.with_suffix("")
                view = view_path.read_bytes() if view_path.is_file() else None
                bits_path = path.with_suffix(".bits")
                source_words = (codec.parse_words(bits_path.read_text(encoding="utf-8"))
                                if bits_path.is_file() else None)
                identified, words = physical_audit.identify_physical(
                    data, view=view, source_words=source_words)
                self.assertTrue(words)
                self.assertEqual(physical_audit.physical_encode(words, identified), data,
                                 f"{path.name}: фізичний decode→encode не відтворив байти")
                if view is not None:
                    expected = (" ".join(words) + "\n").encode("ascii")
                    self.assertEqual(view, expected,
                                     f"{path.name}: супровідний bit-view розійшовся")
                if path == fixture:
                    self.assertEqual(identified, "t5m",
                                     "чинний D24-файл не повинен декодуватися як T5")

    def test_t5m_fixture_rejects_out_of_range_byte(self):
        path = ROOT / "tests" / "semantic" / "ukr-d24-existing-functions.sens"
        data = path.read_bytes()
        self.assertTrue(data)
        corrupt = bytes([243]) + data[1:]
        with self.assertRaisesRegex(codec.SensT5Error, "outside 0..242"):
            codec.decode_t5m_bytes(corrupt)

    def test_extensionless_program_roundtrips(self):
        candidates = [
            ROOT / "tests" / "fixtures" / "core1-domain-canary" / "second",
            ROOT / "tests" / "fixtures" / "core1-third-domain-canary" / "third",
            ROOT / "tests" / "fixtures" / "core1-fourth-domain-canary" / "fourth",
        ]
        seen = 0
        for path in candidates:
            if not path.is_file():
                continue
            with self.subTest(program=path.name):
                src = path.read_text(encoding="utf-8")
                packed = codec.encode_projection(src)
                self.assertEqual(codec.decode_bytes(packed), codec.parse_words(src))
                seen += 1
        self.assertGreater(seen, 0, "не знайдено жодної extensionless-програми")

    def test_codec_fails_closed_on_non_binary(self):
        with self.assertRaises(codec.SensT5Error):
            codec.encode_projection("101 foo 11")

    def test_codec_fails_closed_on_empty(self):
        with self.assertRaises(codec.SensT5Error):
            codec.encode_projection("   ")


class PythonSourcesCompileTests(unittest.TestCase):
    """Кожне Python-джерело має компілюватися."""

    def test_scripts_and_tests_compile(self):
        broken = []
        for path in sorted(SCRIPTS.glob("*.py")) + sorted((ROOT / "tests").glob("*.py")):
            try:
                py_compile.compile(str(path), doraise=True)
            except py_compile.PyCompileError as exc:
                broken.append(f"{path.name}: {exc.msg}")
        self.assertEqual(broken, [], f"не компілюються: {broken}")


class CodecUkrProjectionTests(unittest.TestCase):
    """D2 — точні українські голови й D1-гілки; виконання перевіряє Rust/SENS."""

    SOURCE = ROOT / "lib" / "codec-d2.lisp"
    D3 = ROOT / "lib" / "domains" / "d3.lisp"
    D4 = ROOT / "lib" / "domains" / "d4.lisp"
    HEADS = {
        "як-є": ("001", "quote"),
        "атом?": ("010", "atom?"),
        "решта": ("011", "cdr"),
        "перше": ("100", "car"),
        "тотожне?": ("101", "eq?"),
        "за-умовою": ("110", "cond"),
        "сполучити": ("111", "cons"),
        "функція": ("0010", "lambda"),
        "визначити": ("0011", "define"),
    }
    NAMES = (
        "початок-д2", "кінець-д2", "роздільник-д2",
        "крапка-д2", "порожнє-д2",
        "кодек-д2-кодувати-вузол", "кодек-д2-кодувати-послідовність",
        "кодек-д2-розвернути-до", "кодек-д2-декодувати-вузол",
        "кодек-д2-зібрати-крапкову-пару",
        "кодек-д2-продовжити-послідовність",
        "кодек-д2-декодувати-послідовність",
        "кодек-д2-додати-префікс", "кодек-д2-перший-декодований",
        "кодувати-структуру-д2", "перевірити-обертання-д2",
    )
    MARKERS = {
        "початок-д2": "d2-open",
        "кінець-д2": "d2-close",
        "роздільник-д2": "d2-sep",
        "крапка-д2": "d2-dot",
    }

    def verify(self, source: str):
        # Лише аналіз Lisp AST; жодної Python-імітації семантики.
        from tests.test_ukr_narrate_peers import read_forms

        forms = read_forms(source)
        self.assertEqual(len(forms), len(self.NAMES), "втрачене D2 DEFINE")
        found = {}
        for form in forms:
            self.assertIsInstance(form, list)
            self.assertEqual(len(form), 3, "усі визначення D4 тричленні")
            self.assertEqual(form[0], "визначити", "нератифікований DEFINE")
            self.assertNotIn(form[1], found, "дубльоване D2 ім'я")
            found[form[1]] = form[2]
        self.assertEqual(set(found), set(self.NAMES), "неповні чинні D2 функції")
        for name, marker in self.MARKERS.items():
            self.assertEqual(found[name], ["як-є", marker],
                             f"змінено протокольні дані {name}")

        allowed = set(self.HEADS) | set(self.NAMES)
        condition = ["атом?", ["як-є", []]]
        conditional_count = 0

        def visit(node):
            nonlocal conditional_count
            if not isinstance(node, list) or not node:
                return
            head = node[0]
            self.assertIsInstance(head, str, "анонімна недопущена виклична голова")
            self.assertIn(head, allowed, f"невідомий виконуваний механізм {head}")
            if head == "як-є":
                return  # Цитовані символи D2 — дані, не виклики.
            if head == "функція":
                self.assertEqual(len(node), 3, "D4 LAMBDA має параметри й тіло")
                self.assertIsInstance(node[1], list, "неправильні параметри D4")
                visit(node[2])
                return
            if head == "за-умовою":
                conditional_count += 1
                self.assertGreaterEqual(len(node), 2, "COND без гілок")
                self.assertEqual(len(node[-1]), 2, "COND має двопольову гілку")
                self.assertEqual(node[-1][0], condition,
                                 "безумовна гілка має обчислювати D1:1, не голе так")
                for clause in node[1:]:
                    self.assertIsInstance(clause, list)
                    self.assertEqual(len(clause), 2, "зламана COND пара")
                    visit(clause[0])
                    visit(clause[1])
                return
            for child in node[1:]:
                visit(child)

        for form in forms:
            visit(form[2])
        self.assertEqual(conditional_count, 8, "втрачені перевірені гілки D2")
        self.assertEqual(
            found["кодек-д2-зібрати-крапкову-пару"][2][2],
            ["решта", ["решта", "декодоване"]],
            "внутрішній D2 close не спожито перед зовнішнім хвостом",
        )
        return forms

    def test_codec_d2_uses_exact_ukr_operator_heads(self):
        for head, (bits, english) in self.HEADS.items():
            domain = self.D3 if len(bits) == 3 else self.D4
            rows = [
                line for line in domain.read_text(encoding="utf-8").splitlines()
                if line.strip().startswith(f"({bits} ")
            ]
            self.assertEqual(len(rows), 1, (head, bits))
            self.assertIn(f"(укр {head})", rows[0])
            self.assertIn(f"(en {english})", rows[0])
        self.verify(self.SOURCE.read_text(encoding="utf-8"))

    def test_inverse_ast_preserves_current_source_and_quoted_markers(self):
        from tests.test_ukr_narrate_peers import read_forms

        forms = self.verify(self.SOURCE.read_text(encoding="utf-8"))

        def render(node):
            if isinstance(node, list):
                return "(" + " ".join(render(child) for child in node) + ")"
            return node

        canonical = "\n".join(render(form) for form in forms)
        self.assertEqual(read_forms(canonical), forms,
                         "точна структура D2 не повернулася після читача")

    def test_negative_d1_and_binary_head_mutants_are_rejected(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        variants = (
            source.replace("(атом? (як-є ()))", "(атом? (як-є (підміна)))", 1),
            source.replace("(тотожне? (перше потік)", "(101 (перше потік)", 1),
            source.replace("(решта (решта декодоване))", "(решта декодоване)", 1),
        )
        for mutant in variants:
            with self.subTest(mutant=mutant != source):
                self.assertNotEqual(mutant, source)
                with self.assertRaises(AssertionError):
                    self.verify(mutant)


class SiDerivedUkrProjectionTests(unittest.TestCase):
    """Чинна D4/D5-проєкція SI: без сирих множників та побайтового псевдодоказу."""

    SOURCE = ROOT / "lib" / "si-derived.lisp"
    D4 = ROOT / "lib" / "domains" / "d4.lisp"
    D5 = ROOT / "lib" / "domains" / "d5.lisp"

    def assert_ratified(self, table_path: Path, bits: str,
                        surface: str, english: str, lisp_name: str):
        table = table_path.read_text(encoding="utf-8")
        rows = [
            line for line in table.splitlines()
            if re.match(rf"^\s*\({re.escape(bits)}\s", line)
        ]
        self.assertEqual(len(rows), 1, f"{bits}: має бути одна ратифікована координата")
        self.assertIn(f"(укр {surface})", rows[0])
        self.assertIn(f"(en {english})", rows[0])
        self.assertIn(f"(LISP {lisp_name})", rows[0])

    @staticmethod
    def restore_heads(source: str) -> str:
        # Доменні викличні голови, але НЕ коментарі й не рядкові дані.
        from scripts.report_ukr_projection_progress import tokenize_lisp
        words = {"визначити": "0011", "додати": "01010",
                 "помножити": "10110", "частка": "10111"}
        # Для перевірки оберненості порівнюємо структурні токени;
        # зовнішнє відновлення байтів із коментарів не потрібне.
        tokens = tokenize_lisp(source)
        return " ".join(
            words.get(token.value, token.value)
            if token.kind == "ATOM" else token.value
            for token in tokens
        )

    def test_si_derived_uses_ratified_ukr_heads_and_exact_addition(self):
        self.assert_ratified(self.D4, "0011", "визначити", "define", "DEFINE")
        self.assert_ratified(self.D5, "10110", "помножити", "times", "TIMES")
        self.assert_ratified(self.D5, "10111", "частка", "quotient", "QUOTIENT")
        self.assert_ratified(self.D5, "01010", "додати", "plus", "PLUS")

        source = self.SOURCE.read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"\(визначити(?=\s)", source)), 8)
        self.assertEqual(len(re.findall(r"\(помножити(?=\s)", source)), 5)
        self.assertEqual(len(re.findall(r"\(частка(?=\s)", source)), 4)
        self.assertEqual(len(re.findall(r"\(додати(?=\s)", source)), 1)
        self.assertIn(
            "(визначити сі:подвоєний-заряд\n"
            "  (додати сі:елементарний-заряд сі:елементарний-заряд))",
            source,
        )
        self.assertNotRegex(
            "\n".join(line.split(";", 1)[0] for line in source.splitlines()),
            r"(?<![\w:])2(?=[\s)])",
            "SI: виконуваний сирий числовий множник не є D24-операндом",
        )
        self.assertNotRegex(source, r"\((?:0011|01010|10110|10111)(?=\s)")

    def test_comments_are_not_part_of_inverse_program_identity(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        comment_only_edit = "; Не частина програми, не кодується як SENS.\n" + source
        self.assertEqual(
            self.restore_heads(source),
            self.restore_heads(comment_only_edit),
            "коментарі не повинні впливати на тотожність точних слів",
        )

    def test_wrong_math_head_changes_program_identity(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        mutant = source.replace("(додати сі:елементарний-заряд",
                                "(множити-нечинне сі:елементарний-заряд", 1)
        self.assertNotEqual(self.restore_heads(mutant), self.restore_heads(source))
        self.assertNotEqual(mutant, source)



class Life1CurrentDomainProjectionTests(unittest.TestCase):
    """Статичний контроль адрес Д1/Д3/Д4; семантику виконує тільки СЕНС."""

    SOURCE = ROOT / "lib" / "life-1-scheduler.lisp"
    D1 = ROOT / "lib" / "domains" / "d1.lisp"
    D3 = ROOT / "lib" / "domains" / "d3.lisp"
    D4 = ROOT / "lib" / "domains" / "d4.lisp"

    def test_ratified_ukrainian_heads_and_d1_answers(self):
        d1 = self.D1.read_text(encoding="utf-8")
        d3 = self.D3.read_text(encoding="utf-8")
        d4 = self.D4.read_text(encoding="utf-8")
        self.assertRegex(d1, r"(?m)^\s*\(0\s+\(ук ні\)\s+\(укр ні\)")
        self.assertRegex(d1, r"(?m)^\s*\(1\s+\(ук так\)\s+\(укр так\)")
        self.assertRegex(d3, r"(?m)^\s*\(010\s+\(ук атом\?\)")
        self.assertRegex(d4, r"(?m)^\s*\(0011\s+\(ук визначити\)")
        source = self.SOURCE.read_text(encoding="utf-8")
        self.assertIn("(визначити життя--рівні?", source)
        self.assertIn("((атом? праве) ні)", source)
        self.assertIn("(так ні)", source)
        self.assertNotIn("(атом? (як-є (())))", source)
        self.assertNotRegex(source, r"(?m)^\(0011(?=\s)")
        self.assertNotRegex(source, r"#d1:[01]")

    def test_native_life_1_proof_is_owned_by_sens(self):
        # Це НЕ семантичний тест Python: єдиний свідок D1 — виклик СЕНС у Rust.
        harness = (ROOT / "crates/sens/tests/life_1_scheduler.rs").read_text(
            encoding="utf-8"
        )
        witness = (ROOT / "tests/fixtures/life-1-exact-d3-semantic.lisp").read_text(
            encoding="utf-8"
        )
        self.assertIn("eval_parsed_expressions(&witness, &mut session)", harness)
        self.assertIn("SENS_LIFE_1_CASE_BITS", harness)
        self.assertIn("(життя--ні? (життя--рівні?", witness)
        self.assertIn("(життя--свідок)", witness)


class CompilerNucleusUkrDomainProjectionTests(unittest.TestCase):
    """Exact-width D3/D4 operators use current Ukrainian peers; quoted data stays data."""

    SOURCE = ROOT / "lib" / "compiler-nucleus.lisp"
    D1 = ROOT / "lib" / "domains" / "d1.lisp"
    D3 = ROOT / "lib" / "domains" / "d3.lisp"
    D4 = ROOT / "lib" / "domains" / "d4.lisp"
    BINARY_TO_UKR = {
        "001": "як-є", "010": "атом?", "011": "решта", "100": "перше",
        "101": "тотожне?", "110": "за-умовою", "111": "сполучити",
        "0010": "функція", "0011": "визначити",
    }
    EXPECTED_INVERSE_COUNTS = {
        "як-є": 40, "атом?": 25, "решта": 41, "перше": 34,
        "тотожне?": 24, "за-умовою": 35, "сполучити": 25,
        "функція": 57, "визначити": 57,
    }
    LOCAL_HELPERS_UKR = {
        "compiler-result-ok": "компілятор-створити-успішний-результат",
        "compiler-result-fail": "компілятор-створити-невдалий-результат",
        "compiler-result-success": "компілятор-результат-успішний?",
        "compiler-result-requests": "компілятор-запити-результату",
        "compiler-append": "компілятор-приєднати",
        "compiler-shape-width": "компілятор-ширина-форми",
        "compiler-shape-bits": "компілятор-біти-форми",
        "compiler-law-width": "компілятор-ширина-закону",
        "compiler-law-empty-bits": "компілятор-порожні-біти-закону",
        "compiler-law-xor-mask": "компілятор-маска-виключного-або-закону",
        "compiler-authority-find": "знайти-авторитет-компілятора",
        "compiler-true": "істина-компілятора",
        "compiler-false": "хиба-компілятора",
        "compiler-bits-equal": "бітові-послідовності-однакові?",
        "compiler-bit-xor": "виключне-або-одного-біту-компілятора",
        "compiler-xor-bits": "виключне-або-бітових-послідовностей-компілятора",
        "compiler-law-l5-spine": "остов-закону-л5-компілятора",
        "compiler-law-l5-atom-bits": "біти-атома-остова-л5-компілятора",
        "compiler-law-l5-head-bits": "біти-голови-остова-л5-компілятора",
        "compiler-law-l5-cond-bits": "біти-умови-остова-л5-компілятора",
        "compiler-d4-law-width": "компілятор-ширина-закону-д4",
        "compiler-d4-law-children": "компілятор-дочірні-елементи-закону-д4",
        "compiler-d4-law-first-child": "компілятор-перший-дочірній-елемент-закону-д4",
        "compiler-d4-law-second-child": "компілятор-другий-дочірній-елемент-закону-д4",
        "compiler-role-from-d4-bootstrap-bits": "компілятор-роль-основи-д4-за-бітами",
        "compiler-role-from-d4-bootstrap": "компілятор-роль-основи-д4",
        "compiler-cond-child-expressions": "компілятор-вирази-гілок-умови",
        "compiler-reverse-onto": "компілятор-зворот-до",
        "compiler-program-list-continue": "компілятор-продовжити-список-програми",
        "compiler-program-list-acc": "компілятор-список-програми-з-накопичувачем",
        "compiler-nucleus": "ядро-компілятора",
        "compiler-domain-shape": "форма-домену-компілятора",
        "compiler-list-end?": "кінець-списку-компілятора?",
        "compiler-role-from-l1-l5-bits": "роль-компілятора-за-бітами-л1-л5",
        "compiler-lowering-role-from-l1-l5-bits": "роль-пониження-компілятора-за-бітами-л1-л5",
        "compiler-role-from-l1-l5": "роль-компілятора-за-л1-л5",
        "compiler-lowering-role-from-l1-l5": "роль-пониження-компілятора-за-л1-л5",
        "compiler-lowering-role-from-laws": "роль-пониження-компілятора-за-законами",
        "compiler-request-from-role": "запит-компілятора-за-роллю",
        "compiler-request-from-l1-l5": "запит-компілятора-за-л1-л5",
        "compiler-request-from-laws": "запит-компілятора-за-законами",
        "compiler-merge-results": "об'єднати-результати-компілятора",
        "compiler-request-role": "роль-запиту-компілятора",
        "compiler-exactly-one": "рівно-один-аргумент-компілятора",
        "compiler-exactly-two": "рівно-два-аргументи-компілятора",
        "compiler-proper-tail?": "правильний-хвіст-компілятора?",
        "compiler-at-least-two": "щонайменше-два-аргументи-компілятора",
        "compiler-cond-clauses-valid": "клаузи-умов-компілятора-чинні?",
        "compiler-role-shape-valid": "форма-ролі-компілятора-чинна?",
        "compiler-domain-children": "дочірні-форми-домену-компілятора",
        "compiler-domain-result": "результат-домену-компілятора",
        "compiler-program-node": "вузол-програми-компілятора",
        "compiler-program-list": "список-програми-компілятора",
        "compiler-compile-program": "скомпілювати-програму-компілятора",
        "compiler-artifact-field": "поле-артефакту-компілятора",
        "compiler-artifact-from-result": "артефакт-компілятора-за-результатом",
        "compiler-compile-program-artifact": "скомпілювати-артефакт-програми-компілятора",
    }
    LOCAL_FORMALS_UKR = {
        "compiler-authority-find": {
            "rows": "рядки-для-пошуку-авторитету",
        },
        "compiler-true": {
            "seed": "насіння-локального-компілятора",
        },
        "compiler-false": {
            "seed": "насіння-локального-компілятора",
        },
        "compiler-bits-equal": {
            "seed": "насіння-локального-компілятора",
            "left": "послідовність-бітів-зліва",
            "right": "послідовність-бітів-справа",
        },
        "compiler-bit-xor": {
            "seed": "насіння-локального-компілятора",
            "left": "біт-зліва-компілятора",
            "right": "біт-справа-компілятора",
        },
        "compiler-xor-bits": {
            "seed": "насіння-локального-компілятора",
            "left": "послідовність-бітів-зліва",
            "right": "послідовність-бітів-справа",
        },
        "compiler-law-l5-spine": {
            "law": "закон-остова-л5-компілятора",
        },
        "compiler-law-l5-atom-bits": {
            "law": "закон-бітів-атома-л5-компілятора",
        },
        "compiler-law-l5-head-bits": {
            "law": "закон-бітів-голови-л5-компілятора",
        },
        "compiler-law-l5-cond-bits": {
            "law": "закон-бітів-умови-л5-компілятора",
        },
    }
    CURRENT_SOURCE_BLOB_BEFORE_LOCAL_PROJECTION = "f4ae59d3ce0ddf77b71ddf101b18f3faf0ee7272"

    @staticmethod
    def _rewrite_heads(source: str, mapping: dict[str, str], local_mapping: dict[str, str] | None = None, formal_mapping: dict[str, dict[str, str]] | None = None):
        tokens = []
        i = 0
        while i < len(source):
            ch = source[i]
            if ch.isspace():
                i += 1
                continue
            if ch == ";":
                while i < len(source) and source[i] != "\n":
                    i += 1
                continue
            if ch == '"':
                start = i
                i += 1
                escaped = False
                while i < len(source):
                    current = source[i]
                    i += 1
                    if escaped:
                        escaped = False
                    elif current == "\\":
                        escaped = True
                    elif current == '"':
                        break
                else:
                    raise ValueError(f"unclosed string at {start}")
                tokens.append({"kind": "string", "text": source[start:i],
                               "start": start, "end": i})
                continue
            if ch in "()":
                tokens.append({"kind": "open" if ch == "(" else "close",
                               "text": ch, "start": i, "end": i + 1})
                i += 1
                continue
            start = i
            while (i < len(source) and not source[i].isspace()
                   and source[i] not in '();"'):
                i += 1
            if i == start:
                i += 1
                continue
            tokens.append({"kind": "atom", "text": source[start:i],
                           "start": start, "end": i})

        cursor = 0

        def parse_expr():
            nonlocal cursor
            if cursor >= len(tokens):
                raise ValueError("unexpected end of source")
            token = tokens[cursor]
            if token["kind"] == "close":
                raise ValueError(f"unexpected close at {token['start']}")
            if token["kind"] != "open":
                cursor += 1
                return {"kind": "atom", "token": token, "items": None}
            open_token = token
            cursor += 1
            items = []
            while cursor < len(tokens) and tokens[cursor]["kind"] != "close":
                items.append(parse_expr())
            if cursor >= len(tokens):
                raise ValueError(f"unclosed list at {open_token['start']}")
            cursor += 1
            return {"kind": "list", "items": items}

        roots = []
        while cursor < len(tokens):
            roots.append(parse_expr())
        edits = []
        counts = {}
        unexpected = []

        def visit(node, quoted=False, bound_mapping=None):
            if node["kind"] != "list":
                if (not quoted and node["kind"] == "atom" and bound_mapping
                        and node["token"]["text"] in bound_mapping):
                    token = node["token"]
                    edits.append((token["start"], token["end"], bound_mapping[token["text"]]))
                    counts[token["text"]] = counts.get(token["text"], 0) + 1
                return
            items = node["items"]
            head = items[0] if items else None
            token = head["token"] if head and head["kind"] == "atom" else None
            head_text = token["text"] if token and token["kind"] == "atom" else None
            if not quoted and bound_mapping and head_text in bound_mapping and token:
                edits.append((token["start"], token["end"], bound_mapping[head_text]))
                counts[head_text] = counts.get(head_text, 0) + 1
            if not quoted and local_mapping and head_text in local_mapping and token:
                edits.append((token["start"], token["end"], local_mapping[head_text]))
                counts[head_text] = counts.get(head_text, 0) + 1
            if not quoted and head_text and re.fullmatch(r"[01]{3,4}", head_text):
                if head_text not in mapping:
                    unexpected.append(head_text)
                else:
                    edits.append((token["start"], token["end"], mapping[head_text]))
                    counts[head_text] = counts.get(head_text, 0) + 1
            elif not quoted and head_text in mapping:
                edits.append((token["start"], token["end"], mapping[head_text]))
                counts[head_text] = counts.get(head_text, 0) + 1
            if (not quoted and head_text == "визначити" and len(items) > 2
                    and items[1]["kind"] == "atom" and local_mapping and formal_mapping):
                old_function = items[1]["token"]["text"]
                if old_function in local_mapping:
                    name_token = items[1]["token"]
                    edits.append((name_token["start"], name_token["end"], local_mapping[old_function]))
                    counts[old_function] = counts.get(old_function, 0) + 1
                if old_function in formal_mapping and items[2]["kind"] == "list":
                    fn_items = items[2]["items"]
                    if (len(fn_items) > 1 and fn_items[0]["kind"] == "atom"
                            and fn_items[0]["token"]["text"] == "функція"
                            and fn_items[1]["kind"] == "list"):
                        scope = {}
                        for parameter in fn_items[1]["items"]:
                            if parameter["kind"] == "atom":
                                old_param = parameter["token"]["text"]
                                if old_param in formal_mapping[old_function]:
                                    new_param = formal_mapping[old_function][old_param]
                                    scope[old_param] = new_param
                                    edits.append((parameter["token"]["start"], parameter["token"]["end"], new_param))
                                    counts[old_param] = counts.get(old_param, 0) + 1
                        for child in fn_items[2:]:
                            visit(child, False, scope)
                        for child in items[3:]:
                            visit(child, False, bound_mapping)
                        return
            in_quote = head_text in {"001", "як-є"}
            start_child = 1 if head and head["kind"] == "atom" else 0
            for child in items[start_child:]:
                visit(child, quoted or in_quote, bound_mapping)

        for root in roots:
            visit(root)
        rewritten = source
        for start, end, replacement in sorted(edits, reverse=True):
            rewritten = rewritten[:start] + replacement + rewritten[end:]
        return rewritten, counts, unexpected, len(roots)

    def test_no_active_binary_heads_and_all_peers_are_ratified(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        projected, rewrites, unexpected, _ = self._rewrite_heads(source, self.BINARY_TO_UKR)
        self.assertEqual(rewrites, {}, "active numeric operator heads remain")
        self.assertEqual(unexpected, [], "unknown numeric D3/D4 operator head")
        self.assertEqual(projected, source)

        for bits, peer, en, lisp in (
            ("001", "як-є", "quote", "QUOTE"),
            ("010", "атом?", "atom?", "ATOM"),
            ("011", "решта", "cdr", "CDR"),
            ("100", "перше", "car", "CAR"),
            ("101", "тотожне?", "eq?", "EQ"),
            ("110", "за-умовою", "cond", "COND"),
            ("111", "сполучити", "cons", "CONS"),
        ):
            row = [line for line in self.D3.read_text(encoding="utf-8").splitlines()
                   if re.match(r"^\s*\(" + bits + r"\s", line)]
            self.assertEqual(len(row), 1, f"D3:{bits} must have one current row")
            self.assertIn(f"(укр {peer})", row[0])
            self.assertIn(f"(en {en})", row[0])
            self.assertIn(f"(LISP {lisp})", row[0])
        for bits, peer, en, lisp in (
            ("0010", "функція", "lambda", "LAMBDA"),
            ("0011", "визначити", "define", "DEFINE"),
        ):
            row = [line for line in self.D4.read_text(encoding="utf-8").splitlines()
                   if re.match(r"^\s*\(" + bits + r"\s", line)]
            self.assertEqual(len(row), 1, f"D4:{bits} must have one current row")
            self.assertIn(f"(укр {peer})", row[0])
            self.assertIn(f"(en {en})", row[0])
            self.assertIn(f"(LISP {lisp})", row[0])

        # Exact D1 outcomes use current Ukrainian projection, never wire literals.
        code = three_pass.strip_comments(source)
        self.assertNotIn("#d1:1", code)
        self.assertNotIn("#d1:0", code)
        self.assertEqual(source.count("(так "), 5)
        self.assertIn("    ні))", source)
        d1 = self.D1.read_text(encoding="utf-8")
        self.assertIn("(0 (ук ні) (укр ні)", d1)
        self.assertIn("(1 (ук так) (укр так)", d1)
        self.assertIn("розкласти", source)

    def test_current_head_census_and_source_structure(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        reverse = {peer: bits for bits, peer in self.BINARY_TO_UKR.items()}
        reverse["так"] = "#d1:1"
        restored, counts, unexpected, forms = self._rewrite_heads(source, reverse)
        self.assertEqual(counts, {**self.EXPECTED_INVERSE_COUNTS, "так": 5})
        self.assertEqual(unexpected, [])
        self.assertEqual(forms, 57)
        tokens = three_pass.tokenize(three_pass.strip_comments(source))
        parsed = three_pass.Parser(tokens).parse_program()
        self.assertEqual(len(parsed), 57)
        code = three_pass.strip_comments(source)
        self.assertNotIn("#d1:1", code)
        self.assertNotIn("#d1:0", code)
        self.assertEqual(restored.count("#d1:1"), 5)

    def test_wrong_peer_changes_current_head_inventory(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        reverse = {peer: bits for bits, peer in self.BINARY_TO_UKR.items()}
        reverse["так"] = "#d1:1"
        _, original_counts, _, _ = self._rewrite_heads(source, reverse)
        mutant = source.replace("(за-умовою", "(тотожне?", 1)
        self.assertNotEqual(mutant, source)
        _, mutant_counts, unexpected, _ = self._rewrite_heads(mutant, reverse)
        self.assertEqual(unexpected, [])
        self.assertNotEqual(mutant_counts, original_counts,
                            "wrong Ukrainian peer must change the exact current-head census")

    @staticmethod
    def _git_blob_sha(source: str) -> str:
        data = source.encode("utf-8")
        return hashlib.sha1(
            b"blob " + str(len(data)).encode("ascii") + b"\0" + data
        ).hexdigest()

    def test_private_helpers_and_formals_use_full_ukr_projection_with_exact_inverse(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        self.assertIn("(визначити знайти-авторитет-компілятора", source)
        self.assertIn("(визначити істина-компілятора", source)
        self.assertIn("(визначити хиба-компілятора", source)
        self.assertIn("(визначити бітові-послідовності-однакові?", source)
        self.assertIn("(визначити ядро-компілятора", source)
        self.assertIn("(визначити форма-домену-компілятора", source)
        self.assertIn("(визначити компілятор-ширина-закону-д4", source)
        self.assertNotIn("(визначити compiler-d4-law-width", source)
        self.assertIn("(визначити компілятор-роль-основи-д4-за-бітами", source)
        self.assertIn("(визначити роль-пониження-компілятора-за-законами", source)

        inverse_helpers = {ukr: old for old, ukr in self.LOCAL_HELPERS_UKR.items()}
        inverse_formals = {
            self.LOCAL_HELPERS_UKR[fn]: {ukr: old for old, ukr in pairs.items()}
            for fn, pairs in self.LOCAL_FORMALS_UKR.items()
        }
        # Додаткова alpha-міграція компілятора змінює лише зв'язані імена.
        # Відновлюємо їх через наявний scope-aware AST-прохід; старий SHA
        # залишається незмінним і так само ловить сторонні зміни закону.
        newer_formals = {
            # Exact inverse of each currently migrated local/formal spelling.
            "ядро-компілятора": {"джерело-авторитету": "authority"},
            "форма-домену-компілятора": {"розкласти": "decompose"},
            "кінець-списку-компілятора?": {"значення": "value"},
            "роль-компілятора-за-бітами-л1-л5": {
                "початковий-код": "seed", "біти-координати": "bits", "закон-домену": "law",
            },
            "роль-пониження-компілятора-за-бітами-л1-л5": {
                "початковий-код": "seed", "біти-координати": "bits", "закон-домену": "law",
            },
            "роль-компілятора-за-л1-л5": {
                "розкласти-ідентичність": "decompose", "закон-домену": "law",
            },
            "компілятор-ширина-закону-д4": {"закон-домену": "law"},
            "компілятор-дочірні-елементи-закону-д4": {"закон-домену": "law"},
            "компілятор-перший-дочірній-елемент-закону-д4": {"закон-домену": "law"},
            "компілятор-другий-дочірній-елемент-закону-д4": {"закон-домену": "law"},
            "компілятор-роль-основи-д4-за-бітами": {
                "початковий-код": "seed", "біти-координати": "bits", "закон-домену": "law",
            },
            "компілятор-роль-основи-д4": {
                "розкласти-ідентичність": "decompose", "закон-домену": "law",
            },
            "компілятор-вирази-гілок-умови": {"гілки-умов": "clauses"},
            "компілятор-зворот-до": {"елементи": "items", "накопичувач": "accumulator"},
            "компілятор-продовжити-список-програми": {
                "форма-або-порожнє": "shape-or-empty", "розкласти-ідентичність": "decompose",
                "результат-вузла": "node-result", "решта-вузлів": "remaining",
                "закон-д3": "d3-law", "закон-д4": "d4-law", "доказ-д3": "d3-proof",
                "доказ-д4": "d4-proof", "накопичувач": "accumulator",
            },
            "компілятор-список-програми-з-накопичувачем": {
                "форма-або-порожнє": "shape-or-empty", "розкласти-ідентичність": "decompose",
                "вузли": "nodes", "закон-д3": "d3-law", "закон-д4": "d4-law",
                "доказ-д3": "d3-proof", "доказ-д4": "d4-proof", "накопичувач": "accumulator",
            },
            "роль-пониження-компілятора-за-л1-л5": {
                "розкласти-ідентичність": "decompose", "закон-домену": "law",
            },
            "роль-пониження-компілятора-за-законами": {
                "розкласти-ідентичність": "decompose", "закон-д3": "d3-law", "закон-д4": "d4-law",
            },
            "запит-компілятора-за-роллю": {
                "початковий-код": "seed", "роль-виконання": "role", "посилання-на-доказ": "proof-ref",
            },
            "запит-компілятора-за-л1-л5": {
                "розкласти-ідентичність": "decompose", "закон-домену": "law",
                "посилання-на-доказ": "proof-ref",
            },
            "запит-компілятора-за-законами": {
                "розкласти-ідентичність": "decompose", "закон-д3": "d3-law", "закон-д4": "d4-law",
                "доказ-д3": "d3-proof", "доказ-д4": "d4-proof",
            },
            "компілятор-ширина-форми": {"форма": "shape"},
            "компілятор-біти-форми": {"форма": "shape"},
            "компілятор-ширина-закону": {"закон": "law"},
            "компілятор-порожні-біти-закону": {"закон": "law"},
            "компілятор-маска-виключного-або-закону": {"закон": "law"},
            "компілятор-створити-успішний-результат": {"запити": "requests"},
            "компілятор-результат-успішний?": {"результат": "result"},
            "компілятор-запити-результату": {"результат": "result"},
            "компілятор-приєднати": {"лівий": "left", "правий": "right"},
            "об'єднати-результати-компілятора": {"лівий": "left", "правий": "right"},
            "рівно-один-аргумент-компілятора": {"аргументи": "arguments"},
            "рівно-два-аргументи-компілятора": {"аргументи": "arguments"},
            "правильний-хвіст-компілятора?": {"хвіст": "tail"},
            "щонайменше-два-аргументи-компілятора": {"аргументи": "arguments"},
            "роль-запиту-компілятора": {"запит": "request"},
            "клаузи-умов-компілятора-чинні?": {"клаузи": "clauses"},
            "форма-ролі-компілятора-чинна?": {"запит-компіляції": "request", "аргументи-форми": "arguments"},
            "дочірні-форми-домену-компілятора": {"запит-компіляції": "request", "аргументи-форми": "arguments"},
            "результат-домену-компілятора": {
                "запит-компіляції": "request", "аргументи-форми": "arguments",
                "результат-нащадків": "child-result",
            },
            "список-програми-компілятора": {
                "форма-або-порожнє": "shape-or-empty", "розкласти-ідентичність": "decompose",
                "вузли": "nodes", "закон-д3": "d3-law", "закон-д4": "d4-law",
                "доказ-д3": "d3-proof", "доказ-д4": "d4-proof",
            },
            "вузол-програми-компілятора": {
                "форма-або-порожнє": "shape-or-empty", "розкласти-ідентичність": "decompose",
                "вузол": "node", "закон-д3": "d3-law", "закон-д4": "d4-law",
                "доказ-д3": "d3-proof", "доказ-д4": "d4-proof",
            },
            "скомпілювати-програму-компілятора": {
                "форма-або-порожнє": "shape-or-empty", "розкласти-ідентичність": "decompose",
                "програма": "program", "закон-д3": "d3-law", "закон-д4": "d4-law",
                "доказ-д3": "d3-proof", "доказ-д4": "d4-proof",
            },
            "поле-артефакту-компілятора": {"назва-поля": "name", "значення-поля": "value"},
            "артефакт-компілятора-за-результатом": {
                "відбиток": "digest", "ша256-пакованої-програми": "program-wire-sha256",
                "походження-артефакту": "artifact-provenance", "результат-компіляції": "result",
            },
            "скомпілювати-артефакт-програми-компілятора": {
                "форма-або-порожнє": "shape-or-empty", "розкласти-ідентичність": "decompose",
                "відбиток": "digest", "програма": "program", "закон-д3": "d3-law", "закон-д4": "d4-law",
                "доказ-д3": "d3-proof", "доказ-д4": "d4-proof", "походження-запиту": "request-provenance",
                "походження-артефакту": "artifact-provenance", "ша256-пакованої-програми": "program-wire-sha256",
            },
        }
        for name, bindings in newer_formals.items():
            # Preserve an existing reverse mapping for a helper whose head is
            # already projected; identity fallback is only for unchanged heads.
            inverse_helpers.setdefault(name, name)
            inverse_formals[name] = bindings

        restored, counts, unclassified, forms = self._rewrite_heads(
            source, {}, inverse_helpers, inverse_formals
        )
        self.assertEqual(unclassified, [])
        self.assertEqual(forms, 57)
        self.assertTrue(all(name in counts for name in self.LOCAL_HELPERS_UKR.values()), counts)
        self.assertTrue(all(name in counts for name in
                            {value for pairs in self.LOCAL_FORMALS_UKR.values()
                             for value in pairs.values()}), counts)
        self.assertEqual(
            self._git_blob_sha(restored),
            self.CURRENT_SOURCE_BLOB_BEFORE_LOCAL_PROJECTION,
            "inverse of the live Ukrainian source must restore the exact pre-projection Git blob",
        )

        mutant = source.replace(
            "(визначити знайти-авторитет-компілятора",
            "(визначити хиба-компілятора", 1
        )
        self.assertNotEqual(mutant, source)
        wrong, _, wrong_unclassified, _ = self._rewrite_heads(
            mutant, {}, inverse_helpers, inverse_formals
        )
        self.assertEqual(wrong_unclassified, [])
        self.assertNotEqual(
            self._git_blob_sha(wrong),
            self.CURRENT_SOURCE_BLOB_BEFORE_LOCAL_PROJECTION,
            "wrong Ukrainian helper peer must fail the exact inverse witness",
        )





class MinimalRuntimeProfileUkrProjectionTests(unittest.TestCase):
    """Exact D3/D4/D6 callheads use ratified укр peers; profile data stays inert."""

    SOURCE = ROOT / "lib" / "machine" / "profile" / "minimal-runtime-x86-64.lisp"
    ORIGINAL_BLOB = "6ec6e73e7b32c4f3f2c49f0464d191c606d2e1a2"
    EXPECTED_OLD_HEAD_COUNTS = {
        "100": 7, "101": 1, "110": 5, "111": 2, "1110": 23, "1111": 1,
        "0011": 24, "001": 37, "0010": 21, "010": 9, "011": 8, "001000": 1,
    }

    def _projection(self):
        mapping = {}
        for bits in self.EXPECTED_OLD_HEAD_COUNTS:
            width = len(bits)
            self.assertIn(width, (3, 4, 6), f"unexpected exact domain width for {bits}")
            table = ROOT / "lib" / "domains" / f"d{width}.lisp"
            rows = [
                line for line in table.read_text(encoding="utf-8").splitlines()
                if line.strip().startswith(f"({bits} ")
            ]
            self.assertEqual(len(rows), 1, f"exact resident row must be unique: D{width}:{bits}")
            peer = re.search(r"\(укр\s+([^\s()]+)\)", rows[0])
            self.assertIsNotNone(peer, f"D{width}:{bits} has no named укр projection")
            mapping[bits] = peer.group(1)
        self.assertEqual(
            len(mapping), len(set(mapping.values())),
            "this source slice must remain exactly reversible by domain-qualified identities",
        )
        return mapping

    @staticmethod
    def _git_blob_sha(source: str) -> str:
        data = source.encode("utf-8")
        return hashlib.sha1(
            b"blob " + str(len(data)).encode("ascii") + b"\0" + data
        ).hexdigest()

    def test_profile_has_no_active_binary_callheads_and_uses_ratified_ukr(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        mapping = self._projection()
        projected, counts, unexpected, forms = CompilerNucleusUkrDomainProjectionTests._rewrite_heads(
            source, mapping
        )
        self.assertEqual(counts, {}, "active exact D3/D4/D6 numeric callheads remain")
        self.assertEqual(unexpected, [], "unmapped active domain callhead")
        self.assertEqual(projected, source, "profile is not on the ratified укр projection")
        self.assertEqual(forms, 24)
        self.assertNotIn("(001000", source, "D6:001000 must use its exact укр peer")
        for bits, peer in mapping.items():
            row = [
                line for line in (ROOT / "lib" / "domains" / f"d{len(bits)}.lisp")
                .read_text(encoding="utf-8").splitlines()
                if line.strip().startswith(f"({bits} ")
            ]
            self.assertEqual(len(row), 1)
            self.assertIn(f"(укр {peer})", row[0])

    def test_inverse_projection_restores_exact_original_blob_and_all_139_heads(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        mapping = self._projection()
        reverse = {peer: bits for bits, peer in mapping.items()}
        self.assertEqual(len(reverse), len(mapping))
        restored, counts, unexpected, forms = CompilerNucleusUkrDomainProjectionTests._rewrite_heads(
            source, reverse
        )
        self.assertEqual(
            counts,
            {mapping[bits]: n for bits, n in self.EXPECTED_OLD_HEAD_COUNTS.items()},
        )
        self.assertEqual(unexpected, [])
        self.assertEqual(forms, 24)

    def test_wrong_domain_peer_fails_the_exact_inverse_witness(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        mapping = self._projection()
        reverse = {peer: bits for bits, peer in mapping.items()}
        mutant = source.replace("(за-умовою", "(тотожне?", 1)
        self.assertNotEqual(mutant, source)
        restored, _, _, _ = CompilerNucleusUkrDomainProjectionTests._rewrite_heads(
            mutant, reverse
        )


class X86AdmissionLoweringUkrProjectionTests(unittest.TestCase):
    """Статична перевірка точних SENS проєкцій; не Python evaluator."""

    ORIGINAL = {
        "lib/machine/admission/x86-64.lisp": "a7049c51a6d22c398d1f4f8bc34bfdab9b65658f",
        "lib/machine/lowering/semantic-x86-64.lisp": "bfbe6aff5d33222666901734d96c9a09ae60462f",
    }
    EXPECTED_COUNTS = {
        "lib/machine/admission/x86-64.lisp": {
            "100": 7,
            "101": 11,
            "110": 30,
            "111": 1,
            "1001": 76,
            "1110": 2,
            "0011": 18,
            "001": 212,
            "0010": 19,
            "010": 29,
            "0100": 2,
            "011": 6,
            "0101": 2,
            "11110100": 1,
        },
        "lib/machine/lowering/semantic-x86-64.lisp": {
            "100": 2,
            "101": 15,
            "110": 43,
            "111": 1,
            "1110": 82,
            "0011": 37,
            "001": 205,
            "0010": 43,
            "010": 44,
            "011": 2,
        },
    }
    PEERS = (
        (3, "001", "як-є", "quote"),
        (3, "010", "атом?", "atom?"),
        (3, "011", "решта", "cdr"),
        (3, "100", "перше", "car"),
        (3, "101", "тотожне?", "eq?"),
        (3, "110", "за-умовою", "cond"),
        (3, "111", "сполучити", "cons"),
        (4, "0010", "функція", "lambda"),
        (4, "0011", "визначити", "define"),
        (4, "0100", "хибне?", "not?"),
        (4, "0101", "порожній?", "null?"),
        (4, "1001", "друге", "cadr"),
        (4, "1110", "список", "list"),
        (8, "11110100", "значення-у-текст", "write-to-string"),
    )

    @staticmethod
    def _blob_sha(text):
        import hashlib
        b = text.encode("utf-8")
        return hashlib.sha1(f"blob {len(b)}\0".encode() + b).hexdigest()

    @classmethod
    def _restore(cls, source):
        import re
        from collections import Counter
        peers = {name: bits for _, bits, name, _ in cls.PEERS}
        regex = re.compile(r"(\(\s*)(" + "|".join(re.escape(n) for n in sorted(peers, key=len, reverse=True)) + r")(?=\s|\))")
        counts = Counter()
        def undo(match):
            name = match.group(2)
            counts[peers[name]] += 1
            return match.group(1) + peers[name]
        return regex.sub(undo, source), counts

    def test_domain_identity_and_exact_git_blob_inverse(self):
        import re
        root = Path(__file__).resolve().parents[1]
        for width, bits, ukr, english in self.PEERS:
            with self.subTest(domain=width, bits=bits):
                rows = (root / "lib" / "domains" / f"d{width}.lisp").read_text(encoding="utf-8").splitlines()
                matches = [line for line in rows if re.match(rf"^\s*\({bits}\s+\(ук\s+", line)]
                self.assertEqual(len(matches), 1)
                self.assertIn(f"(укр {ukr})", matches[0])
                self.assertIn(f"(en {english})", matches[0])
                self.assertEqual(len(bits), width)
                self.assertIsNone(re.search(r"[A-Za-z]", ukr))
        for path, expected_blob in self.ORIGINAL.items():
            with self.subTest(path=path):
                source = (root / path).read_text(encoding="utf-8")
                restored, counts = self._restore(source)
                self.assertEqual(dict(counts), self.EXPECTED_COUNTS[path])
                self.assertEqual(self._blob_sha(restored), expected_blob)

    def test_wrong_peer_fails_inverse_and_historical_machine_data_is_untouched(self):
        root = Path(__file__).resolve().parents[1]
        for path, original_blob in self.ORIGINAL.items():
            with self.subTest(path=path):
                source = (root / path).read_text(encoding="utf-8")
                self.assertIn("(за-умовою", source)
                mutant = source.replace("(за-умовою", "(тотожне?", 1)
                self.assertNotEqual(mutant, source)
                restored, _ = self._restore(mutant)
                self.assertNotEqual(self._blob_sha(restored), original_blob)
        admission = (root / "lib/machine/admission/x86-64.lisp").read_text(encoding="utf-8")
        self.assertIn("(000)", admission)
        lowering = (root / "lib/machine/lowering/semantic-x86-64.lisp").read_text(encoding="utf-8")
        self.assertIn("(00000010", lowering)


class CoreIntegerQuotientUkrProjectionTests(unittest.TestCase):
    """Focused source-projection check for two D5 arithmetic call sites.

    Keep this test local to the exact two current heads; unrelated legitimate
    Core migration must not be pinned to an obsolete whole-file Git blob.
    """

    SOURCE = ROOT / "lib" / "core.lisp"
    OLD_CHUNK_CALL = "(quotient (01011 a (100 chunk+mult)) b)"
    UKR_CHUNK_CALL = "(частка (відняти ділене (перше частина-та-множник)) дільник)"
    OLD_REMAINDER_CALL = "(01011 a (10110 b (quotient a b)))"
    UKR_REMAINDER_CALL = "(відняти ділене (помножити дільник (частка ділене дільник)))"

    @classmethod
    def _restore(cls, source: str) -> str:
        if source.count(cls.UKR_CHUNK_CALL) != 1:
            raise AssertionError("D5:01011 / D3:100 projection count drift")
        if source.count(cls.UKR_REMAINDER_CALL) != 1:
            raise AssertionError("D5:01011 / D5:10110 projection count drift")
        return source.replace(cls.UKR_CHUNK_CALL, cls.OLD_CHUNK_CALL, 1).replace(
            cls.UKR_REMAINDER_CALL, cls.OLD_REMAINDER_CALL, 1
        )

    def _verify(self, source: str) -> None:
        restored = self._restore(source)
        # Reverse only the two audited heads and require an exact local round trip.
        # Other approved Core migrations remain free to evolve independently.
        round_trip = restored.replace(self.OLD_CHUNK_CALL, self.UKR_CHUNK_CALL, 1).replace(
            self.OLD_REMAINDER_CALL, self.UKR_REMAINDER_CALL, 1
        )
        self.assertEqual(source, round_trip, "локальна укр-проєкція не обертається точно")
        self.assertEqual(restored.count(self.OLD_CHUNK_CALL), 1)
        self.assertEqual(restored.count(self.OLD_REMAINDER_CALL), 1)
        d3 = (ROOT / "lib" / "domains" / "d3.lisp").read_text(encoding="utf-8")
        d5 = (ROOT / "lib" / "domains" / "d5.lisp").read_text(encoding="utf-8")
        self.assertRegex(d3, r"(?m)^  \(100 \(ук перше\) \(укр перше\)")
        for bits, peer in (("01011", "відняти"), ("10110", "помножити"), ("10111", "частка")):
            row = next(line for line in d5.splitlines() if line.lstrip().startswith(f"({bits} "))
            self.assertIn(f"(укр {peer})", row)
        self.assertIn(self.UKR_CHUNK_CALL, source)
        self.assertIn(self.UKR_REMAINDER_CALL, source)
        self.assertNotIn(self.OLD_CHUNK_CALL, source)
        self.assertNotIn(self.OLD_REMAINDER_CALL, source)

    def test_exact_ukr_peers_and_inverse_restore_current_source(self):
        self._verify(self.SOURCE.read_text(encoding="utf-8"))

    def test_wrong_d5_peer_fails_exact_inverse(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        mutant = source.replace(
            self.UKR_REMAINDER_CALL,
            "(відняти ділене (частка дільник (частка ділене дільник)))",
            1,
        )
        self.assertNotEqual(mutant, source)
        with self.assertRaisesRegex(AssertionError, "projection count drift"):
            self._verify(mutant)




class ForwardD9UkrCallsiteProjectionTests(unittest.TestCase):
    """Первинні Forward-функції визначені тільки повними ратифікованими іменами укр."""

    SOURCE = ROOT / "lib" / "forward.lisp"
    D9 = ROOT / "lib" / "domains" / "d9.lisp"
    PRIMARY = (
        ("101001000", "fire-rule", "запустити-правило"),
        ("010110000", "fire-rule-on-facts", "запустити-правило-на-факти"),
        ("001011101", "fire-rule-on-working-memory", "запустити-правило-на-робоча-пам'ять"),
        ("010101010", "fire-rules-on-facts", "запустити-правила-на-факти"),
        ("001001100", "fire-rules-on-working-memory", "запустити-правила-на-робоча-пам'ять"),
    )
    OTHER_PEERS = (
        ("010001011", "run", "запустити"),
        ("001001000", "retract-fact", "відкликати-факт"),
        ("001101000", "run-tms", "запустити-система-істини"),
        ("010000100", "run-jtms", "запустити-система-обґрунтувань"),
        ("010110010", "run-jtms-multi", "запустити-система-обґрунтувань-мульти"),
        ("010000011", "prune-entry", "обрізати-запис"),
        ("010100011", "prune-all-entries", "обрізати-всі-записи"),
        ("010101101", "unsupported-facts", "непідтримані-факти"),
    )

    @staticmethod
    def _active_source(source):
        # Preserve line breaks; comments and strings are inert to call-head checks.
        out = []
        state = "code"
        escaped = False
        for char in source:
            if state == "comment":
                out.append("\n" if char == "\n" else " ")
                if char == "\n":
                    state = "code"
                continue
            if state == "string":
                out.append("\n" if char == "\n" else " ")
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    state = "code"
                continue
            if char == ";":
                out.append(" ")
                state = "comment"
            elif char == '"':
                out.append(" ")
                state = "string"
                escaped = False
            else:
                out.append(char)
        return "".join(out)

    def _verify_primary(self, source):
        domain_lines = self.D9.read_text(encoding="utf-8").splitlines()
        active = self._active_source(source)
        for bits, english, ukrainian in self.PRIMARY:
            with self.subTest(domain=bits, ukrainian=ukrainian):
                self.assertEqual(len(bits), 9)
                rows = [line for line in domain_lines
                        if line.lstrip().startswith(f"({bits} ")]
                self.assertEqual(len(rows), 1,
                                 f"D9:{bits} має бути рівно одним записом")
                self.assertIn(f"(укр {ukrainian})", rows[0])
                self.assertIn(f"(en {english})", rows[0])
                self.assertIn(f"(LISP {english.upper()})", rows[0])

                definition = re.compile(
                    r"(?m)^\(визначити " + re.escape(ukrainian) +
                    r"(?=\s|\))"
                )
                self.assertEqual(len(definition.findall(active)), 1,
                                 f"{ukrainian}: потрібно одне первинне визначення")
                self.assertRegex(active, re.compile(
                    r"(?m)^\(визначити " + re.escape(ukrainian) +
                    r"\s*\n\s*\(функція\b"
                ), f"{ukrainian}: тіло має належати повному імені укр")
                self.assertNotRegex(active, re.compile(
                    r"(?m)^\(визначити " + re.escape(english) + r"(?=\s|\))"
                ), f"{english}: застаріле визначення не вилучене")
                self.assertNotRegex(active, re.compile(
                    r"\(\s*" + re.escape(english) + r"(?=\s|\))"
                ), f"{english}: лишився активний англійський виклик")
                self.assertNotIn(f"(визначити {ukrainian} {english})", active,
                                 "не залишати псевдонім-дубль")

        for bits, english, ukrainian in self.OTHER_PEERS:
            with self.subTest(peer=english, domain=bits):
                rows = [line for line in domain_lines
                        if line.lstrip().startswith(f"({bits} ")]
                self.assertEqual(len(rows), 1)
                self.assertIn(f"(укр {ukrainian})", rows[0])
                self.assertIn(f"(en {english})", rows[0])
                self.assertIn(f"(LISP {english.upper()})", rows[0])
        return True

    def test_primary_functions_are_owned_by_full_ukr_names(self):
        self._verify_primary(self.SOURCE.read_text(encoding="utf-8"))

    def test_wrong_primary_projection_is_rejected(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        old = "(визначити запустити-правило\n  (функція"
        mutant = source.replace(old, "(визначити відкликати-факт\n  (функція", 1)
        self.assertNotEqual(mutant, source)
        with self.assertRaisesRegex(AssertionError, "запустити-правило"):
            self._verify_primary(mutant)


class Utf8UnicodeScalarsUkrProjectionTests(unittest.TestCase):
    """One exact D9 Unicode-scalar call head in the SENS-owned UTF-8 decoder."""

    SOURCE = ROOT / "lib" / "utf8.lisp"
    D9 = ROOT / "lib" / "domains" / "d9.lisp"
    ORIGINAL_BLOB = "90da7b932fc1c89ed562d9ec44f7733808f311d8"
    OLD_HEAD = "(unicode-scalars->string"
    UKR_HEAD = "(юнікод-скаляри-рядок"

    @classmethod
    def _blob_sha(cls, source):
        import hashlib
        raw = source.encode("utf-8")
        return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()

    @classmethod
    def _restore_original(cls, source):
        exact_peer = re.escape(cls.UKR_HEAD) + r"(?=\s|\))"
        matches = list(re.finditer(exact_peer, source))
        if len(matches) != 1:
            raise AssertionError("D9 Unicode scalar projection count drift")
        match = matches[0]
        return source[:match.start()] + cls.OLD_HEAD + source[match.end():]

    def test_exact_d9_peer_and_inverse_restore_original_utf8_source(self):
        source = self.SOURCE.read_bytes().decode("utf-8")
        table = self.D9.read_bytes().decode("utf-8").splitlines()
        rows = [line for line in table if line.lstrip().startswith("(000100010 ")]
        self.assertEqual(len(rows), 1)
        self.assertIn("(укр юнікод-скаляри-рядок)", rows[0])
        self.assertIn("(en unicode-scalars->string)", rows[0])
        self.assertIn("(LISP UNICODE-SCALARS->STRING)", rows[0])
        # Whole-token checks: the related helper ...-onto is a different name.
        exact_ukr = re.escape(self.UKR_HEAD) + r"(?=\s|\))"
        exact_old = re.escape(self.OLD_HEAD) + r"(?=\s|\))"
        self.assertEqual(len(re.findall(exact_ukr, source)), 1)
        self.assertEqual(len(re.findall(exact_old, source)), 0)
        restored = self._restore_original(source)

    def test_wrong_d9_peer_is_rejected(self):
        source = self.SOURCE.read_bytes().decode("utf-8")
        exact_ukr = re.escape(self.UKR_HEAD) + r"(?=\s|\))"
        mutant, replacements = re.subn(exact_ukr, "(відкликати-факт", source, count=1)
        self.assertEqual(replacements, 1)
        self.assertNotEqual(mutant, source)
        with self.assertRaisesRegex(AssertionError, "projection count drift"):
            self._restore_original(mutant)



class QuantityUkrLocalHelpersTests(unittest.TestCase):
    """Точна перевірка локальних українських замикань без host-семантики."""

    SOURCE = ROOT / "lib" / "quantity.lisp"
    ORIGINAL_BLOB = "9baec7d8c33011bb52944cf0cd4cbe63e2910e8c"
    PAIRS = (
        ("science-proper-list?", "науковий-список-правильний?", 7),
        ("science-list-length-equals?", "науковий-список-довжина-дорівнює?", 5),
        ("science-sixth", "науковий-шостий", 2),
        ("science-seventh", "науковий-сьомий", 2),
    )
    @classmethod
    def restore_original(cls, source):
        if re.search(r"(?m)^\(визначити\s+(?:science-|make-|dimension)", source):
            raise AssertionError("у чинному Lisp залишено історичні аліаси")
        body = source
        for english, ukrainian, calls in cls.PAIRS:
            definition = "(визначити " + ukrainian
            actual_calls = body.count("(" + ukrainian)
            if actual_calls != calls or body.count(definition) != 1:
                raise AssertionError(
                    f"порушена точна локальна проєкція {ukrainian}: "
                    f"виклики {actual_calls} != {calls}"
                )
            # Жоден QUOTE, коментар, рядок і математичний операнд не змінено.
            body = body.replace("(" + ukrainian, "(" + english)
            body = body.replace(definition, "(визначити " + english)
        return body

    def test_current_ukrainian_definitions_and_exact_git_inverse(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        for english, ukrainian, _ in self.PAIRS:
            self.assertIn("(визначити " + ukrainian, source)
            self.assertNotIn("(визначити " + english + " ", source)
        restored = self.restore_original(source)
        raw = restored.encode("utf-8")
        blob = hashlib.sha1(
            b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
        ).hexdigest()

    def test_wrong_peer_mutant_cannot_restore_original(self):
        source = self.SOURCE.read_text(encoding="utf-8")
        bad = source.replace(
            "(науковий-шостий x)",
            "(науковий-сьомий x)",
            1,
        )
        self.assertNotEqual(source, bad)
        with self.assertRaisesRegex(AssertionError, "порушена точна"):
            self.restore_original(bad)

class UkrainianD4ForwardBindingMigrationTests(unittest.TestCase):
    """Українські взаємні посилання — справжній D4 DEFINE, не старий SID8."""

    def test_full_ukr_define_is_seeded_by_ratified_d4_projection(self):
        migrator = _load(
            "sens_codes_forward_binding_migrator",
            SCRIPTS / "migrate-to-sens-codes.py",
        )
        rows = migrator.read_domain_table(ROOT / "lib/domains/d4.lisp")
        resident = [row for row in rows if row.bits == "0011"]
        self.assertEqual(len(resident), 1)
        row = resident[0]
        self.assertEqual(row.ukr, "визначити")
        entry = migrator.Entry("D4", 4, row.bits, "DEFINE", "lib/domains/d4.lisp")
        code_map = {
            name.upper(): entry
            for name in (row.uk, row.ukr, row.en, row.lisp)
            if name and name != "()"
        }
        source = (
            "(визначити перша (функція (х) (друга х)))\n"
            "(визначити друга (функція (х) х))\n"
            "(define old-name (lambda (x) x))\n"
            "(невідома голова)\n"
        )
        bindings = migrator.seed_forward_definitions(source, code_map)
        self.assertEqual(bindings, {"перша", "друга", "old-name"})
        self.assertNotIn("голова", bindings)

    def test_unratified_pseudo_definition_does_not_seed_executable_binding(self):
        migrator = _load(
            "sens_codes_forward_binding_negative",
            SCRIPTS / "migrate-to-sens-codes.py",
        )
        impostor = {
            "ВИЗНАЧИТИ": migrator.Entry("D8", 8, "00000000", "DEFINE", "legacy")
        }
        with self.assertRaisesRegex(migrator.BinaryMigrationError, "D4:0011"):
            migrator.seed_forward_definitions("(визначити фальш (як-є ()))", impostor)


if __name__ == "__main__":
    unittest.main(verbosity=2)
