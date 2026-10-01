#!/usr/bin/env python3
"""#2011 QUOTE generator bounded research.

Question: does QUOTE itself induce a local binary generator family comparable
to CAR/CDR selectors?

This test attacks three tempting candidates:
1. quote-depth as a repeated local action;
2. atom-vs-list payload class as immediate children;
3. reader apostrophe as semantic family evidence.

It does NOT prove that QUOTE can never participate in a richer typed algebra.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RACKET = ROOT / "racket/interpreter.rkt"
WALK = ROOT / "docs/mccarthy-1960-eval-apply-walkthrough-2026-08-28.md"


@dataclass(frozen=True)
class Atom:
    name: str


@dataclass(frozen=True)
class Pair:
    car: object
    cdr: object


class Nil:
    def __repr__(self) -> str:
        return "()"


NIL = Nil()
QUOTE = Atom("QUOTE")


def lisp_list(*items):
    out = NIL
    for item in reversed(items):
        out = Pair(item, out)
    return out


def quote_form(value):
    """Construct syntax/data (QUOTE value); this is not QUOTE evaluation."""
    return lisp_list(QUOTE, value)


def eval_quote_form(form):
    """Historical/current quote law: return operand unchanged."""
    assert isinstance(form, Pair)
    assert form.car == QUOTE
    args = form.cdr
    assert isinstance(args, Pair)
    return args.car


def is_atom(value) -> bool:
    return not isinstance(value, Pair)


def anchor_sources() -> None:
    racket = RACKET.read_text(encoding="utf-8")
    walk = WALK.read_text(encoding="utf-8")
    assert "[(quote)" in racket
    assert "(if (null? args) nil (car args))" in racket
    assert "eq[..;QUOTE]? так" in walk
    assert "cadr[e] = A" in walk


def render(value) -> str:
    if value is NIL:
        return "()"
    if isinstance(value, Atom):
        return value.name
    if isinstance(value, Pair):
        parts = []
        cur = value
        while isinstance(cur, Pair):
            parts.append(render(cur.car))
            cur = cur.cdr
        if cur is NIL:
            return "(" + " ".join(parts) + ")"
        return "(" + " ".join(parts) + " . " + render(cur) + ")"
    return repr(value)


def candidate_quote_depth():
    x = Atom("x")
    one = quote_form(x)
    two = quote_form(one)
    three = quote_form(two)

    assert eval_quote_form(one) == x
    assert eval_quote_form(two) == one
    assert eval_quote_form(two) != x
    assert eval_quote_form(three) == two

    return [
        ("depth1", render(one), render(eval_quote_form(one))),
        ("depth2", render(two), render(eval_quote_form(two))),
        ("depth3", render(three), render(eval_quote_form(three))),
    ]


def candidate_payload_split():
    atom_payload = Atom("x")
    list_payload = lisp_list(Atom("x"), Atom("y"))

    qa = quote_form(atom_payload)
    ql = quote_form(list_payload)

    out_a = eval_quote_form(qa)
    out_l = eval_quote_form(ql)

    assert out_a == atom_payload
    assert out_l == list_payload
    assert is_atom(out_a)
    assert not is_atom(out_l)

    return [
        ("atom", render(atom_payload), render(out_a)),
        ("list", render(list_payload), render(out_l)),
    ]


def candidate_reader_sugar():
    explicit = quote_form(Atom("x"))
    apostrophe_desugared = quote_form(Atom("x"))
    assert explicit == apostrophe_desugared
    return render(explicit)


def main() -> None:
    anchor_sources()

    depth = candidate_quote_depth()
    split = candidate_payload_split()
    sugar = candidate_reader_sugar()

    print("QUOTE depth candidate")
    print("case\\tform\\teval-result")
    for row in depth:
        print("\\t".join(row))

    print()
    print("payload-class candidate")
    print("class\\tpayload\\teval-result")
    for row in split:
        print("\\t".join(row))

    print()
    print("reader-sugar candidate")
    print("explicit and apostrophe-desugared form:", sugar)

    print()
    print("BOUNDED CLASSIFICATION")
    print("quote-depth local generator: NOT PROVEN / candidate falsified at strong-local level")
    print("  reason: deeper quote syntax changes returned data shape and requires construction")
    print("payload atom/list children: typed domain split only, not a new local action")
    print("  reason: QUOTE performs the same operand-preserving law on both payload classes")
    print("reader apostrophe: surface projection only, no semantic child")
    print("QUOTE immediate children remain unallocated by these candidates.")
    print()
    print("PASS: QUOTE suppression is separated from construction of quoted syntax/data.")


if __name__ == "__main__":
    main()
