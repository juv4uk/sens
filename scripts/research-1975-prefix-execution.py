#!/usr/bin/env python3
"""#1975 — execute proven selector descendants as root + suffix program.

Research-only. This script deliberately does NOT use a descendant dispatch table.
It knows only two root mechanisms (CAR/CDR), interprets suffix bits as ordered
composition, then checks parity against the current bounded selector definitions
mechanically parsed from lib/core.lisp.

Path sharing is NOT treated as semantic identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "lib/core.lisp"

DEFINE = "00001001"
LAMBDA = "00001000"
CAR = "00000101"
CDR = "00000110"

ROOT_OPS = {
    "101": CAR,
    "110": CDR,
}

BIT_OPS = {
    "0": CAR,
    "1": CDR,
}

EXPECTED = {
    "caar",
    "cadr",
    "cddr",
    "second",
    "third",
    "fourth",
    "fifth",
    "cadddr",
}


@dataclass(frozen=True)
class Pair:
    car: object
    cdr: object


class SelectorDomainError(Exception):
    pass


def car(value: object) -> object:
    if not isinstance(value, Pair):
        raise SelectorDomainError("CAR expects Pair")
    return value.car


def cdr(value: object) -> object:
    if not isinstance(value, Pair):
        raise SelectorDomainError("CDR expects Pair")
    return value.cdr


MECHANISM = {
    CAR: car,
    CDR: cdr,
}


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
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
            tokens.append(c)
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
            tokens.append(text[start:i])
            continue

        start = i
        while i < len(text) and not text[i].isspace() and text[i] not in "();":
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

    out = []
    while pos < len(tokens):
        out.append(one())
    return out


def selector_ops(expr: object, parameter: str) -> tuple[str, ...] | None:
    """Return outer-to-inner primitive selector ops from a pure selector body."""
    if expr == parameter:
        return ()
    if not isinstance(expr, list) or len(expr) != 2:
        return None
    head, argument = expr
    if head not in (CAR, CDR):
        return None
    rest = selector_ops(argument, parameter)
    if rest is None:
        return None
    return (head,) + rest


def selector_word(ops: tuple[str, ...]) -> str | None:
    if not ops:
        return None
    root = "101" if ops[0] == CAR else "110"
    suffix = "".join("0" if op == CAR else "1" for op in ops[1:])
    return root + suffix


def discover_current_definitions() -> dict[str, tuple[str, object, str]]:
    """name -> (word, source-body, parameter), resolving direct aliases."""
    forms = parse_many(tokenize(CORE.read_text(encoding="utf-8")))
    direct: dict[str, tuple[str, object, str]] = {}
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
            body = value[2]
            ops = selector_ops(body, parameter)
            if ops:
                word = selector_word(ops)
                assert word is not None
                direct[name] = (word, body, parameter)

    changed = True
    while changed:
        changed = False
        for name, target in aliases.items():
            if name not in direct and target in direct:
                direct[name] = direct[target]
                changed = True

    return direct


def word_ops(word: str) -> tuple[str, ...]:
    if len(word) < 3 or any(bit not in "01" for bit in word):
        raise ValueError(f"malformed selector word: {word!r}")
    root = word[:3]
    if root not in ROOT_OPS:
        raise ValueError(f"word {word!r} is outside proven CAR/CDR families")

    return (ROOT_OPS[root],) + tuple(BIT_OPS[bit] for bit in word[3:])


def execute_word(word: str, value: object) -> object:
    """Execute root + suffix with no descendant lookup.

    The selector word stores operations outer-to-inner, e.g.
      1011 = CAR ∘ CDR.
    Function application must therefore apply the innermost op first.
    """
    ops = word_ops(word)
    out = value
    for op in reversed(ops):
        out = MECHANISM[op](out)
    return out


def eval_source_selector(expr: object, parameter: str, value: object) -> object:
    if expr == parameter:
        return value
    if not isinstance(expr, list) or len(expr) != 2:
        raise ValueError("source selector body left the bounded CAR/CDR grammar")
    head, argument = expr
    if head not in MECHANISM:
        raise ValueError(f"unexpected source primitive {head!r}")
    return MECHANISM[head](eval_source_selector(argument, parameter, value))


def full_tree(depth: int, label: str = "r") -> object:
    if depth == 0:
        return label
    return Pair(
        full_tree(depth - 1, label + "0"),
        full_tree(depth - 1, label + "1"),
    )


def assert_same_outcome(fn_a, fn_b) -> None:
    try:
        a = ("value", fn_a())
    except SelectorDomainError as exc:
        a = ("error", str(exc))
    try:
        b = ("value", fn_b())
    except SelectorDomainError as exc:
        b = ("error", str(exc))
    assert a == b, (a, b)


def negative_tests() -> None:
    for bad in ("", "1", "10", "000", "0010", "1110", "10x1"):
        try:
            execute_word(bad, full_tree(3))
        except ValueError:
            pass
        else:
            raise AssertionError(f"malformed/out-of-family word accepted: {bad!r}")

    # Domain failure should match ordinary selector semantics.
    assert_same_outcome(
        lambda: execute_word("101", "atom"),
        lambda: car("atom"),
    )
    assert_same_outcome(
        lambda: execute_word("110", "atom"),
        lambda: cdr("atom"),
    )


def main() -> None:
    discovered = discover_current_definitions()
    missing = EXPECTED - set(discovered)
    if missing:
        raise AssertionError(f"current selector definitions missing: {sorted(missing)}")

    fixtures = [full_tree(7, "a"), full_tree(7, "b"), full_tree(8, "z")]

    print("name\tword\troot\tsuffix\tparity")
    unique_words = set()
    for name in sorted(EXPECTED, key=lambda n: (len(discovered[n][0]), discovered[n][0], n)):
        word, body, parameter = discovered[name]
        unique_words.add(word)
        for fixture in fixtures:
            assert_same_outcome(
                lambda w=word, x=fixture: execute_word(w, x),
                lambda e=body, p=parameter, x=fixture: eval_source_selector(e, p, x),
            )
        print(f"{name}\t{word}\t{word[:3]}\t{word[3:] or '-'}\tPASS")

    # Positive control laws from #1962.
    assert discovered["caar"][0] == "1010"
    assert discovered["cadr"][0] == "1011"
    assert discovered["cddr"][0] == "1101"
    assert discovered["fourth"][0] == "101111"
    assert discovered["cadddr"][0] == "101111"

    negative_tests()

    print("\nmechanism-accounting")
    print(f"root mechanisms known by executor:       {len(ROOT_OPS)}")
    print(f"suffix actions known by executor:        {len(BIT_OPS)}")
    print(f"bounded selector names parity-checked:   {len(EXPECTED)}")
    print(f"unique descendant/root words exercised:  {len(unique_words)}")
    print("per-descendant execution lookup rows:    0")
    print("semantic nodes quotiented by witness:    0")
    print()
    print("PASS: proven selector words execute as root + suffix program")
    print("without a descendant dispatch table; current bounded source definitions")
    print("produce the same outcomes on all fixtures and domain-error controls.")
    print("GUARD: shared execution paths remain weaker than semantic identity.")


if __name__ == "__main__":
    main()
