#!/usr/bin/env python3
"""#1968 — bounded EQ-family falsifier against selector-strength local actions.

Research-only. This does NOT prove that no EQ-family generator can exist.
It asks a narrower falsifiable question:

Can NULL/EQUAL/MEMBER be explained by a small local law comparable to the
CAR/CDR positive control — composition-only, no new branching/recursion,
and no candidate-specific hidden table?

Current core source is parsed mechanically. Human names select the bounded
candidates only; dependency evidence comes from exact binary call heads.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "lib/core.lisp"
TABLE = ROOT / "lib/generated/function-table.lisp"

DEFINE = "00001001"
LAMBDA = "00001000"

SEED = {
    "00000001": "QUOTE",
    "00000010": "ATOM",
    "00000011": "EQ",
    "00000100": "CONS",
    "00000101": "CAR",
    "00000110": "CDR",
    "00000111": "COND",
}

EQ = "00000011"
CAR = "00000101"
CDR = "00000110"
COND = "00000111"

CANDIDATES = ("null?", "equal?", "member?")
CONTROLS = ("caar", "cadr")


@dataclass
class Definition:
    name: str
    code: str
    params: tuple[str, ...]
    body: object


def tokenize(text: str) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(text):
        c = text[i]
        if c.isspace():
            i += 1
            continue
        if c == ";":
            while i < len(text) and text[i] != "\n":
                i += 1
            continue
        if c in "()":
            out.append(c)
            i += 1
            continue
        if c == '"':
            start = i
            i += 1
            escaped = False
            while i < len(text):
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
            out.append(text[start:i])
            continue
        start = i
        while i < len(text) and not text[i].isspace() and text[i] not in "();":
            i += 1
        out.append(text[start:i])
    return out


def parse_many(tokens: list[str]) -> list[object]:
    pos = 0

    def one() -> object:
        nonlocal pos
        if pos >= len(tokens):
            raise ValueError("unexpected end")
        token = tokens[pos]
        pos += 1
        if token == "(":
            items = []
            while True:
                if pos >= len(tokens):
                    raise ValueError("unclosed list")
                if tokens[pos] == ")":
                    pos += 1
                    return items
                items.append(one())
        if token == ")":
            raise ValueError("unexpected close")
        return token

    forms = []
    while pos < len(tokens):
        forms.append(one())
    return forms


def current_codes() -> dict[str, str]:
    out: dict[str, str] = {}
    pattern = re.compile(
        r"^\s*\(([01]{8})\s+identity:[01]{8}/surface:([^\s()]+)"
    )
    for line in TABLE.read_text(encoding="utf-8").splitlines():
        m = pattern.match(line)
        if m:
            code, name = m.groups()
            out[name] = code
    return out


def definitions() -> dict[str, Definition]:
    codes = current_codes()
    out: dict[str, Definition] = {}

    for form in parse_many(tokenize(CORE.read_text(encoding="utf-8"))):
        if not isinstance(form, list) or len(form) < 3 or form[0] != DEFINE:
            continue
        name = form[1]
        value = form[2]
        if not isinstance(name, str) or name not in codes:
            continue
        if not (
            isinstance(value, list)
            and len(value) >= 3
            and value[0] == LAMBDA
            and isinstance(value[1], list)
            and all(isinstance(p, str) for p in value[1])
        ):
            continue
        out[name] = Definition(name, codes[name], tuple(value[1]), value[2])
    return out


def walk(expr: object):
    yield expr
    if isinstance(expr, list):
        for item in expr:
            yield from walk(item)


def call_heads(expr: object) -> list[str]:
    heads: list[str] = []

    def visit(node: object) -> None:
        if not isinstance(node, list) or not node:
            return
        head = node[0]
        if isinstance(head, str):
            heads.append(head)
        for child in node[1:]:
            visit(child)

    visit(expr)
    return heads


def seed_support(expr: object) -> set[str]:
    return {SEED[h] for h in call_heads(expr) if h in SEED}


def pure_selector_composition(expr: object, parameter: str) -> bool:
    """Positive-control grammar: nested unary CAR/CDR over exactly one parameter."""
    if expr == parameter:
        return True
    if not isinstance(expr, list) or len(expr) != 2:
        return False
    head, arg = expr
    return head in (CAR, CDR) and pure_selector_composition(arg, parameter)


def features(d: Definition) -> dict[str, object]:
    heads = call_heads(d.body)
    seeds = seed_support(d.body)
    self_recursive = d.code in heads
    branch = COND in heads
    direct_eq = EQ in heads
    selector_control = (
        len(d.params) == 1 and pure_selector_composition(d.body, d.params[0])
    )
    return {
        "arity": len(d.params),
        "seeds": seeds,
        "self_recursive": self_recursive,
        "branch": branch,
        "direct_eq": direct_eq,
        "selector_control": selector_control,
    }


def main() -> None:
    defs = definitions()
    required = set(CANDIDATES) | set(CONTROLS)
    missing = required - set(defs)
    if missing:
        raise AssertionError(f"missing bounded definitions: {sorted(missing)}")

    print(
        "name\tcode\tarity\tseed-support\tdirect-EQ\tCOND\tself-recursion\t"
        "selector-strength-composition"
    )

    rows = {}
    for name in CONTROLS + CANDIDATES:
        d = defs[name]
        f = features(d)
        rows[name] = f
        seeds = ",".join(sorted(f["seeds"])) or "-"
        print(
            f"{name}\t{d.code}\t{f['arity']}\t{seeds}\t"
            f"{str(f['direct_eq']).lower()}\t"
            f"{str(f['branch']).lower()}\t"
            f"{str(f['self_recursive']).lower()}\t"
            f"{str(f['selector_control']).lower()}"
        )

    # Positive control: the bounded criterion must accept actual selector compositions.
    assert rows["caar"]["selector_control"]
    assert rows["cadr"]["selector_control"]
    assert not rows["caar"]["branch"]
    assert not rows["caar"]["self_recursive"]

    # EQ-family candidates all fail the selector-strength local-action class.
    for name in CANDIDATES:
        assert not rows[name]["selector_control"]

    # NULL is not even an EQ-direct definition in current Core4.
    assert not rows["null?"]["direct_eq"]

    # EQUAL really does extend/use EQ, but adds independent structure/control.
    assert rows["equal?"]["direct_eq"]
    assert rows["equal?"]["branch"]
    assert rows["equal?"]["self_recursive"]
    assert {"ATOM", "CAR", "CDR", "COND", "EQ"}.issubset(rows["equal?"]["seeds"])

    # MEMBER is recursive traversal/control and delegates structural comparison.
    assert rows["member?"]["branch"]
    assert rows["member?"]["self_recursive"]
    assert {"ATOM", "CAR", "CDR", "COND"}.issubset(rows["member?"]["seeds"])

    print()
    print("classification")
    print("EQ -> EQUAL : typed-family candidate only; strong local binary action NOT proven")
    print("EQ -> NULL  : rejected as immediate EQ child in this bounded corpus")
    print("EQ -> MEMBER: rejected as immediate EQ child in this bounded corpus")
    print("0110/0111   : remain unallocated by this experiment")
    print()
    print("PASS: positive selector control succeeds while all three EQ candidates")
    print("fail the same small composition-only/no-control/no-recursion criterion.")
    print("This is bounded negative evidence, not a proof that no richer EQ generator exists.")


if __name__ == "__main__":
    main()
