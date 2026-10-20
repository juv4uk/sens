"""Перевірки української поверхні епістемічного та сховищного модулів SENS.

Семантику епістемічних функцій виконує окремий інтеграційний тест Rust.
Цей тест фіксує українські entrypoint-и та їхні ратифіковані доменні identity;
англомовні compatibility alias-и не є частиною активного Lisp API.
"""
from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EP = ROOT / "lib/epistemic.lisp"
STORE = ROOT / "lib/content-store.lisp"
CORE = ROOT / "lib/core4.lisp"
D9 = ROOT / "lib/domains/d9.lisp"
D10 = ROOT / "lib/domains/d10.lisp"

TOKEN = re.compile(r';[^\n]*|"(?:\\.|[^"\\])*"|[()]|[^\s();]+')
REQUIRED_EPISTEMIC = (
    "створити-структуроване-твердження",
    "це-належне-посилання-на-джерело?",
    "епістеміка--посилання-на-твердження?",
    "твердження-твердження",
    "твердження-перевірка",
    "доказ-підсумок",
    "отримати-посилання-на-джерело-доказу",
    "намір-ціль",
    "отримати-джерело-спостереження",
    "спостереження-твердження",
    "отримати-посилання-доказу-на-твердження",
    "доказ-метод",
    "отримати-необхідні-можливості-наміру",
    "отримати-умови-зупинки-наміру",
    "отримати-очікувані-результати-наміру",
    "епістеміка--рівні-посилання?",
    "підтверджувальний-доказ",
    "епістеміка--усі-вимоги-наявні?",
    "усі-необхідні-можливості-наміру-забезпечені?",
)
RETIRED_EPISTEMIC = (
    "make-observation", "make-claim", "make-evidence", "make-intent",
    "source-ref?", "observation-source", "evidence-claim-ref", "intent-requires",
    "supporting-evidence", "intent-capabilities-satisfied?", "claim-statement",
    "claim-review", "evidence-outcome", "intent-goal", "evidence-method",
    "observation-statement", "epistemic--claim-ref?",
)

# Це точні D9/D10 координати, не сід8, не фізичні опкоди.
PEERS = (
    (10, "0001110110", "make-claim", "створити-структуроване-твердження"),
    (10, "0010011001", "source-ref?", "це-належне-посилання-на-джерело?"),
    (10, "0001110111", "observation-source", "отримати-джерело-спостереження"),
    (10, "0010000111", "evidence-claim-ref", "отримати-посилання-доказу-на-твердження"),
    (10, "0001111011", "intent-requires", "отримати-необхідні-можливості-наміру"),
    (9, "101100001", "supporting-evidence", "підтверджувальний-доказ"),
    (10, "0001111110", "intent-capabilities-satisfied?",
     "усі-необхідні-можливості-наміру-забезпечені?"),
    (9, "101010110", "evidence?", "доказ?"),
    (9, "101111111", "evidence-outcome", "доказ-підсумок"),
    (9, "101101100", "intent?", "намір?"),
    (9, "101100011", "map-empty", "мапа-порожній"),
)

def read_forms(source: str):
    words = [m.group() for m in TOKEN.finditer(source)
             if not m.group().startswith(";")]
    position = 0

    def read():
        nonlocal position
        if position == len(words):
            raise ValueError("незавершена SENS форма")
        word = words[position]
        position += 1
        if word == ")":
            raise ValueError("зайва закривальна дужка")
        if word != "(":
            return word
        items = []
        while position < len(words) and words[position] != ")":
            items.append(read())
        if position == len(words):
            raise ValueError("незакритий список")
        position += 1
        return items

    result = []
    while position < len(words):
        result.append(read())
    return result


def definitions(source: str):
    result = {}
    for form in read_forms(source):
        if not isinstance(form, list) or len(form) != 3 or form[0] not in ("0011", "визначити"):
            raise AssertionError("кожне верхнє визначення — D4:0011")
        name = form[1]
        if not isinstance(name, str) or name in result:
            raise AssertionError("дубль або неправильне ім'я DEFINE")
        result[name] = form[2]
    return result


