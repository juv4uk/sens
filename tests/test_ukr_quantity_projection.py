"""Quantity: exact D1/D3–D6 ukr source projection, not a Python SENS evaluator."""
from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/quantity.lisp"
BASE_BLOB = "e06af39b35862b3f993009fbcff17e5649fa2d56"
NATIVE = {
    3: {"001": "як-є", "010": "атом?", "011": "решта", "100": "перше",
        "101": "тотожне?", "110": "за-умовою", "111": "сполучити"},
    4: {"0010": "функція", "0011": "визначити", "0101": "порожній?",
        "1001": "друге", "1110": "список", "1111": "приєднати"},
    5: {"01011": "відняти", "10011": "третє"},
    6: {"001000": "нехай", "100111": "четверте"},
}
HEAD_COUNTS = {
    "100": 7, "101": 34, "110": 12, "1001": 6, "1110": 20,
    "10011": 6, "100111": 2, "0011": 37, "001": 69, "0010": 33,
    "010": 7, "011": 15, "01011": 1,
}
D1_LITERAL_COUNTS = {"#d1:1": 19}
MAP = {bits: name for table in NATIVE.values() for bits, name in table.items()}
REVERSE = {name: bits for bits, name in MAP.items()}
D1 = {"#d1:1": "так", "#d1:0": "ні"}
D1_REVERSE = {value: key for key, value in D1.items()}
D9 = {"110101100": "символ?", "110110101": "п'ятий"}
D9_REVERSE = {name: bits for bits, name in D9.items()}
FALSE_EXPR = "(тотожне? (як-є (0)) (як-є (1)))"
PRE_REPAIR_BLOB = "8ed44251876053a778837c7739427b7c20427026"

# Новий незалежний локальний шар. Він НЕ стає D9/D10 identity:
# English aliases в кінці файла посилаються на ті самі SENS-замикання.
LOCAL_QUANTITY_BLOB = "9baec7d8c33011bb52944cf0cd4cbe63e2910e8c"
LOCAL_HELPERS = (
    ("science-proper-list?", "науковий-список-правильний?", 7),
    ("science-list-length-equals?", "науковий-список-довжина-дорівнює?", 5),
    ("science-sixth", "науковий-шостий", 2),
    ("science-seventh", "науковий-сьомий", 2),
    ("science-source-authority", "авторитет-наукового-джерела", 1),
    ("science-source-edition", "видання-наукового-джерела", 1),
)
SCHEMA_ARCHIVE_BLOCK = "\n; Сумісні історичні імена схем залишаються зовнішніми\n; посиланнями на ті самі дані. Усі живі внутрішні звернення\n; вже використовують українські зв'язування.\n(визначити *dimension-schema* схема-розмірності)\n(визначити *unit-schema* схема-одиниці-виміру)\n(визначити *quantity-schema* схема-величини)\n(визначити *science-source-schema* схема-наукового-джерела)\n(визначити *scientific-constant-schema* схема-наукової-константи)\n"
QUANTITY_FORMALS = (
    ("науковий-список-правильний?", (("x", "значення", 4),)),
    ("науковий-список-довжина-дорівнює?", (("items", "елементи", 3), ("remaining", "залишок", 4))),
    ("науковий-шостий", (("values", "поля", 2),)),
    ("науковий-сьомий", (("values", "поля", 2),)),
    ("створити-розмірність", (("base", "основа", 2), ("exponent", "показник", 2))),
    ("розмірність-основа", (("dimension", "розмірність", 2),)),
    ("розмірність-показник", (("dimension", "розмірність", 2),)),
    ("створити-одиниця", (("dimensions", "розмірності", 2),)),
    ("одиниця-розмірності", (("unit", "одиниця", 2),)),
    ("створити-величина", (("value", "значення", 2), ("unit", "одиниця", 2))),
    ("величина-значення", (("quantity", "величина", 2),)),
    ("величина-одиниця", (("quantity", "величина", 2),)),
    ("створити-наука-джерело", (("authority", "авторитет", 2), ("edition", "видання", 2))),
    ("розмірність?", (("x", "значення", 6),)),
    ("одиниця-виміру?", (("x", "значення", 5),)),
    ("величина?", (("x", "значення", 6),)),
    ("наука-джерело?", (("x", "значення", 5),)),
    ("науковий-константа-стан-чинний?", (("status", "стан", 3),)),
    ("науковий-константа-вид-чинний?", (("kind", "вид", 3),)),
    ("створити-науковий-константа", (("name", "назва", 2), ("quantity", "величина", 2), ("status", "стан", 2), ("kind", "вид", 2), ("system", "система", 2), ("source", "джерело", 2))),
    ("науковий-константа?", (("x", "значення", 11),)),
    ("науковий-константа-ім'я", (("constant", "константа", 2),)),
    ("науковий-константа-величина", (("constant", "константа", 2),)),
    ("науковий-константа-значення", (("constant", "константа", 2),)),
    ("науковий-константа-одиниця", (("constant", "константа", 2),)),
    ("науковий-константа-стан", (("constant", "константа", 2),)),
    ("науковий-константа-вид", (("constant", "константа", 2),)),
    ("науковий-константа-система", (("constant", "константа", 2),)),
    ("науковий-константа-джерело", (("constant", "константа", 2),)),
    ("науковий-константа-клаузи", (("constant", "константа", 9), ("name", "назва", 8))),
    ("авторитет-наукового-джерела", (("source", "джерело", 2),)),
    ("видання-наукового-джерела", (("source", "джерело", 2),)),
)


