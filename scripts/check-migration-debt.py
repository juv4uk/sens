#!/usr/bin/env python3
"""Свідок боргу міграції — точковий інформативний тест.

Ідея (ми цінуємо кожен біт):

  Доменний оператор (D3..D6) має бути записаний СВОЇМ бінарним кодом. Якщо
  він лишається плейн-назвою в ПОЗИЦІЇ ГОЛОВИ (а не як дані всередині quote),
  і при цьому ніде в репо не визначений користувачем — це борг міграції.

Це відрізняє справжній борг від:
  - даних усередині (quote ...)/(001 ...) — там назви не є головами;
  - користувацьких функцій, що ЗБІГАЮТЬСЯ з іменем оператора
    (напр. lib/core.lisp сам визначає `quotient`/`reduce`/`*-onto`).

Використовує всі 2046 функцій D1..D10 як авторитетну таблицю операторів
(беруться лише call-домени D3..D6) + документований аліас def->define.

Вивід — таблиця боргу (файл | голова | кількість | домен | код). За
замовчуванням це ЗВІТ (вихід 0), бо невиразний literal-список із назвою
оператора може дати хибний позитив; прапорець --fail робить перевірку
fail-closed (ненульовий вихід на борг). Read-only.
Запуск: python3 scripts/check-migration-debt.py [--fail] [корінь ...]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from domain_tables import read_domain_table, CURRENT_HUMAN_TABLES  # noqa: E402

DEFAULT_SCOPES = ("lib", "scripts")
SKIP_PARTS = ("lib/domains", "lib/generated", "lib/surface")
CALL_DOMAIN_MIN = 3  # D1 (істина) і D2 (структура) — значення/каркас, не голови виклику
CALL_DOMAIN_MAX = 6


def norm(name: str) -> str:
    return name.rstrip("?!").casefold()


def load_operator_authority() -> dict[str, tuple[str, str]]:
    """Плейн-ім'я оператора -> (домен, точний код), лише call-домени D3..D6."""
    authority: dict[str, tuple[str, str]] = {}
    for table in CURRENT_HUMAN_TABLES:
        width = int(table.stem[1:])
        if width < CALL_DOMAIN_MIN or width > CALL_DOMAIN_MAX:
            continue
        for row in read_domain_table(table):
            for name in (row.en, row.lisp):
                if name:
                    authority.setdefault(norm(name), (row.domain, row.bits))
    authority["def"] = ("D4", "0011")  # документований аліас define
    return authority


def tokenize(text: str) -> list[str]:
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == ";":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c.isspace():
            i += 1
            continue
        if c in "()":
            out.append(c)
            i += 1
            continue
        if c == '"':
            j = i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                    continue
                if text[j] == '"':
                    break
                j += 1
            out.append(text[i:j + 1])
            i = j + 1
            continue
        j = i
        while j < n and not text[j].isspace() and text[j] not in '()"':
            j += 1
        out.append(text[i:j])
        i = j
    return out


def parse_all(tokens: list[str]) -> list:
    pos = [0]

    def read():
        token = tokens[pos[0]]
        pos[0] += 1
        if token == "(":
            node = []
            while pos[0] < len(tokens) and tokens[pos[0]] != ")":
                node.append(read())
            pos[0] += 1
            return node
        return token

    forms = []
    while pos[0] < len(tokens):
        forms.append(read())
    return forms


def collect_heads(node, code: bool, debt: dict[str, int], authority: dict) -> None:
    if not isinstance(node, list) or not node:
        return
    head = node[0]
    if code and isinstance(head, str) and not re.fullmatch(r"[01]+", head):
        if norm(head) in authority:
            debt[head] = debt.get(head, 0) + 1
    quoted = isinstance(head, str) and (norm(head) == "quote" or head == "001")
    lambda_form = isinstance(head, str) and (norm(head) == "lambda" or head == "0010")
    for idx, child in enumerate(node):
        if quoted and idx == 1:
            collect_heads(child, False, debt, authority)   # payload цитати = дані
        elif lambda_form and idx == 1:
            collect_heads(child, False, debt, authority)   # параметри лямбди — не голови
        else:
            collect_heads(child, code, debt, authority)


def user_defined_names(paths: list[Path]) -> set[str]:
    names: set[str] = set()
    pattern = re.compile(r"^\((?:0011|def)\s+([^\s()]+)", re.MULTILINE)
    for path in paths:
        for match in pattern.finditer(path.read_text(encoding="utf-8")):
            names.add(norm(match.group(1)))
    return names


def in_scope(path: Path, scopes: tuple[str, ...]) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    if path.suffix != ".lisp":
        return False
    if any(rel.startswith(skip + "/") or rel == skip for skip in SKIP_PARTS):
        return False
    return any(rel.startswith(s + "/") or rel == s for s in scopes)


def main(argv: list[str]) -> int:
    args = argv[1:]
    fail_closed = "--fail" in args
    scopes = tuple(a for a in args if a != "--fail") or DEFAULT_SCOPES
    authority = load_operator_authority()
    paths = sorted(p for p in ROOT.rglob("*.lisp") if in_scope(p, scopes))
    userdef = user_defined_names(paths)

    rows: list[tuple[str, str, int, str, str]] = []
    total = 0
    for path in paths:
        debt: dict[str, int] = {}
        try:
            collect_heads(parse_all(tokenize(path.read_text(encoding="utf-8"))), True, debt, authority)
        except IndexError:
            continue
        for head, count in debt.items():
            if norm(head) in userdef:
                continue  # користувацька функція з тим самим іменем — не борг
            domain, bits = authority[norm(head)]
            rows.append((path.relative_to(ROOT).as_posix(), head, count, domain, bits))
            total += count

    print("свідок боргу міграції (плейн-оператор у позиції голови)")
    print(f"область: {', '.join(scopes)}  (файлів: {len(paths)}, користувацьких імен: {len(userdef)})")
    print(f"авторитет операторів: D3..D6 + def, позицій: {len(authority)}")
    print()
    if not rows:
        print("MIGRATION-DEBT: PASS — жодного допущеного оператора не лишилось плейн у коді")
        return 0
    header = f"{'файл':<52}{'голова':<16}{'к-сть':<7}{'домен':<7}{'код':<8}"
    print(header)
    print("-" * len(header))
    for rel, head, count, domain, bits in sorted(rows, key=lambda r: (-r[2], r[0])):
        print(f"{rel:<52}{head:<16}{count:<7}{domain:<7}{bits:<8}")
    print("-" * len(header))
    print(f"борг: {total} голови у {len({r[0] for r in rows})} файлі(ах)")
    if fail_closed:
        print("MIGRATION-DEBT: FAIL — оператори лишились плейн у коді (див. таблицю)")
        return 1
    print("MIGRATION-DEBT: ЗВІТ — борг показано вище (додайте --fail для ненульового виходу)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