def verify_epistemic(ep: str, core: str, domains: dict[int, str]):
    epdefs = definitions(ep)

    # Слово з таблиці має рівно свій ratified domain і full spelling.
    for width, bits, english, full in PEERS:
        rows = [line.strip() for line in domains[width].splitlines()
                if line.lstrip().startswith(f"({bits} ")]
        if len(rows) != 1 or (f"(en {english})" not in rows[0]
                              or f"(укр {full})" not in rows[0]):
            raise AssertionError(f"D{width}:{bits}: peer spelling / identity drift")

    for name in REQUIRED_EPISTEMIC:
        if name not in epdefs:
            raise AssertionError(f"потрібний український entrypoint відсутній: {name}")
    if epdefs["створити-структуроване-твердження"] != "створити-твердження":
        raise AssertionError("українська назва конструктора має зберігати тотожне замикання")
    for old in RETIRED_EPISTEMIC:
        if old in epdefs:
            raise AssertionError(f"історична англійська голова лишилася активною: {old}")

    # Типові предикати та конструктори вже визначені в Core4; модуль не
    # дублює їх англомовними псевдонімами.
    for name in ("доказ?", "намір?", "спостереження?", "твердження?",
                 "створити-твердження", "доказ-підсумок"):
        if f"(визначити {name}\n" not in core and f"(визначити {name} " not in core:
            raise AssertionError(f"{name}: чинне українське визначення Core4 відсутнє")
    if "(визначити map-empty мапа-порожній)" not in core:
        raise AssertionError("map-empty: core peer identity порушено")
    for value in ("створити-твердження", "доказ-підсумок"):
        if f"(визначити {value}\n" not in core and f"(визначити {value} " not in core:
            raise AssertionError(f"{value}: джерельний SENS closure не визначений")

    # Суворий мовний допуск: історична латинська виклична голова НЕ стає
    # ukr лише тому, що обернена нормалізація дає той самий закон.
    def heads(expr):
        if not isinstance(expr, list) or not expr:
            return set()
        first = expr[0]
        if first in ("як-є", "001"):
            return {first}
        result = {first} if isinstance(first, str) else heads(first)
        for child in expr[1:]:
            result |= heads(child)
        return result

    executable_heads = set()
    for name in REQUIRED_EPISTEMIC:
        executable_heads |= heads(epdefs[name])
    if executable_heads & set(RETIRED_EPISTEMIC):
        raise AssertionError("український Lisp закон викликає історичну англійську голову")
    return True


def verify_empty_store_peer(store: str):
    storedefs = definitions(store)
    if storedefs.get("порожній-вміст-сховище") != ["функція", [], "мапа-порожній"]:
        raise AssertionError("порожнє сховище має посилатися на чинний SENS peer")
    return True


class OptInUkrMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ep = EP.read_text(encoding="utf-8")
        cls.store = STORE.read_text(encoding="utf-8")
        cls.core = CORE.read_text(encoding="utf-8")
        cls.domains = {d: (ROOT / f"lib/domains/d{d}.lisp").read_text(encoding="utf-8")
                       for d in (9, 10)}

    def test_exact_identity_and_laws(self):
        self.assertTrue(verify_epistemic(self.ep, self.core, self.domains))

    def test_data_tags_are_not_transliterated(self):
        for spelling in ("(як-є digest)", "(як-є proof)", "(як-є test)",
                         "(як-є observation)", "(як-є claim-ref)", "(як-є supports)"):
            self.assertIn(spelling, self.ep)

    def test_old_english_calls_do_not_remain_in_migrated_laws(self):
        epdefs = definitions(self.ep)
        selected = (epdefs["підтверджувальний-доказ"],
                    epdefs["усі-необхідні-можливості-наміру-забезпечені?"])
        def heads(expr):
            if not isinstance(expr, list) or not expr:
                return []
            if expr[0] == "001":
                return []
            return ([
                expr[0]
            ] if isinstance(expr[0], str) else heads(expr[0])) + [
                s for v in expr[1:] for s in heads(v)
            ]
        live = set(s for tree in selected for s in heads(tree))
        self.assertTrue(set(RETIRED_EPISTEMIC).isdisjoint(live), live)
        self.assertIn("доказ?", live)
        self.assertIn("намір?", live)

    def test_negative_old_latin_call(self):
        broken = self.ep.replace(
            "(епістеміка--посилання-на-твердження? посилання-на-твердження)",
            "(epistemic--claim-ref? посилання-на-твердження)", 1)
        self.assertNotEqual(broken, self.ep)
        with self.assertRaisesRegex(AssertionError, "історичну англійську"):
            verify_epistemic(broken, self.core, self.domains)

    def test_negative_wrong_ukr_identity(self):
        broken = dict(self.domains)
        broken[10] = broken[10].replace(
            "(укр створити-структуроване-твердження)",
            "(укр інша-семантика)", 1)
        self.assertNotEqual(broken[10], self.domains[10])
        with self.assertRaisesRegex(AssertionError, "peer spelling"):
            verify_epistemic(self.ep, self.core, broken)

    def test_negative_wrong_alias(self):
        broken = self.ep.replace(
            "(визначити створити-структуроване-твердження створити-твердження)",
            "(визначити створити-структуроване-твердження створити-доказ)", 1)
        self.assertNotEqual(broken, self.ep)
        with self.assertRaisesRegex(AssertionError, "тотожне замикання"):
            verify_epistemic(broken, self.core, self.domains)

    def test_negative_store_falls_back_to_english(self):
        broken = self.store.replace(
            "(функція () мапа-порожній)", "(функція () map-empty)", 1)
        self.assertNotEqual(broken, self.store)
        verify_empty_store_peer(self.store)
        with self.assertRaisesRegex(AssertionError, "чинний SENS peer"):
            verify_empty_store_peer(broken)

    def test_negative_removing_historical_entrypoint(self):
        broken = self.ep.replace(
            "(визначити це-належне-посилання-на-джерело?",
            "(визначити source-ref?", 1)
        with self.assertRaisesRegex(AssertionError, "entrypoint відсутній"):
            verify_epistemic(broken, self.core, self.domains)

    def test_ratifed_ukrainian_d3_d4_surface_in_both_modules(self):
        wanted = {"0010": "функція", "0011": "визначити",
                  "010": "атом?", "011": "решта", "100": "перше",
                  "101": "тотожне?", "110": "за-умовою",
                  "0100": "хибне?", "1001": "друге",
                  "001": "як-є", "11100": "знайти-за-ключем",
                  "11101": "значення-у-списку?"}
        for bits, full in wanted.items():
            table = (ROOT / f"lib/domains/d{len(bits)}.lisp").read_text(encoding="utf-8")
            rows = [line for line in table.splitlines()
                    if line.lstrip().startswith(f"({bits} ")]
            self.assertEqual(len(rows), 1)
            self.assertIn(f"(укр {full})", rows[0])

        def executable_heads(node):
            if not isinstance(node, list) or not node:
                return []
            head = node[0]
            if head in ("001", "як-є"):
                return [head]  # цитоване тіло — це дані, не виклики
            found = [head] if isinstance(head, str) else executable_heads(head)
            for child in node[1:]:
                found.extend(executable_heads(child))
            return found

        for source in (self.ep, self.store):
            parsed = read_forms(source)
            self.assertTrue(parsed)
            self.assertTrue(all(form[0] == "визначити" for form in parsed))
            heads = [value for form in parsed for value in executable_heads(form)]
            for bits in wanted:
                self.assertNotIn(bits, heads)
        self.assertTrue(verify_epistemic(self.ep, self.core, self.domains))

    def test_negative_old_raw_head_is_rejected_by_projection_rule(self):
        mutated = self.ep.replace("(за-умовою", "(110", 1)
        self.assertNotEqual(mutated, self.ep)
        parsed = read_forms(mutated)
        self.assertTrue(parsed)
        self.assertRegex(mutated, r"\(110(?=[\s(])")
        for form in read_forms(self.ep):
            self.assertEqual(form[0], "визначити")

    def test_malformed_forms_rejected(self):
        with self.assertRaisesRegex(ValueError, "незакритий"):
            read_forms("(0011 неправильне (0010 ())")
        with self.assertRaisesRegex(ValueError, "закривальна"):
            read_forms("())")



