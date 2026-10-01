#!/usr/bin/env python3
"""#1962 research-only: discover pure CAR/CDR selector identities and quotient by path.

This is not production semantic authority. It reads current Lisp source plus the
generated legacy function table, discovers one-argument definitions made only
from exact CAR/CDR composition, resolves direct aliases, and groups old fixed-8
identities by the resulting variable-width selector path.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "lib/core.lisp"
TABLE = ROOT / "lib/generated/function-table.lisp"
LEGACY_AUDIT = ROOT / "contracts/primitive-budget-audit-734.lisp"

DEFINE = "00001001"
LAMBDA = "00001000"
CAR = "00000101"
CDR = "00000110"


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c.isspace():
            i += 1
            continue
        if c == ";":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c in "()":
            tokens.append(c)
            i += 1
            continue
        if c == '"':
            start = i
            i += 1
            escaped = False
            while i < n:
                ch = text[i]
                i += 1
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    break
            else:
                raise ValueError(f"unterminated string at byte {start}")
            tokens.append(text[start:i])
            continue

        start = i
        while i < n and not text[i].isspace() and text[i] not in "();":
            i += 1
        tokens.append(text[start:i])
    return tokens


def parse_many(tokens: list[str]) -> list[object]:
    pos = 0

    def one() -> object:
        nonlocal pos
        if pos >= len(tokens):
            raise ValueError("unexpected end")
        token = tokens[pos]
        pos += 1
        if token == "(":
            out = []
            while True:
                if pos >= len(tokens):
                    raise ValueError("unclosed list")
                if tokens[pos] == ")":
                    pos += 1
                    return out
                out.append(one())
        if token == ")":
            raise ValueError("unexpected close")
        return token

    forms = []
    while pos < len(tokens):
        forms.append(one())
    return forms


def selector_ops(expr: object, parameter: str) -> tuple[str, ...] | None:
    if expr == parameter:
        return ()
    if not isinstance(expr, list) or len(expr) != 2:
        return None
    head, argument = expr
    if head not in (CAR, CDR):
        return None
    tail = selector_ops(argument, parameter)
    if tail is None:
        return None
    return (head,) + tail


def selector_path(ops: tuple[str, ...]) -> str | None:
    if not ops:
        return None
    root = "101" if ops[0] == CAR else "110"
    suffix = "".join("0" if op == CAR else "1" for op in ops[1:])
    return root + suffix


def discover_core() -> tuple[dict[str, str], dict[str, str]]:
    forms = parse_many(tokenize(CORE.read_text(encoding="utf-8")))
    direct: dict[str, str] = {}
    aliases: dict[str, str] = {}

    for form in forms:
        if not isinstance(form, list) or len(form) < 3 or form[0] != DEFINE:
            continue
        name = form[1]
        value = form[2]
        if not isinstance(name, str):
            continue

        if isinstance(value, str):
            aliases[name] = value
            continue

        if (
            isinstance(value, list)
            and len(value) >= 3
            and value[0] == LAMBDA
            and isinstance(value[1], list)
            and len(value[1]) == 1
            and isinstance(value[1][0], str)
        ):
            parameter = value[1][0]
            ops = selector_ops(value[2], parameter)
            if ops:
                path = selector_path(ops)
                if path:
                    direct[name] = path

    changed = True
    while changed:
        changed = False
        for name, target in aliases.items():
            if name not in direct and target in direct:
                direct[name] = direct[target]
                changed = True

    return direct, aliases


def legacy_identities() -> dict[str, str]:
    out: dict[str, str] = {}
    pattern = re.compile(
        r"^\s*\(([01]{8})\s+identity:[01]{8}/surface:([^\s()]+)"
    )
    for line in TABLE.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            code, name = match.groups()
            out[name] = code
    return out


def main() -> None:
    paths, aliases = discover_core()
    old = legacy_identities()

    rows = []
    for name, path in sorted(paths.items(), key=lambda item: (len(item[1]), item[1], item[0])):
        if name in old:
            rows.append((name, old[name], path, aliases.get(name, "-")))

    expected = {"second", "third", "fourth", "fifth", "caar", "cadr", "cddr", "cadddr"}
    found = {name for name, *_ in rows}
    missing = expected - found
    if missing:
        raise AssertionError(f"expected selector identities missing from discovery: {sorted(missing)}")

    groups: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for name, old8, path, _alias in rows:
        groups[path].append((name, old8))

    duplicate_groups = {
        path: tuple(name for name, _old8 in members)
        for path, members in groups.items()
        if len(members) > 1
    }

    assert set(duplicate_groups.get("1011", ())) == {"second", "cadr"}
    assert set(duplicate_groups.get("101111", ())) == {"fourth", "cadddr"}

    bounded = [row for row in rows if row[0] in expected]
    unique_paths = {path for name, old8, path, alias in bounded}
    assert len(bounded) == 8
    assert len(unique_paths) == 6

    legacy_text = LEGACY_AUDIT.read_text(encoding="utf-8")
    legacy_conflict = "retain distinct from second" in legacy_text.lower()

    print("name\told-fixed8\tselector-path\tdirect-alias-target")
    for name, old8, path, alias in bounded:
        print(f"{name}\t{old8}\t{path}\t{alias}")

    print("\nquotient-classes")
    for path in sorted(groups, key=lambda p: (len(p), p)):
        members = [name for name, _old8 in groups[path] if name in expected]
        if members:
            print(f"{path}\t{','.join(members)}")

    print("\nsummary")
    print(f"old registered selector-like identities: {len(bounded)}")
    print(f"unique canonical selector paths:       {len(unique_paths)}")
    print(f"duplicate identities eliminated:       {len(bounded) - len(unique_paths)}")
    print(f"legacy #734 second/cadr distinct-policy present: {str(legacy_conflict).lower()}")

    print("\ninterpretation")
    print("PASS: current core source mechanically discovers the same two duplicate path classes")
    print("      as the hand-audited genealogy: second=cadr and fourth=cadddr.")
    print("NOTE: this is research evidence for quotienting identity by canonical path; it is")
    print("      not a production allocation decision. Any arity/error/effect difference would")
    print("      falsify a collapse candidate before migration.")


if __name__ == "__main__":
    main()
