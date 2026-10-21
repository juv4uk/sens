"""Чинна українська проєкція TCP/островів: закони джерела, не старий SID8 знімок.

Це статична перевірка Lisp AST. Реальне SENS виконання захисту D6
перевіряє crates/sens/tests/island_lowering_ukr_runtime.rs.
Цей тест НЕ видає допуску T5M, oracle або релізу.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOKEN = re.compile(r';[^\n]*|"(?:\\.|[^"\\])*"|[()]|[^\s();]+')
PEERS = {
    "функція": (4, "0010"),
    "як-є": (3, "001"),
    "атом?": (3, "010"),
    "решта": (3, "011"),
    "перше": (3, "100"),
    "тотожне?": (3, "101"),
    "за-умовою": (3, "110"),
    "сполучити": (3, "111"),
    "друге": (4, "1001"),
    "список": (4, "1110"),
    "рядок-додати": (9, "110011110"),
    "четверте": (6, "100111"),
}


def parse(source: str) -> list:
    words = [match.group() for match in TOKEN.finditer(source)
             if not match.group().startswith(";")]
    offset = 0

    def read():
        nonlocal offset
        if offset >= len(words):
            raise ValueError("незавершена Lisp-форма")
        word = words[offset]
        offset += 1
        if word == ")":
            raise ValueError("зайва закривальна дужка")
        if word != "(":
            return word
        children = []
        while offset < len(words) and words[offset] != ")":
            children.append(read())
        if offset >= len(words):
            raise ValueError("немає закривальної дужки")
        offset += 1
        return children

    result = []
    while offset < len(words):
        result.append(read())
    return result


def heads(node) -> list[str]:
    if not isinstance(node, list) or not node:
        return []
    head = node[0]
    called = [head] if isinstance(head, str) else heads(head)
    if head == "як-є":
        return called  # цитоване значення не містить викличних голів
    for child in node[1:]:
        called.extend(heads(child))
    return called


def definitions(forms: list) -> dict[str, list]:
    rows: dict[str, list] = {}
    for form in forms:
        if isinstance(form, list) and len(form) == 3 and form[0] == "визначити":
            name = form[1]
            if not isinstance(name, str) or name in rows:
                raise AssertionError("повторна або неатомарна Lisp-назва")
            rows[name] = form
    return rows


def validate_current(path: str, source: str) -> dict[str, list]:
    forms = parse(source)
    defs = definitions(forms)
    called = [head for form in forms for head in heads(form)]
    old_encoded = [head for head in called
                   if re.fullmatch(r"[01]{3,11}", head)]
    if old_encoded:
        raise AssertionError(f"{path}: машинні викличні голови замість укр: {old_encoded}")
    if "#d1:" in source or "#d8:" in source or "#b" in source:
        raise AssertionError(f"{path}: старі кодовані літерали")
    if not defs:
        raise AssertionError(f"{path}: немає виконуваних визначень")
    return defs


def validate_island_guard(source: str) -> None:
    defs = validate_current("lib/island-lowering.lisp", source)
    if "острів-є-четверте-поле?" not in defs or "острів-обробити-вибір" not in defs:
        raise AssertionError("не визначено захисну функцію та обробник")
    if "(острів-є-четверте-поле? вибір)" not in source:
        raise AssertionError("немає перевірки перед четвертим полем")
    if "(четверте вибір)" not in source:
        raise AssertionError("змінено ратифікований D6-селектор")
    if source.count("(як-є malformed-selection)") < 2:
        raise AssertionError("обрізана форма мусить дати іменовану відмову")
    shape = defs["острів-є-четверте-поле?"]
    checks = heads(shape)
    if checks.count("атом?") < 4 or "решта" not in checks:
        raise AssertionError("кожен крок D3 CDR має перевірятися до D6")
    if "(вибрати-механізм ідентичність виконавець)" not in source:
        raise AssertionError("обхід добору механізму неприпустимий")


class UkrainianTcpIslandCurrentTests(unittest.TestCase):
    def test_current_ratified_ukrainian_head_coordinates(self):
        for spelling, (width, bits) in PEERS.items():
            with self.subTest(surface=spelling):
                source = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
                row = next((line for line in source.splitlines()
                            if line.startswith(f"  ({bits} ")), None)
                self.assertIsNotNone(row, (spelling, bits))
                self.assertIn(f"(укр {spelling})", row)

    def test_current_tcp_and_island_lisp_without_obsolete_blob_requirements(self):
        tcp = (ROOT / "lib/tcp.lisp").read_text(encoding="utf-8")
        island = (ROOT / "lib/island-lowering.lisp").read_text(encoding="utf-8")
        self.assertIn('"0.0.0.0"', tcp)
        self.assertIn("(визначити протокол-передавання-читати", tcp)
        self.assertIn("(визначити протокол-передавання-записати", tcp)
        validate_current("lib/tcp.lisp", tcp)
        validate_island_guard(island)

    def test_negative_mutations_reject_unguarded_d6_and_obsolete_literals(self):
        island = (ROOT / "lib/island-lowering.lisp").read_text(encoding="utf-8")
        for mutant in (
            island.replace("(острів-є-четверте-поле? вибір)", "так", 1),
            island.replace("(четверте вибір)", "(третє вибір)", 1),
            island.replace("(як-є malformed-selection)", "(як-є success)", 2),
            island.replace("(решта запис)", "(00001101 запис)", 1),
        ):
            with self.subTest(change=mutant != island):
                self.assertNotEqual(mutant, island)
                with self.assertRaises(AssertionError):
                    validate_island_guard(mutant)
        tcp = (ROOT / "lib/tcp.lisp").read_text(encoding="utf-8")
        with self.assertRaises(AssertionError):
            validate_current("lib/tcp.lisp", tcp + "\n(визначити проба #d1:1)\n")

    def test_malformed_lisp_is_not_counted_as_reversible(self):
        for source in ("(", ")", "(за-умовою (тотожне?", "(визначити x) )"):
            with self.assertRaises(ValueError):
                parse(source)


if __name__ == "__main__":
    unittest.main()