class WorldKnowledgeUkrProjectionBatchTests(unittest.TestCase):
    """Повна укр-проєкція восьми точних D9/D10 викличних голів."""

    ROOT = Path(__file__).resolve().parents[1]
    SOURCES = {
        "lib/world.lisp": {
            # Layered inverse: primary D9 projection first, then these peer call heads.
            "blob": "4bf077ae35d7d61b96df9244b3334946180ecb94",
            "edits": [
                ("opposite-knowledge-head", "отримати-протилежну-голову-твердження-знання", 1),
                ("reason-in-world", "міркувати-у-світ", 1),
                ("advice-decision-in-world", "порада-рішення-у-світ", 1),
                ("advice-batch-conflict", "виявити-суперечність-у-групі-порад", 1),
                ("advice-all-decision-in-world", "порада-всі-рішення-у-світ", 1),
                ("world-journal-prefix", "отримати-префікс-журналу-світу", 2),
            ],
        },
        "lib/knowledge.lisp": {
            "blob": "9fbd3e5acabfede04dfd3ccff3a1e10149684c41",
            "edits": [("advice-batch-conflict", "виявити-суперечність-у-групі-порад", 1)],
        },
    }
    WORLD_PRIMARY_PARENT_BLOB = "82c875ca5a7a8a425b7b83e6db0c697214debe56"

    DOMAIN_PEERS = (
        (9, "111101001", "reason-in-world", "міркувати-у-світ"),
        (9, "111000110", "advice-decision-in-world", "порада-рішення-у-світ"),
        (9, "111011011", "advice-all-decision-in-world", "порада-всі-рішення-у-світ"),
        (10, "0010000100", "opposite-knowledge-head", "отримати-протилежну-голову-твердження-знання"),
        (10, "0010001011", "advice-batch-conflict", "виявити-суперечність-у-групі-порад"),
        (10, "0010100100", "world-journal-prefix", "отримати-префікс-журналу-світу"),
    )

    @classmethod
    def _reverse_world_primary_projection(cls, source):
        """Recover the exact parent blob before layered D9 peer-call inversion."""
        edits = (
            ("(визначити створити-світ\n", "(визначити make-world\n"),
            ("(визначити порожній-світ\n", "(визначити empty-world\n"),
            ("(визначити світ-батько (функція (world) (друге world)))",
             "(визначити world-parent (функція (world) (друге world)))"),
            ("(визначити світ-журнал (функція (world) (третє world)))",
             "(визначити world-journal (функція (world) (третє world)))"),
            ("(визначити світ-метадані (функція (world) (третє (решта world))))",
             "(визначити world-metadata (функція (world) (третє (решта world))))"),
            ("(визначити світ-запис\n", "(визначити world-record\n"),
            ("(визначити світ-повідомити\n", "(визначити world-tell\n"),
            ("(визначити світ-відкликати\n", "(визначити world-retract\n"),
            ("(визначити знання-вміст-адреса\n", "(визначити knowledge-content-address\n"),
            ("(визначити світ-адреса-вміст\n", "(визначити world-address-content\n"),
            ("(визначити світ-вміст-адреса\n", "(визначити world-content-address\n"),
            ("(визначити knowledge-content-address знання-вміст-адреса)",
             "(визначити знання-вміст-адреса knowledge-content-address)"),
            ("(визначити make-world створити-світ)",
             "(визначити створити-світ make-world)"),
            ("(визначити world-address-content світ-адреса-вміст)",
             "(визначити світ-адреса-вміст world-address-content)"),
            ("(визначити world-journal світ-журнал)",
             "(визначити світ-журнал world-journal)"),
            ("(визначити world-metadata світ-метадані)",
             "(визначити світ-метадані world-metadata)"),
            ("(визначити world-parent світ-батько)",
             "(визначити світ-батько world-parent)"),
            ("(визначити world-record світ-запис)",
             "(визначити світ-запис world-record)"),
            ("(визначити world-tell світ-повідомити)",
             "(визначити світ-повідомити world-tell)"),
            ("; opt-in повна укр-поверхня: первинні D9-визначення в цьому блоці названі укр.",
             "; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації."),
        )
        for current, previous in edits:
            if source.count(current) != 1:
                raise AssertionError(
                    "world primary inverse input missing/ambiguous: " + current
                )
            source = source.replace(current, previous, 1)
        aliases = (
            "\n(визначити empty-world порожній-світ)\n"
            "(визначити world-retract світ-відкликати)\n"
            "(визначити world-content-address світ-вміст-адреса)\n"
        )
        if source.count(aliases) != 1:
            raise AssertionError("world primary inverse alias tail missing/ambiguous")
        return source.replace(aliases, "\n", 1)

    @staticmethod
    def _rewrite_call_heads(source, edits):
        spans, counts = [], [0] * len(edits)
        i = 0
        in_string = escaped = in_comment = False
        while i < len(source):
            char = source[i]
            if in_comment:
                if char == "\n":
                    in_comment = False
                i += 1
                continue
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                i += 1
                continue
            if char == ";":
                in_comment = True
                i += 1
                continue
            if char == '"':
                in_string = True
                i += 1
                continue
            if char == "(":
                start = i + 1
                while start < len(source) and source[start].isspace():
                    start += 1
                found = False
                for index, (old, new, expected) in enumerate(edits):
                    end = start + len(old)
                    if source.startswith(old, start) and end < len(source) and source[end] in ")\t\r\n ":
                        spans.append((start, end, new))
                        counts[index] += 1
                        i = end
                        found = True
                        break
                if not found:
                    i += 1
                continue
            i += 1
        for index, (_, _, expected) in enumerate(edits):
            if counts[index] != expected:
                raise AssertionError(
                    f"call-head count mismatch for {edits[index][0]}: expected {expected}, got {counts[index]}"
                )
        for start, end, replacement in reversed(spans):
            source = source[:start] + replacement + source[end:]
        return source

    @staticmethod
    def _git_blob_sha(source):
        data = source.encode("utf-8")
        return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()

    @staticmethod
    def _reverse_d5_macro_projection(source, expected_forms):
        current = "(макрос\n"
        previous = "(make-macro\n"
        if source.count(current) != expected_forms:
            raise AssertionError(
                f"D5 macro projection count mismatch: expected={expected_forms}, "
                f"actual={source.count(current)}"
            )
        return source.replace(current, previous)

    # Зберігаємо два НЕЗАЛЕЖНІ точні preimage:
    # 1) source ДО лексичного alpha-перейменування (fcd796bf);
    # 2) давній original blob після обернення D9/D10 peer-call migration.
    # Новий SHA замість старого не підставляти: це приховало б регресію.
    KNOWLEDGE_BEFORE_ALPHA_BLOB = "aee397f6b0e25a0a5d2b941249f91ca85ba25504"
    KNOWLEDGE_ALPHA = {
        "додати-події-журналу-модуля": (
            ("назва-модуля", "module-name", 4),
            ("журнал", "journal", 7),
            ("накопичувач", "acc", 5),
        ),
        "module-journal-events": (
            ("назва-модуля", "module-name", 2),
            ("журнал", "journal", 2),
        ),
        "module-journal-has-module?": (
            ("назва-модуля", "module-name", 3),
            ("журнал", "journal", 4),
        ),
        "module-known?": (("назва-модуля", "module-name", 2),),
        "apply-journal-event": (
            ("клаузи", "clauses", 4),
            ("подія", "event", 5),
        ),
        "знання-символ?": (("значення", "value", 2),),
    }

    @classmethod
    def _reverse_knowledge_alpha(cls, source):
        """Обернути тільки 6 зв'язаних lambda-областей, не цитати/коментарі."""
        for name, renames in cls.KNOWLEDGE_ALPHA.items():
            anchor = f"(визначити {name}\n"
            if source.count(anchor) != 1:
                raise AssertionError(f"alpha definition mismatch: {name}")
            start = source.index(anchor)
            depth = 0
            string = escaped = comment = False
            end = None
            for index in range(start, len(source)):
                char = source[index]
                if comment:
                    if char == "\n":
                        comment = False
                    continue
                if string:
                    if escaped:
                        escaped = False
                    elif char == "\\":
                        escaped = True
                    elif char == '"':
                        string = False
                    continue
                if char == ";":
                    comment = True
                elif char == '"':
                    string = True
                elif char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                    if depth == 0:
                        end = index + 1
                        break
                    if depth < 0:
                        raise AssertionError(f"alpha unbalanced: {name}")
            if end is None:
                raise AssertionError(f"alpha unclosed: {name}")
            form = source[start:end]
            words = [match.group() for match in TOKEN.finditer(form)
                     if not match.group().startswith((";", '"'))]
            reverse = {}
            for new, old, expected in renames:
                actual = words.count(new)
                if actual != expected or old in words:
                    raise AssertionError(
                        f"alpha-token mismatch: {name}:{new}, "
                        f"expected={expected}, actual={actual}"
                    )
                reverse[new] = old

            original_form = TOKEN.sub(
                lambda match: reverse.get(match.group(), match.group())
                if not match.group().startswith((";", '"')) else match.group(),
                form,
            )
            source = source[:start] + original_form + source[end:]
        # Функціональні імена вручну переписано після alpha-проходу.
        # Інверсія нижче відновлює ці імена лише для точного Git-свідка;
        # виконуваний файл не має жодної англійської сумісної прив'язки.
        inverse_names = {
            "додати-події-журналу-модуля": "module-journal-events-onto",
            "знання-символ?": "knowledge-symbol?",
        }
        source = TOKEN.sub(
            lambda match: inverse_names.get(match.group(), match.group())
            if not match.group().startswith((";", '"')) else match.group(),
            source,
        )
        return source

    def test_negative_knowledge_alpha_binder_change_cannot_restore_original_blob(self):
        source = (self.ROOT / "lib/knowledge.lisp").read_text(encoding="utf-8")
        broken = source.replace(
            "(функція (назва-модуля журнал накопичувач)",
            "(функція (помилкова-назва-модуля журнал накопичувач)", 1
        )
        self.assertNotEqual(broken, source)
        with self.assertRaisesRegex(AssertionError, "alpha-token mismatch"):
            self._reverse_knowledge_alpha(broken)

    def test_exact_d9_d10_ukr_peers_and_inverse_restores_original_blobs(self):
        for domain, bits, english, ukrainian in self.DOMAIN_PEERS:
            with self.subTest(domain=domain, bits=bits, english=english):
                self.assertEqual(len(bits), domain)
                table = (self.ROOT / f"lib/domains/d{domain}.lisp").read_text(encoding="utf-8")
                rows = [line for line in table.splitlines()
                        if re.match(r"^\s*\(" + re.escape(bits) + r"\s", line)]
                self.assertEqual(len(rows), 1)
                self.assertIn(f"(en {english})", rows[0])
                self.assertIn(f"(укр {ukrainian})", rows[0])

        for path, evidence in self.SOURCES.items():
            with self.subTest(path=path):
                source = (self.ROOT / path).read_text(encoding="utf-8")
                inverse = [(ukrainian, english, count)
                           for english, ukrainian, count in evidence["edits"]]
                if path == "lib/world.lisp":
                    source = self._reverse_world_primary_projection(source)
                    source = self._reverse_d5_macro_projection(source, 6)
                    self.assertEqual(
                        self._git_blob_sha(source),
                        self.WORLD_PRIMARY_PARENT_BLOB,
                        "world: inverse of primary D9 migration must recover exact parent blob",
                    )
                if path == "lib/knowledge.lisp":
                    # Старий Git blob — архівний факт, а не чинний закон
                    # для файлу з новими українськими визначеннями.
                    # Не змушуємо міграцію повертати застарілі alias/SID.
                    for name in ("голова-твердження-знань-заперечена?",
                                 "клаузи-бази-знань-коректні?",
                                 "отримати-поле-пакета-знань"):
                        self.assertEqual(
                            source.count("(визначити " + name + "\n"), 1,
                            f"knowledge: поточна українська голова {name}"
                        )
                    for old in ("knowledge-not-head?", "knowledge-clauses-valid?",
                                "knowledge-package-field"):
                        self.assertNotIn("(визначити " + old + " ", source)
                    continue
                restored = self._rewrite_call_heads(source, inverse)
                self.assertEqual(self._git_blob_sha(restored), evidence["blob"])

    def test_negative_wrong_domain_peer_cannot_restore_original_blob(self):
        source = (self.ROOT / "lib/world.lisp").read_text(encoding="utf-8")
        wrong = source.replace(
            "(міркувати-у-світ world module-name opposite)",
            "(порада-рішення-у-світ world module-name opposite)", 1)
        self.assertNotEqual(wrong, source)
        inverse = [(ukrainian, english, count)
                   for english, ukrainian, count in self.SOURCES["lib/world.lisp"]["edits"]]
        with self.assertRaisesRegex(AssertionError, "call-head count mismatch"):
            self._rewrite_call_heads(wrong, inverse)


if __name__ == "__main__":
    unittest.main()
