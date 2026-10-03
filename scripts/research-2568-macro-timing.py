#!/usr/bin/env python3
"""#2568 — Hart DEFINE-time vs SENS evaluation-time macro timing witness.

Research-only. Historical Hart behavior is an explicit source premise from
MIT AI Memo 57 (1963); this program does not manufacture historical evidence.

It proves only that two expansion loci are observably distinct under one
minimal redefinition trace.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLOSURES = ROOT / "crates" / "sens" / "src" / "eval" / "closures.rs"
LIVE_TEST = ROOT / "crates" / "sens" / "tests" / "post_d4_macro_timing.rs"


@dataclass(frozen=True)
class Trace:
    macro_at_definition: str
    macro_at_call: str


def hart_define_time(trace: Trace) -> str:
    """Hart AIM-057 premise: DEFINE performs macro expansion."""
    expanded_body = trace.macro_at_definition
    return expanded_body


def sens_evaluation_time(trace: Trace) -> str:
    """Current SENS model: macro call remains until evaluator invocation."""
    return trace.macro_at_call


def source_controls() -> None:
    closures = CLOSURES.read_text(encoding="utf-8")
    live_test = LIVE_TEST.read_text(encoding="utf-8")

    assert "pub(super) fn apply_macro(" in closures
    assert "slots.push(quoted(argument)?)" in closures
    assert "let expanded_expr = value_to_expr(expanded_value, span)?;" in closures
    assert "environment: calling_environment.clone()" in closures

    # The live runtime witness pins the current observation independently of
    # this abstract two-model trace.
    assert "phase-transformer" in live_test
    assert 'assert_eq!(' in live_test
    assert '"NEW"' in live_test


def main() -> None:
    source_controls()

    trace = Trace(macro_at_definition="OLD", macro_at_call="NEW")

    hart = hart_define_time(trace)
    sens = sens_evaluation_time(trace)

    assert hart == "OLD"
    assert sens == "NEW"
    assert hart != sens

    print("MACRO-TIMING-WITNESS=PASS")
    print("historical-premise=Hart-AIM-057-DEFINE-performs-expansion")
    print("trace=define-macro-OLD -> define-containing-function -> redefine-macro-NEW -> call")
    print(f"definition-time-observation={hart}")
    print(f"evaluation-time-observation={sens}")
    print("EXPANSION-TIMING=INDEPENDENT-AXIS")
    print("BINARY-OBJECT=UNPLACED")
    print("EXACT-WIDTH=UNRESOLVED")
    print("NON-CONCLUSION=no-placement-from-timing-axis")


if __name__ == "__main__":
    main()