def _rewrite_definition_atoms(source: str, function_name: str, edits) -> str:
    """Rename only bound local atoms in one exact Lisp definition."""
    anchors = list(re.finditer(
        r"(?m)^\(визначити\s+" + re.escape(function_name) + r"(?=\s|\))",
        source,
    ))
    if len(anchors) != 1:
        raise AssertionError(
            f"{function_name}: очікувалося одне визначення, знайдено {len(anchors)}"
        )
    start = anchors[0].start()
    depth = 0
    in_string = escaped = in_comment = False
    end = None
    for index in range(start, len(source)):
        char = source[index]
        if in_comment:
            if char == "\n":
                in_comment = False
            continue
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == ";":
            in_comment = True
        elif char == '"':
            in_string = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                end = index + 1
                break
            if depth < 0:
                raise AssertionError(f"{function_name}: незбалансоване визначення")
    if end is None:
        raise AssertionError(f"{function_name}: незакрите визначення")

    form = source[start:end]
    counts = {old: 0 for old, _new, _expected in edits}
    chunks = []
    index = 0
    while index < len(form):
        char = form[index]
        if char == ";":
            stop = form.find("\n", index)
            if stop < 0:
                stop = len(form)
            chunks.append(form[index:stop])
            index = stop
            continue
        if char == '"':
            stop = index + 1
            while stop < len(form):
                if form[stop] == "\\":
                    stop += 2
                elif form[stop] == '"':
                    stop += 1
                    break
                else:
                    stop += 1
            chunks.append(form[index:stop])
            index = stop
            continue
        if char.isspace() or char in "();'":
            chunks.append(char)
            index += 1
            continue
        stop = index
        while stop < len(form) and not form[stop].isspace() and form[stop] not in ("(", ")", ";", '"', "'"):
            stop += 1
        atom = form[index:stop]
        edit = next((item for item in edits if item[0] == atom), None)
        if edit is None:
            chunks.append(atom)
        else:
            chunks.append(edit[1])
            counts[atom] += 1
        index = stop
    for old, _new, expected in edits:
        if counts[old] != expected:
            raise AssertionError(
                f"{function_name}: кількість локальних атомів {old}: "
                f"очікувалося {expected}, знайдено {counts[old]}"
            )
    return source[:start] + "".join(chunks) + source[end:]


def project_quantity_formals(source: str) -> str:
    for name, edits in QUANTITY_FORMALS:
        source = _rewrite_definition_atoms(source, name, edits)
    return source


def restore_quantity_formals(source: str) -> str:
    for name, edits in QUANTITY_FORMALS:
        inverse = tuple((ukrainian, english, count) for english, ukrainian, count in edits)
        source = _rewrite_definition_atoms(source, name, inverse)
    return source


