#!/usr/bin/env python3
"""#2162 — executable D4 polarity witness over current Core1.

Research-only. The script tests whether Candidate A's within-pair orientation
matches concrete operational asymmetries in lib/core1.lisp. It does not make
bit geometry semantic authority.
"""

from __future__ import annotations

from itertools import product
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
CORE1 = ROOT / "lib" / "core1.lisp"

PAIR_PREFIX = {
    "APPLY/EVAL": "000",
    "LAMBDA/DEFINE": "001",
    "EVCON/EVLIS": "011",
    "LOOKUP/BIND": "111",
}

PAIR_MEMBERS = {
    "APPLY/EVAL": ("APPLY", "EVAL"),
    "LAMBDA/DEFINE": ("LAMBDA", "DEFINE"),
    "EVCON/EVLIS": ("EVCON", "EVLIS"),
    "LOOKUP/BIND": ("LOOKUP", "BIND"),
}

# The member with the stronger current "context expansion / construction"
# witness. These preferences are justified below from executable Core1 source.
BIT1_EVIDENCE = {
    "APPLY/EVAL": "EVAL",
    "LAMBDA/DEFINE": "DEFINE",
    "EVCON/EVLIS": "EVLIS",
    "LOOKUP/BIND": "BIND",
}


def strip_comments(source: str) -> str:
    return "\n".join(line.split(";", 1)[0] for line in source.splitlines())


def extract_top_level_form(source: str, marker: str) -> str:
    start = source.find(marker)
    if start < 0:
        raise AssertionError(f"missing marker: {marker}")

    depth = 0
    in_string = False
    escaped = False
    seen_open = False

    for i in range(start, len(source)):
        ch = source[i]

        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue

        if ch == "(":
            depth += 1
            seen_open = True
        elif ch == ")":
            depth -= 1
            if seen_open and depth == 0:
                return source[start : i + 1]

    raise AssertionError(f"unterminated form: {marker}")


def token_count(form: str, token: str) -> int:
    return len(re.findall(rf"(?<![A-Za-z0-9-]){re.escape(token)}(?![A-Za-z0-9-])", form))


def evidence(core1: str) -> dict[str, bool]:
    lookup = extract_top_level_form(core1, "(00001001 C1-LOOKUP\n")
    bind = extract_top_level_form(core1, "(00001001 C1-BIND\n")
    evlis = extract_top_level_form(core1, "(00001001 C1-EVLIS\n")
    evcon = extract_top_level_form(core1, "(00001001 C1-EVCON\n")
    apply_ = extract_top_level_form(core1, "(00001001 C1-APPLY\n")
    eval_ = extract_top_level_form(core1, "(00001001 C1-EVAL\n")
    eval_program = extract_top_level_form(core1, "(00001001 C1-EVAL-PROGRAM\n")
    definitionp = extract_top_level_form(core1, "(00001001 C1-DEFINITIONP\\n")

    # LOOKUP reads existing bindings; BIND constructs fresh environment cells.
    lookup_bind = (
        "(00000100" not in lookup
        and token_count(bind, "00000100") >= 2
        and "C1-BIND" in bind
    )

    # EVCON selects a branch; EVLIS builds an evaluated list with CONS.
    evcon_evlis = (
        "(00000100 FIRST REST)" in evlis
        and "(00000100 FIRST REST)" not in evcon
        and "C1-EVLIS" in evlis
        and "C1-EVCON" in evcon
    )

    # EVAL owns contextual interpretation breadth; APPLY consumes a resolved FN.
    contextual_helpers = ("C1-LOOKUP", "C1-EVCON", "C1-BIND", "C1-EVLIS", "C1-APPLY")
    eval_breadth = sum(token_count(eval_, x) for x in contextual_helpers)
    apply_breadth = sum(token_count(apply_, x) for x in contextual_helpers)
    apply_eval = eval_breadth > apply_breadth and "C1-APPLY-PRIMITIVE" in apply_

    # LAMBDA creates a closure from current lexical context; DEFINE is admitted
    # only at program/top-level and extends GLOBAL with a new binding cell.
    lambda_define = (
        "C1-LAMBDA-NAMEP" in eval_
        and "FUNCTION" in eval_
        and "C1-DEFINITIONP" in eval_program
        and "C1-DEFINE-NAMEP" in definitionp
        and re.search(r"\\(00000100\\s+\\(00000100", eval_program) is not None
        and "GLOBAL" in eval_program
    )

    return {
        "APPLY/EVAL": apply_eval,
        "LAMBDA/DEFINE": lambda_define,
        "EVCON/EVLIS": evcon_evlis,
        "LOOKUP/BIND": lookup_bind,
    }


def orientation_rows() -> list[tuple[int, dict[str, tuple[str, str]]]]:
    rows = []
    pair_names = tuple(PAIR_PREFIX)

    for bits in product((0, 1), repeat=len(pair_names)):
        mapping = {}
        score = 0

        for pair_name, flip in zip(pair_names, bits):
            a, b = PAIR_MEMBERS[pair_name]
            zero, one = (a, b) if flip == 0 else (b, a)
            mapping[pair_name] = (zero, one)
            if one == BIT1_EVIDENCE[pair_name]:
                score += 1

        rows.append((score, mapping))

    return rows


def main() -> None:
    core1 = strip_comments(CORE1.read_text(encoding="utf-8"))
    observed = evidence(core1)

    assert all(observed.values()), observed

    rows = orientation_rows()
    assert len(rows) == 16

    best = max(score for score, _ in rows)
    winners = [mapping for score, mapping in rows if score == best]

    assert best == 4
    assert len(winners) == 1

    winner = winners[0]
    assert winner["APPLY/EVAL"] == ("APPLY", "EVAL")
    assert winner["LAMBDA/DEFINE"] == ("LAMBDA", "DEFINE")
    assert winner["EVCON/EVLIS"] == ("EVCON", "EVLIS")
    assert winner["LOOKUP/BIND"] == ("LOOKUP", "BIND")

    print("D4 polarity witness: PASS")
    print("source=lib/core1.lisp")
    for pair_name in PAIR_PREFIX:
        zero, one = winner[pair_name]
        print(f"{PAIR_PREFIX[pair_name]}0={zero} {PAIR_PREFIX[pair_name]}1={one}")
    print("orientation-space=16")
    print("best-operational-evidence-score=4")
    print("best-orientations=1")
    print("NON-CONCLUSION: no universal semantic bit law is proved")
    print("NON-CONCLUSION: pair placement remains subject to #2158 owner ratification")


if __name__ == "__main__":
    main()
