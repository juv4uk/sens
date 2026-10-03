#!/usr/bin/env python3
"""#2631 — minimize returned-form protocol against D4 EVAL + caller-context carrier.

Research-only. No width, coordinate, or resident is allocated.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLOSURES = ROOT / "crates" / "sens" / "src" / "eval" / "closures.rs"
EVAL_IO = ROOT / "crates" / "sens" / "src" / "eval" / "special_forms" / "io.rs"


def source_controls() -> None:
    closures = CLOSURES.read_text(encoding="utf-8")
    eval_io = EVAL_IO.read_text(encoding="utf-8")

    # Current macro path: transformer body returns a value, converted to syntax,
    # then tail-evaluated specifically in the caller environment.
    assert "let expanded_value = evaluate(last, &local_environment)?;" in closures
    assert "let expanded_expr = value_to_expr(expanded_value, span)?;" in closures
    assert "expression: expanded_expr," in closures
    assert "environment: calling_environment.clone()," in closures

    # Existing EVAL path reuses the same data->code conversion and evaluates in
    # an explicitly supplied Environment. This is the operation root donor.
    assert "let expression = closures::value_to_expr(datum, span)?;" in eval_io
    assert "evaluate(&lowered[0], environment)" in eval_io


def eval_symbol(form: str, environment: dict[str, str]) -> str:
    """Bounded explicit-context model of evaluating one returned symbol form."""
    return environment[form]


def main() -> None:
    source_controls()

    returned_form = "x"
    caller_a = {"x": "A"}
    caller_b = {"x": "B"}

    # Direct-value protocol returns the form/data itself.
    direct = returned_form
    assert direct == "x"

    # Returned-form protocol is ordinary evaluation once the chosen caller
    # context is explicit.
    reevaluated_a = eval_symbol(returned_form, caller_a)
    reevaluated_b = eval_symbol(returned_form, caller_b)
    assert reevaluated_a == "A"
    assert reevaluated_b == "B"

    # Context choice is observably relevant; EVAL alone does not choose which
    # caller context must be used.
    assert reevaluated_a != reevaluated_b

    # Therefore the factor does not require a new execution root beyond EVAL.
    # It is a policy over an admitted operation plus the independently charged
    # caller-environment carrier premise from R3 (#2630/#2637).
    root_status = "POLICY-OVER-ROOT"

    print("ROOT-MIN-R4=PASS")
    print("FACTOR=returned-form-protocol")
    print("DIRECT-VALUE=x")
    print("CALLER-A-REEVAL=A")
    print("CALLER-B-REEVAL=B")
    print("DATA-TO-CODE=SHARED-WITH-D4-EVAL")
    print("EXECUTION-ROOT=D4-EVAL")
    print("CALLER-CONTEXT-SELECTION=OBSERVABLE")
    print("CALLER-CONTEXT-DEPENDENCY=R3-CARRIER-PREMISE")
    print(f"ROOT-STATUS={root_status}")
    print("WIDTH=UNKNOWN")
    print("COORDINATE=UNPLACED")
    print("NEW-RESIDENTS=0")
    print("NON-CONCLUSION=no-D5-D6-placement")


if __name__ == "__main__":
    main()