PUBLIC_PROJECTIONS = (
    ("make-dimension", "створити-розмірність", "111001100"),
    ("dimension?", "розмірність?", "111010000"),
    ("dimension-base", "розмірність-основа", "111101100"),
    ("dimension-exponent", "розмірність-показник", "111001101"),
    ("make-unit", "створити-одиниця", "111010001"),
    ("unit?", "одиниця-виміру?", "111000011"),
    ("unit-dimensions", "одиниця-розмірності", "111011100"),
    ("make-quantity", "створити-величина", "111001111"),
    ("quantity?", "величина?", "111000101"),
    ("quantity-value", "величина-значення", "111101000"),
    ("quantity-unit", "величина-одиниця", "111111001"),
    ("make-science-source", "створити-наука-джерело", "111110101"),
    ("science-source?", "наука-джерело?", "111011101"),
    ("scientific-constant-status-valid?", "науковий-константа-стан-чинний?", "111110010"),
    ("scientific-constant-kind-valid?", "науковий-константа-вид-чинний?", "111101111"),
    ("make-scientific-constant", "створити-науковий-константа", "111101110"),
    ("scientific-constant?", "науковий-константа?", "111111110"),
    ("scientific-constant-name", "науковий-константа-ім'я", "111000010"),
    ("scientific-constant-quantity", "науковий-константа-величина", "111101101"),
    ("scientific-constant-value", "науковий-константа-значення", "111010111"),
    ("scientific-constant-unit", "науковий-константа-одиниця", "111011001"),
    ("scientific-constant-status", "науковий-константа-стан", "111010010"),
    ("scientific-constant-kind", "науковий-константа-вид", "111001001"),
    ("scientific-constant-system", "науковий-константа-система", "111111101"),
    ("scientific-constant-source", "науковий-константа-джерело", "111110110"),
    ("scientific-constant->clauses", "науковий-константа-клаузи", "111100111"),
)
def restore_local_helper_layer(source: str) -> str:
    """Точний обернений прохід проєкцій; читача чи обчислювача не запускає."""
    # Архівний шар відтворюємо лише в перевірці походження, не в живій бібліотеці.
    if re.search(r"(?m)^\\(визначити\\s+[A-Za-z*]", source):
        raise AssertionError("у чинному Lisp залишено латинське визначення")
    body = source + SCHEMA_ARCHIVE_BLOCK
    # Local binders belong to the Ukrainian primary definitions; undo them
    # before the public-name inverse changes those definition heads to English.
    body = restore_quantity_formals(body)
    inverse = {ukrainian: english for english, ukrainian, _bits in PUBLIC_PROJECTIONS}
    body, restored_public = project_public_names(body, inverse)
    if set(restored_public) != set(inverse):
        raise AssertionError("не вдалося точно відновити всі первинні назви Quantity")
    for english, ukrainian, calls in LOCAL_HELPERS:
        if (body.count("(" + ukrainian) != calls
                or body.count("(визначити " + ukrainian) != 1):
            raise AssertionError("порушена локальна українська проєкція: " + ukrainian)
        body = body.replace("(" + ukrainian, "(" + english)
        body = body.replace("(визначити " + ukrainian, "(визначити " + english)
    if git_blob(body) != LOCAL_QUANTITY_BLOB:
        raise AssertionError("оригінальний Git blob локальної проєкції не відновлено")
    return body


def apply_local_helper_layer(source: str) -> str:
    """Прямий прохід від історичного тіла до чинних назв та сумісних імен."""
    body = source
    for english, ukrainian, calls in LOCAL_HELPERS:
        if (body.count("(" + english) != calls
                or body.count("(визначити " + english) != 1):
            raise AssertionError("порушено зворотну локальну проєкцію: " + english)
        body = body.replace("(" + english, "(" + ukrainian)
        body = body.replace("(визначити " + english, "(визначити " + ukrainian)
    forward = {english: ukrainian for english, ukrainian, _bits in PUBLIC_PROJECTIONS}
    body, projected_public = project_public_names(body, forward)
    if set(projected_public) != set(forward):
        raise AssertionError("не вдалося точно застосувати всі первинні назви Quantity")
    body = project_quantity_formals(body)
    if not body.endswith(SCHEMA_ARCHIVE_BLOCK):
        raise AssertionError("історичні дані схем не відтворилися точно")
    return body[:-len(SCHEMA_ARCHIVE_BLOCK)]



def project_heads(text: str, mapping: dict[str, str]) -> tuple[str, dict[str, int]]:
    """Only first source atom after (. Strings/comments and every other byte copy."""
    chunks: list[str] = []
    seen: dict[str, int] = {}
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch == ";":
            j = text.find("\n", i)
            if j < 0:
                j = n
            chunks.append(text[i:j])
            i = j
            continue
        if ch == '"':
            j = i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                elif text[j] == '"':
                    j += 1
                    break
                else:
                    j += 1
            chunks.append(text[i:j])
            i = j
            continue
        if ch == "(":
            chunks.append(ch)
            i += 1
            j = i
            while j < n and text[j].isspace():
                j += 1
            chunks.append(text[i:j])
            if j < n and not (text[j].isspace() or text[j] in '();"\''):
                k = j
                while k < n and not (text[k].isspace() or text[k] in '();'):
                    k += 1
                word = text[j:k]
                mapped = mapping.get(word)
                chunks.append(word if mapped is None else mapped)
                if mapped is not None:
                    seen[word] = seen.get(word, 0) + 1
                i = k
            else:
                i = j
            continue
        chunks.append(ch)
        i += 1
    return "".join(chunks), seen


