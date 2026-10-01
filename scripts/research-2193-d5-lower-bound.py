#!/usr/bin/env python3
"""#2193 — D5 lower-bound witness.

Research-only. This script proves a tiny observational lower bound:
with identical call syntax, ordinary eager closures and raw-form transformers
cannot both be represented by one undifferentiated call mode.

It does NOT prove that the discriminator must be D5 code 00101.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MACRO_TESTS = ROOT / "crates" / "sens" / "tests" / "macro_derivation.rs"
EVALUATOR = ROOT / "crates" / "sens" / "src" / "eval" / "mod.rs"
CLOSURES = ROOT / "crates" / "sens" / "src" / "eval" / "closures.rs"


@dataclass(frozen=True)
class Outcome:
    ordinary_ok: bool
    transformer_ok: bool


def one_mode(eager: bool) -> Outcome:
    """One global call policy for both ordinary closure and transformer."""
    # Witness call shape:
    #   (f (quote ok) never-defined)
    #
    # Ordinary closure semantics require eager evaluation. If not eager, an
    # undefined unused operand would cease to fail before body execution.
    ordinary_ok = eager

    # Transformer semantics require raw preservation. If eager, the undefined
    # unused operand fails before the transformer body can ignore it.
    transformer_ok = not eager

    return Outcome(ordinary_ok=ordinary_ok, transformer_ok=transformer_ok)


def two_mode() -> Outcome:
    """One discriminator selecting eager ordinary vs raw transformer call mode."""
    ordinary_eager = True
    transformer_eager = False
    return Outcome(
        ordinary_ok=ordinary_eager,
        transformer_ok=not transformer_eager,
    )


def source_witnesses() -> None:
    tests = MACRO_TESTS.read_text(encoding="utf-8")
    evaluator = EVALUATOR.read_text(encoding="utf-8")
    closures = CLOSURES.read_text(encoding="utf-8")

    # Existing observable transformer behavior.
    assert "language_owned_defmacro_preserves_unevaluated_arguments" in tests
    assert "never-defined" in tests

    # Ordinary call path evaluates arguments before semantic invocation.
    assert "values.push(evaluate(argument, environment)?)" in evaluator

    # Transformer call path receives raw Expr and quotes it instead.
    assert "Some(Value::Macro(closure))" in evaluator
    assert "pub(super) fn apply_macro(" in closures
    assert "slots.push(quoted(argument)?); // Do NOT evaluate arguments" in closures


def main() -> None:
    source_witnesses()

    one_mode_rows = {
        "ordinary-eager": one_mode(True),
        "raw": one_mode(False),
    }

    for row in one_mode_rows.values():
        assert not (row.ordinary_ok and row.transformer_ok)

    split = two_mode()
    assert split.ordinary_ok and split.transformer_ok

    print("D5 semantic lower-bound witness: PASS")
    print("same-call-syntax=yes")
    print("one-mode-models=2")
    for name, row in one_mode_rows.items():
        print(
            f"{name}: ordinary={'PASS' if row.ordinary_ok else 'FAIL'} "
            f"transformer={'PASS' if row.transformer_ok else 'FAIL'}"
        )
    print("one-mode-satisfies-both=0")
    print("one-discriminator-model: ordinary=PASS transformer=PASS")
    print("lower-bound=at-least-one-observable-stage/call-mode-discriminator")
    print("STRICT-D4-ONLY-WITHOUT-DISCRIMINATOR=FALSIFIED")
    print("NON-CONCLUSION: discriminator representation is not fixed")
    print("NON-CONCLUSION: D5 address 00101 is not ratified")


if __name__ == "__main__":
    main()
