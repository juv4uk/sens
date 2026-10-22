"""Незалежний AST-свідок для Advice Taker + 2046 доменних координат.

Доводимо 3 D3 guards і незмінність 8 source-функцій після вилучення
трьох нових перших клауз. Механізм виконання перевіряє Rust job окремо.
"""
from copy import deepcopy
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/understand.lisp"
TOKENS = re.compile(r';[^\n]*|"(?:\\.|[^"\\])*"|[()]|[^\s();]+')
GUARDED = {"strip-article", "understand", "understand-query"}
LET_REDUCED = {"understand-is", "understand-universal", "understand-query-is"}
# Frozen original D6 LET forms from main@c18ca3e2 (before any changes).
FROZEN_LETS = {
    "understand-is": """(0011 understand-is
      (0010 (words)
        (001000 ((subject (100 words))
                  (after-is (strip-article (0111 words))))
          (1110 (1110 (100 after-is) subject)))))""",
    "understand-universal": """(0011 understand-universal
      (0010 (words)
        (001000 ((subject-class (1001 words))
                  (property (100111 words)))
          (1110 (1110 (001 has) (1110 (001 var) (001 w)) property)
                (1110 subject-class (1110 (001 var) (001 w)))))))""",
    "understand-query-is": """(0011 understand-query-is
      (0010 (words)
        (001000 ((subject (1001 words))
                  (after (0111 words)))
          (1110 (100 (strip-article after)) subject))))""",
}
FROZEN = {
    "strip-article": "db88279d0f09812f",
    "understand-is": "c496864af8ccff2c",
    "understand-relation": "c4e51fdb4bfe9317",
    "understand-universal": "730247ec3b359011",
    "understand": "420149e09343a899",
    "understand-query-is": "12138acbeb6d89f6",
    "understand-query-relation": "6dd63349949d36fd",
    "understand-query": "a267fbc6d7ca58d6",
}
MASK = (1 << 64) - 1


def read_forms(source):
    words = [m.group() for m in TOKENS.finditer(source)
             if not m.group().startswith(";")]
    pos = 0

    def read():
        nonlocal pos
        if pos >= len(words):
            raise AssertionError("неповний S-expression")
        word = words[pos]
        pos += 1
        if word == ")":
            raise AssertionError("зайва )")
        if word != "(":
            return word
        values = []
        while pos < len(words) and words[pos] != ")":
            values.append(read())
        if pos >= len(words):
            raise AssertionError("незакрита форма")
        pos += 1
        return values

    result = []
    while pos < len(words):
        result.append(read())
    return result


def canonical(node):
    return "(" + " ".join(map(canonical, node)) + ")" if isinstance(node, list) else node


def digest(node):
    h = 0xCBF29CE484222325
    for char in canonical(node):
        h = ((h ^ ord(char)) * 0x100000001B3) & MASK
    return f"{h:016x}"



# Chosen CURRENT `укр` peers of executable D1/D3/D4/D5/D6 operators.
# These spellings are checked independently against each exact-width table.
CURRENT_HEADS = {
    "як-є": "001", "атом?": "010", "решта": "011",
    "перше": "100", "тотожне?": "101",
    "за-умовою": "110", "сполучити": "111",
    "функція": "0010", "визначити": "0011",
    "хибне?": "0100", "порожній?": "0101",
    "решта-решти": "0111", "друге": "1001",
    "список": "1110", "третє": "10011", "четверте": "100111",
}
LOCAL_HELPERS = {
    "прибрати-артикль": "strip-article",
    "побудувати-факт-є": "understand-is",
    "побудувати-факт-відношення": "understand-relation",
    "побудувати-універсальне-правило": "understand-universal",
    "розібрати-контрольоване-твердження": "understand",
    "побудувати-запит-є": "understand-query-is",
    "побудувати-запит-відношення": "understand-query-relation",
    "розібрати-контрольований-запит": "understand-query",
}
LOCAL_FORMALS = {
    "слова": "words",
    "підмет": "subject",
    "після-є": "after-is",
    "клас-підмета": "subject-class",
    "властивість": "property",
    "гілки": "clauses",
    "після": "after",
}
LOCAL_NAME_HISTORY = {**LOCAL_HELPERS, **LOCAL_FORMALS}
RESIDENT_HISTORY = {
    "розібрати-є": "understand-is",
    "розібрати-відношення": "understand-relation",
    "розібрати-загальний": "understand-universal",
    "розібрати": "understand",
    "розібрати-запит-є": "understand-query-is",
    "розібрати-запит-відношення": "understand-query-relation",
    "розібрати-запит": "understand-query",
}
HISTORICAL_RESIDENT_HEADS = set(RESIDENT_HISTORY.values())
SOURCE_ALIASES = {
    "розібрати-є": "побудувати-факт-є",
    "розібрати-відношення": "побудувати-факт-відношення",
    "розібрати-загальний": "побудувати-універсальне-правило",
    "розібрати": "розібрати-контрольоване-твердження",
    "розібрати-запит-є": "побудувати-запит-є",
    "розібрати-запит-відношення": "побудувати-запит-відношення",
    "розібрати-запит": "розібрати-контрольований-запит",
}