def project_literals(text: str, mapping: dict[str, str]) -> tuple[str, dict[str, int]]:
    """Exact atom projection outside strings/comments; quoted (0)/(1) remain data."""
    chunks: list[str] = []
    seen: dict[str, int] = {}
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch == ";":
            j = text.find("\n", i)
            if j < 0:
                j = n
            chunks.append(text[i:j])
            i = j
            continue
        if ch == '"':
            j = i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                elif text[j] == '"':
                    j += 1
                    break
                else:
                    j += 1
            chunks.append(text[i:j])
            i = j
            continue
        if ch.isspace() or ch in "();":
            chunks.append(ch)
            i += 1
            continue
        j = i
        while j < n and not (text[j].isspace() or text[j] in '();"'):
            j += 1
        word = text[i:j]
        mapped = mapping.get(word)
        chunks.append(word if mapped is None else mapped)
        if mapped is not None:
            seen[word] = seen.get(word, 0) + 1
        i = j
    return "".join(chunks), seen


def project_public_names(text: str, mapping: dict[str, str]) -> tuple[str, dict[str, int]]:
    """Project callable heads plus DEFINE targets, copying comments and strings."""
    projected, seen = project_heads(text, mapping)
    chunks: list[str] = []
    for line in projected.splitlines(keepends=True):
        match = re.match(r"^(\s*\(визначити\s+)([^\s()]+)", line)
        if match is None:
            chunks.append(line)
            continue
        name = match.group(2)
        renamed = mapping.get(name)
        if renamed is None:
            chunks.append(line)
            continue
        chunks.append(line[:match.start(2)] + renamed + line[match.end(2):])
        seen[name] = seen.get(name, 0) + 1
    return "".join(chunks), seen



def git_blob(text: str) -> str:
    raw = text.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


