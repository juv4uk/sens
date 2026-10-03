#!/usr/bin/env python3
"""#2580 — Hart whole-call vs SENS operand-only macro input witness.

Research-only. Historical Hart behavior is an explicit source premise from
AIM-057; this program does not manufacture historical evidence or allocate a
binary identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL_MOD = ROOT / "crates" / "sens" / "src" / "eval" / "mod.rs"
CLOSURES = ROOT / "crates" / "sens" / "src" / "eval" / "closures.rs"


@dataclass(frozen=True)
class Invocation:
    head: str
    operands: tuple[str, ...]


def hart_whole_call(invocation: Invocation) -> tuple[str, tuple[str, ...]]:
    """Hart AIM-057 premise: macro receives a form beginning with macro name."""
    return invocation.head, invocation.operands


def sens_operands_only(invocation: Invocation) -> tuple[str, ...]:
    """Current SENS apply_macro input: raw operand Exprs only."""
    return invocation.operands


def source_controls() -> None:
    evaluator = EVAL_MOD.read_text(encoding="utf-8")
    closures = CLOSURES.read_text(encoding="utf-8")

    # evaluate_list separates the head and passes only the operand tail.
    assert "&items[1..]," in evaluator

    # Both macro dispatch paths forward only the already-separated arguments.
    needle = "closures::apply_macro(closure.clone(), arguments, environment, span)"
    assert evaluator.count(needle) >= 2

    # The macro application API has no invocation-head parameter.
    start = closures.index("pub(super) fn apply_macro(")
    signature = closures[start : closures.index(") -> Result<EvalStep", start)]
    assert "closure: Rc<Closure>" in signature
    assert "arguments: &[Expr]" in signature
    assert "calling_environment: &Environment" in signature
    assert "head_name" not in signature
    assert "head_expr" not in signature
    assert "head_sid" not in signature


def main() -> None:
    source_controls()

    a = Invocation("macro-a", ("payload",))
    b = Invocation("macro-b", ("payload",))

    hart_a = hart_whole_call(a)
    hart_b = hart_whole_call(b)
    sens_a = sens_operands_only(a)
    sens_b = sens_operands_only(b)

    # Same transformer + same operand, different call head.
    assert a.head != b.head
    assert a.operands == b.operands

    # Whole-call protocol exposes the alias/head distinction.
    assert hart_a != hart_b
    assert hart_a[0] == "macro-a"
    assert hart_b[0] == "macro-b"

    # Operand-only protocol creates a deliberate information collision.
    assert sens_a == sens_b == ("payload",)

    # Old coarse A/B/C projection cannot express this distinction.
    hart_abc = ("RAW", "NO-EXPLICIT-CALLER-ENV", "FORM-RESULT")
    sens_abc = ("RAW", "NO-EXPLICIT-CALLER-ENV", "FORM-RESULT")
    assert hart_abc == sens_abc

    print("MACRO-CALL-FORM-WITNESS=PASS")
    print("historical-premise=Hart-AIM-057-whole-form-input")
    print("HART-INPUT-SHAPE=WHOLE-CALL")
    print("SENS-INPUT-SHAPE=OPERANDS-ONLY")
    print("alias-countermodel=(macro-a payload)!=(macro-b payload)-for-Hart")
    print("operand-collision=[payload]==[payload]-for-current-SENS")
    print("OLD-ABC-PROJECTION=COLLISION")
    print("CALL-PACKAGING=INDEPENDENT-AXIS")
    print("BINARY-OBJECT=UNPLACED")
    print("EXACT-WIDTH=UNRESOLVED")
    print("NON-CONCLUSION=no-placement-from-call-packaging-axis")


if __name__ == "__main__":
    main()