# Справжній доданий кореневий SENS-виклик — не дев'ятий DEFINE і не D9 alias.
# Вимагати точний позитивний вхід; довільне дописування форм не приймаємо.
SOURCE_WITNESS = ["прибрати-артикль", ["як-є", ["кіт", "собака"]]]


def normalize_current_source_forms(source_forms):
    """Strict inverse ONLY for canonical operator positions; QUOTE data is opaque."""
    if len(source_forms) != len(FROZEN) + len(SOURCE_ALIASES) + 1:
        raise AssertionError("очікуються 8 законів, 7 D9-аліасів і один SENS-виклик")
    definitions = source_forms[:len(FROZEN)]
    aliases = source_forms[len(FROZEN):len(FROZEN) + len(SOURCE_ALIASES)]
    if source_forms[-1] != SOURCE_WITNESS:
        raise AssertionError("кінцевий SENS-виклик змінено або замінено даними")
    if {row[1] for row in definitions} != set(LOCAL_HELPERS):
        raise AssertionError("втрачене, дубльоване або неукраїнське локальне визначення")
    if any(not isinstance(row, list) or len(row) != 3
           or row[0] != "визначити" for row in aliases):
        raise AssertionError("неправильна форма D9-аліаса")
    if {tuple(row[1:]) for row in aliases} != set(SOURCE_ALIASES.items()):
        raise AssertionError("змінена чинна D9-проєкція/прив'язка")

    def lower(node):
        if isinstance(node, str):
            return {"так": "#d1:1", "ні": "#d1:0"}.get(
                node, LOCAL_NAME_HISTORY.get(node, node)
            )
        if not node:
            return []
        head = node[0]
        if head == "як-є":
            # Do NOT touch data under QUOTE.
            return ["001"] + deepcopy(node[1:])
        if isinstance(head, str) and head in CURRENT_HEADS:
            return [CURRENT_HEADS[head]] + [lower(x) for x in node[1:]]
        # Поточні D9-імена та україномовні помічники інвертуються
        # лише в копії для звірки історичного AST.
        if isinstance(head, str) and head in RESIDENT_HISTORY:
            return [RESIDENT_HISTORY[head]] + [lower(x) for x in node[1:]]
        if isinstance(head, str) and head in LOCAL_HELPERS:
            return [LOCAL_HELPERS[head]] + [lower(x) for x in node[1:]]
        if isinstance(head, str) and head in HISTORICAL_RESIDENT_HEADS:
            raise AssertionError("застаріла латинська виклична голова: " + head)
        if isinstance(head, str) and re.fullmatch(r"[01]{3,6}", head):
            raise AssertionError("старий виконавчий бітовий голов лишився: " + head)
        return [lower(x) for x in node]
    return [lower(node) for node in definitions]