class QuantityUkrProjection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_ratifed_exact_domain_keys(self):
        self.assertEqual(len(MAP), len(REVERSE), "ambiguous peer inversion")
        for domain, values in NATIVE.items():
            table = (ROOT / f"lib/domains/d{domain}.lisp").read_text(encoding="utf-8")
            for bits, ukr in values.items():
                with self.subTest(domain=domain, bits=bits):
                    self.assertRegex(table, re.compile(
                        r"^\s*\(" + bits + r"\s+\(ук\s+[^()]+\)\s+\(укр\s+"
                        + re.escape(ukr) + r"\)", re.MULTILINE))
        d1 = (ROOT / "lib/domains/d1.lisp").read_text(encoding="utf-8")
        self.assertIn("(0 (ук ні) (укр ні)", d1)
        self.assertIn("(1 (ук так) (укр так)", d1)

    def test_public_quantity_names_match_ratified_d9_keys(self):
        source = self.source
        d9 = (ROOT / "lib" / "domains" / "d9.lisp").read_text(encoding="utf-8")
        for english, ukrainian, bits in PUBLIC_PROJECTIONS:
            with self.subTest(english=english, bits=bits):
                self.assertEqual(len(bits), 9, f"D9 key has wrong width: {bits}")
                rows = [
                    line for line in d9.splitlines()
                    if line.lstrip().startswith(f"({bits} ")
                ]
                self.assertEqual(len(rows), 1, f"D9 must contain one exact row for {bits}")
                self.assertIn(f"(en {english})", rows[0])
                self.assertIn(f"(укр {ukrainian})", rows[0])
                self.assertRegex(
                    source,
                    rf"(?m)^\(визначити\s+{re.escape(ukrainian)}(?=\s|\))",
                )
                self.assertNotIn(f"(визначити {english} ", source)
                self.assertNotRegex(
                    source,
                    rf"(?m)^\s*\({bits}(?:\s|\))",
                    "укр source must not make a D9 coordinate directly callable",
                )


    def restore_previous(self):
        canonical_local = restore_local_helper_layer(self.source)
        expanded, false_count = project_literals(canonical_local, {"ні": FALSE_EXPR})
        previous, peer_counts = project_heads(expanded, D9_REVERSE)
        self.assertEqual(false_count, {"ні": 5})
        self.assertEqual(peer_counts, {"символ?": 3, "п'ятий": 2})
        self.assertEqual(git_blob(previous), PRE_REPAIR_BLOB)
        return previous

    def test_quantity_local_formals_are_ukrainian_and_reversible(self):
        expected = (
            ("науковий-список-правильний?", "(функція (значення)", "(функція (x)"),
            ("науковий-список-довжина-дорівнює?", "(функція (елементи залишок)", "(функція (items remaining)"),
            ("науковий-шостий", "(функція (поля)", "(функція (values)"),
            ("науковий-сьомий", "(функція (поля)", "(функція (values)"),
            ("створити-розмірність", "(функція (основа показник)", "(функція (base exponent)"),
            ("розмірність-основа", "(функція (розмірність)", "(функція (dimension)"),
            ("розмірність-показник", "(функція (розмірність)", "(функція (dimension)"),
            ("створити-одиниця", "(функція (розмірності)", "(функція (dimensions)"),
            ("одиниця-розмірності", "(функція (одиниця)", "(функція (unit)"),
            ("створити-величина", "(функція (значення одиниця)", "(функція (value unit)"),
            ("величина-значення", "(функція (величина)", "(функція (quantity)"),
            ("величина-одиниця", "(функція (величина)", "(функція (quantity)"),
            ("створити-наука-джерело", "(функція (авторитет видання)", "(функція (authority edition)"),
        )
        for name, ukrainian_formals, legacy_formals in expected:
            with self.subTest(function=name):
                anchor = f"(визначити {name}"
                start = self.source.index(anchor)
                next_definition = self.source.find("\n(визначити ", start + len(anchor))
                form = self.source[start:] if next_definition < 0 else self.source[start:next_definition]
                self.assertIn(ukrainian_formals, form)
                self.assertNotIn(legacy_formals, form)
        historical = restore_local_helper_layer(self.source)
        self.assertEqual(apply_local_helper_layer(historical), self.source)

    def test_remaining_local_formals_are_ukrainian(self):
        expected = (
            ("розмірність?", "(функція (значення)", "(функція (x)"),
            ("одиниця-виміру?", "(функція (значення)", "(функція (x)"),
            ("величина?", "(функція (значення)", "(функція (x)"),
            ("наука-джерело?", "(функція (значення)", "(функція (x)"),
            ("науковий-константа-стан-чинний?", "(функція (стан)", "(функція (status)"),
            ("науковий-константа-вид-чинний?", "(функція (вид)", "(функція (kind)"),
            ("створити-науковий-константа", "(функція (назва величина стан вид система джерело)",
             "(функція (name quantity status kind system source)"),
            ("науковий-константа?", "(функція (значення)", "(функція (x)"),
            ("науковий-константа-ім'я", "(функція (константа)", "(функція (constant)"),
            ("науковий-константа-величина", "(функція (константа)", "(функція (constant)"),
            ("науковий-константа-значення", "(функція (константа)", "(функція (constant)"),
            ("науковий-константа-одиниця", "(функція (константа)", "(функція (constant)"),
            ("науковий-константа-стан", "(функція (константа)", "(функція (constant)"),
            ("науковий-константа-вид", "(функція (константа)", "(функція (constant)"),
            ("науковий-константа-система", "(функція (константа)", "(функція (constant)"),
            ("науковий-константа-джерело", "(функція (константа)", "(функція (constant)"),
            ("науковий-константа-клаузи", "(функція (константа)", "(функція (constant)"),
            ("авторитет-наукового-джерела", "(функція (джерело)", "(функція (source)"),
            ("видання-наукового-джерела", "(функція (джерело)", "(функція (source)"),
        )
        for name, ukrainian, legacy in expected:
            with self.subTest(function=name):
                self.assertIn(f"(визначити {name}", self.source)
                self.assertIn(ukrainian, self.source)
                self.assertNotIn(legacy, self.source)
        self.assertIn("(функція (назва)", self.source)
        self.assertNotIn("(функція (name)", self.source)
        self.assertEqual(apply_local_helper_layer(restore_local_helper_layer(self.source)), self.source)

    def test_exact_original_git_blob_recoverable(self):
        previous = self.restore_previous()
        old_d1, seen_d1 = project_literals(previous, D1_REVERSE)
        old, seen = project_heads(old_d1, REVERSE)
        self.assertEqual(seen, {MAP[bits]: n for bits, n in HEAD_COUNTS.items()})
        self.assertEqual(seen_d1, {"так": 19})
        self.assertEqual(git_blob(old), BASE_BLOB)

    def test_no_remaining_claimed_numeric_heads_or_d1_literals(self):
        same, left = project_heads(self.source, MAP)
        self.assertEqual(left, {})
        self.assertEqual(same, self.source)
        same, left = project_literals(self.source, D1)
        self.assertEqual(left, {})
        self.assertEqual(same, self.source)
        same, left = project_heads(self.source, D9)
        self.assertEqual(left, {})
        self.assertEqual(same, self.source)

    def test_two_way_projection_idempotence(self):
        previous = self.restore_previous()
        raw, _ = project_heads(project_literals(previous, D1_REVERSE)[0], REVERSE)
        again, _ = project_heads(raw, MAP)
        again, _ = project_literals(again, D1)
        again, _ = project_heads(again, D9)
        self.assertEqual(again.count(FALSE_EXPR), 5)
        again = again.replace(FALSE_EXPR, "ні")
        self.assertEqual(again, restore_local_helper_layer(self.source))
        self.assertEqual(apply_local_helper_layer(again), self.source)

    def test_comments_strings_and_quoted_data_unchanged(self):
        synthetic = '; #d1:1 (0011 ignored)\n"(010 not-code) #d1:1"\n(0011 x (001 (0)))\n'
        migrated, counts = project_heads(synthetic, MAP)
        migrated, d1counts = project_literals(migrated, D1)
        self.assertEqual(counts, {"0011": 1, "001": 1})
        self.assertEqual(d1counts, {})
        self.assertIn('; #d1:1 (0011 ignored)', migrated)
        self.assertIn('"(010 not-code) #d1:1"', migrated)
        self.assertIn("(визначити x (як-є (0)))", migrated)

    def test_data_tags_d9_and_exact_d1_false(self):
        self.assertIn("(як-є dimension/1)", self.source)
        self.assertIn("(як-є scientific-constant)", self.source)
        self.assertNotIn("(як-є (0))", self.source)
        self.assertNotIn("(як-є (1))", self.source)
        self.assertNotIn("(110101100", self.source)
        self.assertNotIn("(110110101", self.source)
        self.assertIn("(символ?", self.source)
        self.assertIn("(п'ятий", self.source)
        self.assertIn("(так", self.source)
        self.assertEqual(project_literals(self.source, {"ні": FALSE_EXPR})[1], {"ні": 5})

    def test_d9_peer_names_have_exact_domain_and_core4_authority(self):
        table = (ROOT / "lib/domains/d9.lisp").read_text(encoding="utf-8")
        core = (ROOT / "lib/core4.lisp").read_text(encoding="utf-8")
        for bits, ukr in D9.items():
            with self.subTest(bits=bits):
                self.assertRegex(table, re.compile(
                    r"^\s*\(" + bits + r"\s+\(ук\s+" + re.escape(ukr)
                    + r"\)\s+\(укр\s+" + re.escape(ukr) + r"\)", re.MULTILINE))
                self.assertRegex(core, re.compile(
                    r"^\(визначити\s+" + re.escape(ukr) + r"[\s()]", re.MULTILINE))

    def test_definition_names_remain_historical(self):
        old, _ = project_heads(project_literals(self.restore_previous(), D1_REVERSE)[0], REVERSE)
        definitions_old = re.findall(r"\(0011\s+([^\s()]+)", old)
        historical = restore_local_helper_layer(self.source)
        definitions_new = re.findall(r"\(визначити\s+([^\s()]+)", historical)
        self.assertEqual(definitions_old, definitions_new)
        self.assertEqual(len(definitions_new), 37)

    def test_wrong_local_helper_mutant_fails_strict_inverse(self):
        bad = self.source.replace(
            "(науковий-шостий x)", "(науковий-сьомий x)", 1
        )
        self.assertNotEqual(bad, self.source)
        with self.assertRaisesRegex(AssertionError, "порушена локальна"):
            restore_local_helper_layer(bad)

    def test_lisp_delimiters_balanced_without_python_semantics(self):
        code = re.sub(r';[^\n]*|"(?:\\.|[^"\\])*"', "", self.source)
        depth = 0
        for char in code:
            depth += (char == "(") - (char == ")")
            self.assertGreaterEqual(depth, 0)
        self.assertEqual(depth, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
