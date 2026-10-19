"""Exact-identity source migration of immutable persistent MAP into full укр.

Only D4 DEFINE, D3 QUOTE and exact D1:YES change their textual projection.
No host hashmap, new domain code, automatic aliasing or Python evaluation.
"""
from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/persistent-map.lisp"
PRE_MIGRATION_BLOB = "149d768862b8719d789297e53e80fad90c9fbfe7"
POST_D3D4_BLOB = "b6b84716702e7546cb2c0f031524210cb7d7b956"

# Після вже перевіреної D1/D3/D4 проєкції ці три викличні голови
# перейшли на наявні Lisp-owned українські alias bindings. Не виводимо
# викличність D9:MAP-INSERT з одного ратифікованого рядка таблиці.
MAP_FORMALS = (
    ("мапа-вставити", (("key", "ключ", 5), ("value", "значення", 4), ("entries", "записи", 6))),
    ("мапа-отримати", (("key", "ключ", 3), ("entries", "записи", 5))),
    ("мапа-містить?", (("key", "ключ", 2), ("entries", "записи", 2))),
    ("мапа-список", (("entries", "записи", 2),)),
)


RECENT_CALLS = (
    ("(map-insert key value (решта entries))",
     "(внутрішня-мапа-вставити key value (решта entries))"),
    ("(map-get key (решта entries))",
     "(мапа-отримати key (решта entries))"),
    ("(map-get key entries)",
     "(мапа-отримати key entries)"),
)