def verify_unchanged_laws(forms):
    if len(forms) != 8:
        raise AssertionError("кількість основних функцій змінилася")
    names = set()
    for form in forms:
        if not (isinstance(form, list) and len(form) == 3
                and form[0] == "0011" and isinstance(form[1], str)):
            raise AssertionError("визначення має лишатися D4:0011")
        name = form[1]
        if name in names or name not in FROZEN:
            raise AssertionError("невідома/дубльована функція")
        names.add(name)
        original = deepcopy(form)
        if name in ("understand-universal", "understand-query-relation"):
            # Перевіряємо чинні захисні гілки SENS; лише в копії AST
            # знімаємо їх для історичного закону на повних даних.
            lam = original[2]
            cond = lam[2]
            guards = (
                [["010", "words"], ["001", []]],
                [["010", ["011", "words"]], ["001", []]],
                [["010", ["011", ["011", "words"]]], ["001", []]],
                [["010", ["011", ["011", ["011", "words"]]]], ["001", []]],
            )
            if (not isinstance(cond, list) or cond[0] != "110"
                    or tuple(cond[1:5]) != guards
                    or len(cond) != 6
                    or cond[5][0] != ["010", ["001", []]]):
                raise AssertionError("захист четвертого слова має точний D3 закон")
            lam[2] = cond[5][1]
        if name in GUARDED:
            lam = original[2]
            if not (isinstance(lam, list) and lam[0] == "0010"
                    and isinstance(lam[2], list) and lam[2][0] == "110"):
                raise AssertionError("невалідна D4 λ / D3 COND")
            clauses = lam[2][1:]
            if not clauses or clauses[0] != [["010", "words"], ["001", []]]:
                raise AssertionError("непорожній CAR до точного D3 ATOM")
            lam[2].pop(1)
            if name in ("understand", "understand-query"):
                # Перевірка актуальних D3 захистів короткого списку.
                # Із копії AST їх прибираємо тільки при звірці
                # законів для повних програм, не у виконуваному Lisp.
                guards = (
                    [["010", ["011", "words"]], ["001", []]],
                    [["010", ["011", ["011", "words"]]], ["001", []]],
                )
                for guard in guards:
                    if len(lam[2]) < 2 or lam[2][1] != guard:
                        raise AssertionError("неповний список має D3-захист до селекторів")
                    lam[2].pop(1)
            # Поточний D1:YES ОБЧИСЛЮЄТЬСЯ SENS: D3 ATOM(D3 QUOTE NIL).
            # Історичний frozen AST уже містив цей самий закон, тому
            # його не можна замінювати текстовим #d1 чи host-булевим.
            fallback = lam[2][-1]
            if not (isinstance(fallback, list)
                    and len(fallback) == 2
                    and fallback[0] == ["010", ["001", []]]):
                raise AssertionError("відсутній точний D1:YES у COND")
        if name in LET_REDUCED:
            # Незалежна beta-редукція історичного D6 LET з frozen main:
            # обидва binding-вирази чисті та кожен параметр вжито лише раз.
            frozen = read_forms(FROZEN_LETS[name])
            if len(frozen) != 1 or digest(frozen[0]) != FROZEN[name]:
                raise AssertionError("історичний контрольний AST/sha втрачено")
            old_let = frozen[0][2][2]
            if old_let[0] != "001000" or len(old_let[1]) != 2:
                raise AssertionError("історичний D6 LET має два зв'язування")
            binding = {item[0]: item[1] for item in old_let[1]}
            params = set(binding)
            def uses(node):
                if isinstance(node, list):
                    return sum(uses(child) for child in node)
                return 1 if node in params else 0
            if uses(old_let[2]) != 2:
                raise AssertionError("beta-редукція змінила використання")
            def substitute(node):
                if isinstance(node, list):
                    return [substitute(child) for child in node]
                return deepcopy(binding[node]) if node in binding else node
            expected = substitute(old_let[2])
            if original[2][2] != expected:
                raise AssertionError("неточна підстановка D6 LET у чисту D3/D4 композицію")
        elif digest(original) != FROZEN[name]:
            raise AssertionError("історичне тіло змінено: " + name)
    if names != set(FROZEN):
        raise AssertionError("втрачено визначення")
    return forms


def catalog():
    records = []
    for width in range(1, 11):
        source = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
        rows = re.findall(r"(?m)^  \(([01]+) (.*)$", source)
        records.extend((width, binary, rest) for binary, rest in rows)
    return records


def verify_catalog(records):
    if len(records) != 2046:
        raise AssertionError("не всі D1–D10: 2046")
    seen = set()
    start = 0
    order = ("(ук ", "(укр ", "(san ", "(en ", "(LISP ", "(sym ")
    for width in range(1, 11):
        expected = [format(v, f"0{width}b") for v in range(1 << width)]
        rows = records[start:start + (1 << width)]
        if [b for _, b, _ in rows] != expected or any(w != width for w, _, _ in rows):
            raise AssertionError(f"D{width}: втрачено точні leading zeros/порядок")
        for w, b, body in rows:
            key = w, b
            if key in seen:
                raise AssertionError("дубль доменної координати")
            seen.add(key)
            places = [body.find(s) for s in order]
            if min(places) < 0 or places != sorted(places):
                raise AssertionError("бракує проєкції uk/укр/sa/en/LISP/sym")
        start += 1 << width
    return seen


