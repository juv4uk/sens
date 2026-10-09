#!/usr/bin/env python3
"""D10 source-only research: finite first-order LEAST GENERAL GENERALIZATION.

Ground constructor terms ONLY. No D1–D9 or D2 syntax semantics, no T5.
Inputs (a) {"a":"literal"} or (b) {"f":"constructor","args":[...]}.
Fresh "hole" variables occur ONLY in the output; repeated (left,right)
disagreement pairs MUST share a variable. Explicit substitutions are witnesses.

Research HOLD: this is neither a resident, a ratification, nor a production
Lisp evaluator. Native SWI-Prolog oracle is independent (see tests/oracles).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

NAME = re.compile(r"[A-Za-zА-Яа-яІіЇїЄєҐґ][\w-]*\Z", flags=re.UNICODE)
MAX_NODES = 128
MAX_DEPTH = 16


class AntiUnifyBlocked(ValueError):
    pass


def ground(t: object, *, depth: int = 0, budget: list[int] | None = None) -> None:
    """Validate exact finite trees; no input variables or ambiguous JSON."""
    if budget is None:
        budget = [MAX_NODES]
    if depth > MAX_DEPTH or budget[0] <= 0:
        raise AntiUnifyBlocked("BOUND: term depth or node budget exceeded")
    budget[0] -= 1
    if not isinstance(t, dict):
        raise AntiUnifyBlocked("GROUND: term must be a tagged dictionary")
    if set(t) == {"a"}:
        if not isinstance(t["a"], str) or not NAME.fullmatch(t["a"]):
            raise AntiUnifyBlocked("ATOM: noncanonical ground symbol")
    elif set(t) == {"f", "args"}:
        if not isinstance(t["f"], str) or not NAME.fullmatch(t["f"]):
            raise AntiUnifyBlocked("CONSTRUCTOR: noncanonical symbol")
        if not isinstance(t["args"], list) or len(t["args"]) > 16:
            raise AntiUnifyBlocked("ARITY: finite ordered arguments only")
        for child in t["args"]:
            ground(child, depth=depth + 1, budget=budget)
    else:
        raise AntiUnifyBlocked("GROUND: only atoms and constructors (no binders, vars or frames)")


def key(t: dict) -> str:
    return json.dumps(t, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def anti_unify(left: dict, right: dict) -> dict:
    """Total deterministic least-general generalizer (modulo variable alpha names)."""
    ground(left)
    ground(right)
    memo: dict[tuple[str, str], str] = {}
    a: list[dict] = []
    b: list[dict] = []

    def step(x: dict, y: dict) -> dict:
        if x == y:
            return x
        if (set(x) == {"f", "args"} and set(y) == {"f", "args"}
                and x["f"] == y["f"] and len(x["args"]) == len(y["args"])):
            return {"f": x["f"],
                    "args": [step(u, v) for u, v in zip(x["args"], y["args"])]}
        pair = (key(x), key(y))
        if pair not in memo:
            name = "V" + str(len(memo))
            memo[pair] = name
            a.append({"hole": name, "term": x})
            b.append({"hole": name, "term": y})
        return {"hole": memo[pair]}

    generalizer = step(left, right)
    result = {"generalizer": generalizer, "left_substitution": a, "right_substitution": b}
    if instantiate(generalizer, a) != left or instantiate(generalizer, b) != right:
        raise AntiUnifyBlocked("WITNESS: substitution fails to reconstruct input")
    return result


def instantiate(pattern: dict, mapping: list[dict]) -> dict:
    """Independent check that an output pattern instantiates to a GROUND term."""
    replacements: dict[str, dict] = {}
    for item in mapping:
        if not isinstance(item, dict) or set(item) != {"hole", "term"}:
            raise AntiUnifyBlocked("WITNESS: malformed mapping")
        label = item["hole"]
        if (not isinstance(label, str) or not re.fullmatch(r"V(?:0|[1-9][0-9]*)", label)
                or label in replacements):
            raise AntiUnifyBlocked("WITNESS: repeated or illegal variable")
        ground(item["term"])
        replacements[label] = item["term"]

    def walk(t: dict) -> dict:
        if not isinstance(t, dict):
            raise AntiUnifyBlocked("WITNESS: malformed pattern")
        if set(t) == {"hole"}:
            if t["hole"] not in replacements:
                raise AntiUnifyBlocked("WITNESS: unbound hole")
            return replacements[t["hole"]]
        if set(t) == {"a"}:
            ground(t)
            return t
        if set(t) == {"f", "args"}:
            return {"f": t["f"], "args": [walk(c) for c in t["args"]]}
        raise AntiUnifyBlocked("WITNESS: invalid tagged generalizer")

    output = walk(pattern)
    ground(output)
    return output


def check_result(left: dict, right: dict, result: dict) -> None:
    """Reconstruction + exact least-general form; weak 'any generalization' is not enough."""
    if not isinstance(result, dict) or set(result) != {
        "generalizer", "left_substitution", "right_substitution"
    }:
        raise AntiUnifyBlocked("RESULT: expected explicit pair of substitutions")
    if (instantiate(result["generalizer"], result["left_substitution"]) != left
            or instantiate(result["generalizer"], result["right_substitution"]) != right):
        raise AntiUnifyBlocked("RESULT: witnesses do not reconstruct source terms")
    if result != anti_unify(left, right):
        raise AntiUnifyBlocked("MINIMALITY: arbitrary generalization or repeated-variable drift")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True,
                        help="JSON array of bounded {left,right} samples, read only")
    args = parser.parse_args(argv)
    try:
        rows = json.loads(args.cases.read_text(encoding="utf-8"))
        if not isinstance(rows, list) or not rows or len(rows) > 2000:
            raise AntiUnifyBlocked("CASES: require 1..2000 finite pairs")
        results = []
        for row in rows:
            if not isinstance(row, dict) or set(row) != {"left", "right"}:
                raise AntiUnifyBlocked("CASES: each row requires exactly left/right")
            result = anti_unify(row["left"], row["right"])
            check_result(row["left"], row["right"], result)
            results.append(result)
        print(json.dumps(results, ensure_ascii=False, separators=(",", ":")))
        return 0
    except (AntiUnifyBlocked, OSError, ValueError, TypeError, RecursionError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