def _rewrite_map_formals(source: str, function_name: str, edits) -> str:
    """Rename exact local atoms in one map definition; strings/comments are data."""
    anchors = list(re.finditer(
        r"(?m)^\\(визначити\\s+" + re.escape(function_name) + r"(?=\\s|\\))",
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
                raise AssertionError(f"{function_name}: незбалансована форма")
    if end is None:
        raise AssertionError(f"{function_name}: незакрита форма")
    form = source[start:end]
    mappings = {old: (new, expected) for old, new, expected in edits}
    counts = {old: 0 for old in mappings}
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
        while stop < len(form) and not form[stop].isspace() and form[stop] not in "();'\\\"":
            stop += 1
        atom = form[index:stop]
        if atom in mappings:
            renamed, _expected = mappings[atom]
            chunks.append(renamed)
            counts[atom] += 1
        else:
            chunks.append(atom)
        index = stop
    for old, (_new, expected) in mappings.items():
        if counts[old] != expected:
            raise AssertionError(
                f"{function_name}: кількість атомів {old}: очікувалося {expected}, знайдено {counts[old]}"
            )
    return source[:start] + "".join(chunks) + source[end:]


def apply_map_formals(source: str) -> str:
    for name, edits in MAP_FORMALS:
        source = _rewrite_map_formals(source, name, edits)
    return source


def undo_map_formals(source: str) -> str:
    for name, edits in reversed(MAP_FORMALS):
        inverse = tuple((ukrainian, english, count) for english, ukrainian, count in edits)
        source = _rewrite_map_formals(source, name, inverse)
    return source


def undo_primary_projection(source: str) -> str:
    """Invert the exact D9 primary-surface commit without touching laws/data."""
    previous = source
    pairs = (
        ("(визначити мапа-порожній (як-є ()))",
         "(визначити map-empty (як-є ()))"),
        ("(визначити мапа-вставити\n", "(визначити map-insert\n"),
        ("(визначити мапа-отримати\n", "(визначити map-get\n"),
        ("(визначити мапа-містить?\n", "(визначити map-contains?\n"),
        ("(визначити мапа-список\n", "(визначити map->list\n"),
        ("(визначити внутрішня-мапа-вставити мапа-вставити)",
         "(визначити внутрішня-мапа-вставити map-insert)"),
        ("(визначити внутрішня-мапа-отримати мапа-отримати)",
         "(визначити внутрішня-мапа-отримати map-get)"),
        ("(визначити внутрішня-мапа-містить мапа-містить?)",
         "(визначити внутрішня-мапа-містить map-contains?)"),
        ("(визначити внутрішня-мапа-список мапа-список)",
         "(визначити внутрішня-мапа-список map->list)"),
    )
    for current, historic in pairs:
        if previous.count(current) != 1:
            raise AssertionError("MAP: primary-укр inverse input missing/ambiguous: " + current)
        previous = previous.replace(current, historic, 1)
    current_tail = """; Full укр names are the primary Lisp-owned closures for their ratified residents.
; Exact identities: MAP-EMPTY D9:101100011; MAP-INSERT D9:101101110;
; MAP-GET D9:101100101; MAP-CONTAINS? D9:101100010; MAP->LIST D9:101001100.
; The width belongs to the domain row; this library never executes raw bit strings.
(визначити внутрішня-мапа-порожній мапа-порожній)

; Історичні англійські входи — сумісні псевдоніми тих самих укр-замикань.
(визначити map-empty мапа-порожній)
(визначити map-insert мапа-вставити)
(визначити map-get мапа-отримати)
(визначити map-contains? мапа-містить?)
(визначити map->list мапа-список)
"""
    historic_tail = """; D9 resident projections over the existing immutable map mechanism.
; Exact identities: MAP-EMPTY D9:101100011; MAP-GET D9:101100101;
; MAP-CONTAINS? D9:101100010; MAP->LIST D9:101001100.
; These wrappers preserve the map's maybe-shaped lookup result and dotted-entry order.
(визначити внутрішня-мапа-порожній map-empty)
(визначити мапа-порожній внутрішня-мапа-порожній)
(визначити мапа-отримати внутрішня-мапа-отримати)
(визначити мапа-містить? внутрішня-мапа-містить)
(визначити мапа-список внутрішня-мапа-список)
"""
    if not previous.endswith(current_tail):
        raise AssertionError("MAP: primary-укр inverse tail missing/ambiguous")
    return previous[:-len(current_tail)] + historic_tail


def apply_primary_projection(source: str) -> str:
    """Reapply the exact D9 primary-surface migration."""
    current = source
    pairs = (
        ("(визначити map-empty (як-є ()))",
         "(визначити мапа-порожній (як-є ()))"),
        ("(визначити map-insert\n", "(визначити мапа-вставити\n"),
        ("(визначити map-get\n", "(визначити мапа-отримати\n"),
        ("(визначити map-contains?\n", "(визначити мапа-містить?\n"),
        ("(визначити map->list\n", "(визначити мапа-список\n"),
        ("(визначити внутрішня-мапа-вставити map-insert)",
         "(визначити внутрішня-мапа-вставити мапа-вставити)"),
        ("(визначити внутрішня-мапа-отримати map-get)",
         "(визначити внутрішня-мапа-отримати мапа-отримати)"),
        ("(визначити внутрішня-мапа-містить map-contains?)",
         "(визначити внутрішня-мапа-містить мапа-містить?)"),
        ("(визначити внутрішня-мапа-список map->list)",
         "(визначити внутрішня-мапа-список мапа-список)"),
    )
    for historic, projected in pairs:
        if current.count(historic) != 1:
            raise AssertionError("MAP: primary-укр projection input missing/ambiguous: " + historic)
        current = current.replace(historic, projected, 1)
    historic_tail = """; D9 resident projections over the existing immutable map mechanism.
; Exact identities: MAP-EMPTY D9:101100011; MAP-GET D9:101100101;
; MAP-CONTAINS? D9:101100010; MAP->LIST D9:101001100.
; These wrappers preserve the map's maybe-shaped lookup result and dotted-entry order.
(визначити внутрішня-мапа-порожній map-empty)
(визначити мапа-порожній внутрішня-мапа-порожній)
(визначити мапа-отримати внутрішня-мапа-отримати)
(визначити мапа-містить? внутрішня-мапа-містить)
(визначити мапа-список внутрішня-мапа-список)
"""
    current_tail = """; Full укр names are the primary Lisp-owned closures for their ratified residents.
; Exact identities: MAP-EMPTY D9:101100011; MAP-INSERT D9:101101110;
; MAP-GET D9:101100101; MAP-CONTAINS? D9:101100010; MAP->LIST D9:101001100.
; The width belongs to the domain row; this library never executes raw bit strings.
(визначити внутрішня-мапа-порожній мапа-порожній)

; Історичні англійські входи — сумісні псевдоніми тих самих укр-замикань.
(визначити map-empty мапа-порожній)
(визначити map-insert мапа-вставити)
(визначити map-get мапа-отримати)
(визначити map-contains? мапа-містить?)
(визначити map->list мапа-список)
"""
    if not current.endswith(historic_tail):
        raise AssertionError("MAP: historic primary-surface tail missing/ambiguous")
    return current[:-len(historic_tail)] + current_tail


def undo_recent_calls(source: str) -> str:
    previous = source
    for old, projected in RECENT_CALLS:
        if previous.count(projected) != 1:
            raise AssertionError("MAP: неоднозначний або відсутній поточний український виклик")
        previous = previous.replace(projected, old, 1)
    if git_blob(previous) != POST_D3D4_BLOB:
        raise AssertionError("MAP: нова проєкція змінила байти поза трьома викликами")
    return previous


def apply_recent_calls(source: str) -> str:
    current = source
    for old, projected in RECENT_CALLS:
        if current.count(old) != 1:
            raise AssertionError("MAP: неможливо точно відтворити три проєкції викликів")
        current = current.replace(old, projected, 1)
    return current



CURRENT_DEFS = (
    "мапа-порожній", "мапа-вставити", "мапа-отримати", "мапа-містить?", "мапа-список",
    "внутрішня-мапа-вставити", "внутрішня-мапа-отримати",
    "внутрішня-мапа-містить", "внутрішня-мапа-список",
    "внутрішня-мапа-порожній", "map-empty", "map-insert", "map-get",
    "map-contains?", "map->list",
)
PEERS = {1: ("1", "так"), 3: ("001", "як-є"), 4: ("0011", "визначити")}


def restore_exact_previous(source: str) -> str:
    source = undo_map_formals(source)
    source = undo_primary_projection(source)
    source = undo_recent_calls(source)
    restored = []
    for line in source.splitlines(keepends=True):
        if line.lstrip().startswith(";"):
            restored.append(line)
            continue
        line = re.sub(r"\(визначити(?=\s)", "(0011", line)
        line = re.sub(r"\(так(?=\s|$)", "(#d1:1", line)
        # D3 QUOTE was present in the body of the unique map-empty declaration.
        line = line.replace("(0011 map-empty (як-є ()))",
                            "(0011 map-empty (001 ()))")
        restored.append(line)
    return "".join(restored)


def git_blob(source: str) -> str:
    encoded = source.encode("utf-8")
    return hashlib.sha1(
        b"blob " + str(len(encoded)).encode() + b"\0" + encoded
    ).hexdigest()


def verify(source: str) -> None:
    if git_blob(restore_exact_previous(source)) != PRE_MIGRATION_BLOB:
        raise AssertionError("MAP: змінено байти поза D1/D3/D4 peer проєкціями")
    heads = re.findall(r"(?m)^\(визначити\s+([^\s()]+)", source)
    if tuple(heads) != CURRENT_DEFS:
        raise AssertionError("MAP: визначення/порядок/імена порушено")
    if source.count("(так") != 2:
        raise AssertionError("MAP: мають бути два явні D1:YES fallback")
    if "(визначити мапа-порожній (як-є ()))" not in source:
        raise AssertionError("MAP: D3:001 QUOTE не на повній укр-проєкції")


class PersistentMapUkrTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_domain_contract_exact_and_not_sid8(self):
        for width, (bits, expected) in PEERS.items():
            src = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
            row = next((line for line in src.splitlines()
                        if line.lstrip().startswith(f"({bits} ")), None)
            self.assertIsNotNone(row)
            self.assertIn(f"(укр {expected})", row)
        self.assertEqual(len(set(PEERS)), 3)

    def test_original_blob_fully_recovered_no_semantic_substitution(self):
        verify(self.source)

    def test_all_fifteen_defs_and_d1_quote_are_ukr(self):
        self.assertEqual(self.source.count("(визначити "), 15)
        self.assertIn("(визначити мапа-порожній (як-є ()))", self.source)
        code = "\n".join(s for s in self.source.splitlines()
                         if not s.lstrip().startswith(";"))
        self.assertNotRegex(code, r"\([01]{3,9}(?=\s|\))")
        self.assertNotIn("#d1:1", code)
        self.assertEqual(code.count("(так"), 2)

    def test_immutable_map_mechanism_and_aliases_unchanged(self):
        for form in (
            "(внутрішня-мапа-вставити ключ значення (решта записи))",
            "(мапа-отримати ключ (решта записи))",
            "(мапа-отримати ключ записи)",
            "(визначити внутрішня-мапа-вставити мапа-вставити)",
            "(визначити внутрішня-мапа-отримати мапа-отримати)",
            "(визначити внутрішня-мапа-містить мапа-містить?)",
            "(визначити внутрішня-мапа-список мапа-список)",
            "(визначити внутрішня-мапа-порожній мапа-порожній)",
            "(визначити map-empty мапа-порожній)",
            "(визначити map-insert мапа-вставити)",
            "(визначити map-get мапа-отримати)",
            "(визначити map-contains? мапа-містить?)",
            "(визначити map->list мапа-список)",
        ):
            self.assertIn(form, self.source)
        verify(self.source)

    def test_map_formals_are_ukrainian_and_exactly_reversible(self):
        expected = (
            ("мапа-вставити", "(функція (ключ значення записи)", "(функція (key value entries)"),
            ("мапа-отримати", "(функція (ключ записи)", "(функція (key entries)"),
            ("мапа-містить?", "(функція (ключ записи)", "(функція (key entries)"),
            ("мапа-список", "(функція (записи)", "(функція (entries)"),
        )
        for name, ukrainian, legacy in expected:
            with self.subTest(function=name):
                self.assertIn(f"(визначити {name}", self.source)
                self.assertIn(ukrainian, self.source)
                self.assertNotIn(legacy, self.source)
        self.assertEqual(apply_map_formals(undo_map_formals(self.source)), self.source)

    def test_fail_closed_for_wrong_op_bit_or_data(self):
        for mutation in (
            self.source.replace("(визначити мапа-порожній", "(функція мапа-порожній", 1),
            self.source.replace("(як-є ())", "(атом? ())", 1),
            self.source.replace("(так", "(ні", 1),
            self.source.replace("(сполучити ключ значення)", "(сполучити значення ключ)", 1),
            self.source.replace("(визначити внутрішня-мапа-отримати мапа-отримати)",
                                "(визначити внутрішня-мапа-отримати мапа-містить?)", 1),
            self.source.replace("(мапа-отримати ключ записи)",
                                "(мапа-містить? ключ записи)", 1),
            self.source.replace("(внутрішня-мапа-вставити ключ значення",
                                "(мапа-вставити ключ значення", 1),
        ):
            with self.assertRaises(AssertionError):
                verify(mutation)

    def test_reversible_exact_projection_idempotence(self):
        previous = restore_exact_previous(self.source)
        again = previous.replace("(0011 map-empty (001 ()))",
                                 "(визначити map-empty (як-є ()))")
        again = re.sub(r"\(0011(?=\s)", "(визначити", again)
        again = re.sub(r"\(#d1:1(?=\s|$)", "(так", again, flags=re.M)
        again = apply_recent_calls(again)
        again = apply_primary_projection(again)
        again = apply_map_formals(again)
        self.assertEqual(again, self.source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