class UnderstandExactD3Witness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_forms = read_forms(SOURCE.read_text(encoding="utf-8"))
        cls.forms = normalize_current_source_forms(cls.source_forms)

    def test_source_is_current_ukrainian_with_exact_domain_peers(self):
        rows = ((3, "001", "як-є"), (3, "010", "атом?"),
                (3, "011", "решта"), (3, "100", "перше"),
                (3, "101", "тотожне?"), (3, "110", "за-умовою"),
                (3, "111", "сполучити"), (4, "0010", "функція"),
                (4, "0011", "визначити"), (4, "0100", "хибне?"),
                (4, "0101", "порожній?"), (4, "0111", "решта-решти"),
                (4, "1001", "друге"), (4, "1110", "список"),
                (5, "10011", "третє"), (6, "100111", "четверте"),
                (1, "1", "так"))
        for width, bits, ukr in rows:
            with self.subTest(domain=width, bits=bits):
                source = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
                matches = [line for line in source.splitlines()
                           if line.strip().startswith(f"({bits} (ук ")]
                self.assertEqual(len(matches), 1)
                self.assertIn(f"(укр {ukr})", matches[0])
        verify_unchanged_laws(self.forms)

    def test_five_current_d9_call_peers_and_negative_old_head(self):
        # Ратифікована координата + реальна Lisp-closure, не W8→D8.
        current = {
            "000001011": "розібрати-є",
            "000001100": "розібрати-відношення",
            "000011111": "розібрати-загальний",
            "000110000": "розібрати-запит-відношення",
            "000111001": "розібрати-запит-є",
        }
        source = (ROOT / "lib/domains/d9.lisp").read_text(encoding="utf-8")
        for bits, ukr in current.items():
            with self.subTest(bits=bits):
                rows = [line for line in source.splitlines()
                        if line.lstrip().startswith(f"({bits} (ук ")]
                self.assertEqual(len(rows), 1)
                self.assertIn(f"(укр {ukr})", rows[0])
        # Кожна з п'яти голів з'являється рівно в одному виконуваному місці.
        def heads(node):
            if not isinstance(node, list):
                return []
            return ([node[0]] if node and isinstance(node[0], str) else []
                    ) + [v for child in node for v in heads(child)]
        executed = [h for form in self.source_forms[:8] for h in heads(form)]
        for peer in current.values():
            self.assertEqual(executed.count(peer), 1, peer)
        verify_unchanged_laws(self.forms)  # frozen 8 historic digest proofs
        mutant = deepcopy(self.source_forms)
        # Навіть одна зворотна латинська голова порушує міграційний контракт.
        for form in mutant[:8]:
            if form[1] == "розібрати-контрольоване-твердження":
                form[2][2][2][1][0] = "understand-universal"
                break
        with self.assertRaisesRegex(AssertionError, "застаріла латинська"):
            normalize_current_source_forms(mutant)

    def test_negative_wrong_ukr_function_and_wrong_d1_fallback(self):
        bad_head = deepcopy(self.source_forms)
        bad_head[0][2][2][1][0][0] = "тотожне?"
        with self.assertRaisesRegex(AssertionError, "непорожній CAR"):
            verify_unchanged_laws(normalize_current_source_forms(bad_head))
        bad_d1 = deepcopy(self.source_forms)
        bad_d1[0][2][2][-1][0] = "ні"
        with self.assertRaisesRegex(AssertionError, "точний D1:YES"):
            verify_unchanged_laws(normalize_current_source_forms(bad_d1))
        # Справжній однобітний семантичний мутант: ATOM(QUOTE NIL)
        # дає D1:YES, а ATOM(QUOTE (NIL)) мусить дати D1:NO.
        # Перевіряємо саме дерево SENS, не буквальне слово «так».
        bad_false = deepcopy(self.source_forms)
        fallback_condition = bad_false[0][2][2][-1][0]
        self.assertEqual(fallback_condition, ["атом?", ["як-є", []]])
        fallback_condition[1][1] = [[]]
        with self.assertRaisesRegex(AssertionError, "точний D1:YES"):
            verify_unchanged_laws(normalize_current_source_forms(bad_false))
        bad_legacy = deepcopy(self.source_forms)
        bad_legacy[0][0] = "0011"
        with self.assertRaisesRegex(AssertionError, "старий виконавчий"):
            normalize_current_source_forms(bad_legacy)

    def test_all_local_helpers_and_formals_use_full_ukr_names(self):
        definitions = self.source_forms[:len(FROZEN)]
        self.assertEqual({form[1] for form in definitions}, set(LOCAL_HELPERS))
        self.assertTrue(all(form[2][1] == ["слова"] for form in definitions))
        self.assertEqual(
            {tuple(form[1:]) for form in self.source_forms[
                len(FROZEN):len(FROZEN) + len(SOURCE_ALIASES)]},
            set(SOURCE_ALIASES.items()),
        )
        self.assertEqual(self.source_forms[-1], SOURCE_WITNESS)

    def test_negative_changed_or_duplicate_executable_witness(self):
        for mutation in ("замінений", "продубльований"):
            with self.subTest(mutation=mutation):
                bad = deepcopy(self.source_forms)
                if mutation == "замінений":
                    bad[-1][0] = "решта"
                    message = "кінцевий SENS-виклик"
                else:
                    bad.append(deepcopy(SOURCE_WITNESS))
                    message = "очікуються 8 законів"
                with self.assertRaisesRegex(AssertionError, message):
                    normalize_current_source_forms(bad)

    def test_all_eight_functions_preserve_original_laws(self):
        verify_unchanged_laws(self.forms)

    def test_three_empty_guards_are_d3_not_legacy_w8(self):
        verify_unchanged_laws(self.forms)
        self.assertEqual(len(GUARDED), 3)
        self.assertEqual(3 * (len("010") + len("001")), 18)

    def test_negative_missing_fourth_word_guard(self):
        for name in ("understand-universal", "understand-query-relation"):
            with self.subTest(function=name):
                mutated = deepcopy(self.forms)
                definition = next(form for form in mutated if form[1] == name)
                definition[2][2].pop(4)
                with self.assertRaisesRegex(AssertionError, "захист четвертого слова"):
                    verify_unchanged_laws(mutated)

    def test_negative_missing_guard(self):
        mutated = deepcopy(self.forms)
        mutated[0][2][2].pop(1)
        with self.assertRaisesRegex(AssertionError, "непорожній CAR"):
            verify_unchanged_laws(mutated)

    def test_negative_missing_short_word_list_guard(self):
        for name in ("understand", "understand-query"):
            with self.subTest(function=name):
                mutated = deepcopy(self.forms)
                definition = next(form for form in mutated if form[1] == name)
                definition[2][2].pop(2)
                with self.assertRaisesRegex(AssertionError, "неповний список має D3-захист"):
                    verify_unchanged_laws(mutated)

    def test_negative_legacy_8bit_or_wrong_d1_result(self):
        for bad in ["00000101", "1"]:
            mutated = deepcopy(self.forms)
            mutated[0][2][2][1][0][0] = bad
            with self.assertRaisesRegex(AssertionError, "D3 ATOM"):
                verify_unchanged_laws(mutated)

    def test_three_d6_let_forms_beta_reduce_to_existing_d3_d4(self):
        verify_unchanged_laws(self.forms)
        # 3× (ATOM + QUOTE) guards cost 18 bits; three D6 LET
        # heads disappear entirely, saving 18 operator-head bits.
        self.assertEqual(3 * (len("010") + len("001")) - 3 * len("001000"), 0)

    def test_negative_legacy_d6_let_reintroduction(self):
        mutated = deepcopy(self.forms)
        definition = next(form for form in mutated if form[1] == "understand-is")
        definition[2][2] = ["001000", [["subject", ["100", "words"]],
                                       ["after-is", ["strip-article", ["0111", "words"]]]],
                            ["1110", ["1110", ["100", "after-is"], "subject"]]]
        with self.assertRaisesRegex(AssertionError, "неточна підстановка"):
            verify_unchanged_laws(mutated)

    def test_negative_mutated_original_function_body(self):
        mutated = deepcopy(self.forms)
        mutated[2][2][2][0] = "001"
        with self.assertRaisesRegex(AssertionError, "історичне тіло"):
            verify_unchanged_laws(mutated)

    def test_all_2046_exact_coordinates_and_six_surfaces(self):
        rows = catalog()
        coords = verify_catalog(rows)
        self.assertEqual(len(coords), 2046)
        self.assertEqual(len(set(int(bits, 2) for _, bits in coords)), 1024)

    def test_negative_w10_to_w9_truncation(self):
        rows = catalog()
        verify_catalog(rows)
        mutated = list(rows)
        i = next(i for i, (w, b, _) in enumerate(mutated) if w == 10 and b == "1111111111")
        mutated[i] = (9, "111111111", mutated[i][2])
        with self.assertRaisesRegex(AssertionError, "D10"):
            verify_catalog(mutated)

    def test_negative_missing_linguistic_projection(self):
        rows = catalog()
        w, b, text = rows[-1]
        rows[-1] = (w, b, text.replace("(san ", "(sans ", 1))
        with self.assertRaisesRegex(AssertionError, "проєкції"):
            verify_catalog(rows)


if __name__ == "__main__":
    unittest.main()
