#!/usr/bin/env python3
"""#2522 — FEXPR/FSUBR protocol-cube witness.

Research-only. Separates three observable call-protocol dimensions:

A. operand mode: eager values vs raw forms
B. caller-context access: unavailable vs explicit caller environment
C. result protocol: direct value vs returned form re-evaluated in caller context

Historical Lisp 1.5 Appendix B supplies FEXPR/FSUBR with raw operands plus the
current a-list. The current SENS macro runtime is inspected only as a later
comparison point; it is not historical authority.

No binary coordinate or width is assigned.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLOSURES_RS = ROOT / "crates" / "sens" / "src" / "eval" / "closures.rs"


class OperandMode(str, Enum):
    EAGER = "eager"
    RAW = "raw"


class EnvMode(str, Enum):
    NONE = "no-direct-caller-env"
    CALLER = "explicit-caller-env"


class ResultMode(str, Enum):
    VALUE = "direct-value"
    REEVAL = "form-reeval-in-caller"


@dataclass(frozen=True)
class Protocol:
    operand: OperandMode
    env: EnvMode
    result: ResultMode


HISTORICAL_FEXPR = Protocol(
    OperandMode.RAW,
    EnvMode.CALLER,
    ResultMode.VALUE,
)

CURRENT_TRANSFORMER = Protocol(
    OperandMode.RAW,
    EnvMode.NONE,
    ResultMode.REEVAL,
)


def raw_operand_probe(protocol: Protocol) -> tuple[str, str]:
    """Body uses only first operand; second operand is undefined."""
    if protocol.operand is OperandMode.EAGER:
        return ("error", "undefined-second-operand")
    return ("ok", "first-form-preserved")


def caller_env_probe(protocol: Protocol) -> tuple[str, str]:
    """Body requests caller-only binding x=42, not supplied as an operand."""
    if protocol.env is EnvMode.CALLER:
        return ("ok", "42")
    return ("error", "caller-env-unavailable")


def result_protocol_probe(protocol: Protocol) -> tuple[str, str]:
    """Body returns the symbol/form x while caller binds x=42."""
    returned = "x"
    if protocol.result is ResultMode.REEVAL:
        return ("ok", "42")
    return ("ok", returned)


def signature(protocol: Protocol):
    return (
        raw_operand_probe(protocol),
        caller_env_probe(protocol),
        result_protocol_probe(protocol),
    )


def all_protocols() -> dict[str, Protocol]:
    rows: dict[str, Protocol] = {}
    for raw, env, reeval in product((0, 1), repeat=3):
        protocol = Protocol(
            OperandMode.RAW if raw else OperandMode.EAGER,
            EnvMode.CALLER if env else EnvMode.NONE,
            ResultMode.REEVAL if reeval else ResultMode.VALUE,
        )
        rows[f"{raw}{env}{reeval}"] = protocol
    return rows


def source_classify_current_transformer() -> None:
    source = CLOSURES_RS.read_text(encoding="utf-8")
    start = source.index("pub(super) fn apply_macro(")
    end = source.index("pub(super) fn value_to_expr", start)
    macro = source[start:end]

    # Raw operands: current macro path quotes source Expr rather than evaluating it.
    assert "slots.push(quoted(argument)?); // Do NOT evaluate arguments" in macro

    # Transformer body runs in a frame derived from the transformer's captured closure.
    assert "let local_environment = call_frame(&closure, slots);" in macro
    assert "let expanded_value = evaluate(last, &local_environment)?;" in macro

    # Result protocol is explicitly data -> code -> caller-environment evaluation.
    assert "let expanded_expr = value_to_expr(expanded_value, span)?;" in macro
    assert "environment: calling_environment.clone()" in macro

    # The caller environment is not inserted into the transformer's parameter slots.
    # In the current implementation it appears only as function input and as the
    # environment for post-expansion tail evaluation.
    assert macro.count("calling_environment") == 2
    assert "slots.push(calling_environment" not in macro


def main() -> None:
    source_classify_current_transformer()

    protocols = all_protocols()
    signatures = {bits: signature(protocol) for bits, protocol in protocols.items()}

    # Each protocol corner is observably distinguishable by the three probes.
    assert len(protocols) == 8
    assert len(set(signatures.values())) == 8, signatures

    # Axis A is independent: change only operand mode.
    for env, reeval in product((0, 1), repeat=2):
        a = protocols[f"0{env}{reeval}"]
        b = protocols[f"1{env}{reeval}"]
        assert a.env == b.env and a.result == b.result
        assert raw_operand_probe(a) != raw_operand_probe(b)
        assert caller_env_probe(a) == caller_env_probe(b)
        assert result_protocol_probe(a) == result_protocol_probe(b)

    # Axis B is independent: change only caller-environment availability.
    for raw, reeval in product((0, 1), repeat=2):
        a = protocols[f"{raw}0{reeval}"]
        b = protocols[f"{raw}1{reeval}"]
        assert a.operand == b.operand and a.result == b.result
        assert caller_env_probe(a) != caller_env_probe(b)
        assert raw_operand_probe(a) == raw_operand_probe(b)
        assert result_protocol_probe(a) == result_protocol_probe(b)

    # Axis C is independent: change only direct-value vs form-re-eval result.
    for raw, env in product((0, 1), repeat=2):
        a = protocols[f"{raw}{env}0"]
        b = protocols[f"{raw}{env}1"]
        assert a.operand == b.operand and a.env == b.env
        assert result_protocol_probe(a) != result_protocol_probe(b)
        assert raw_operand_probe(a) == raw_operand_probe(b)
        assert caller_env_probe(a) == caller_env_probe(b)

    # Historical FEXPR/FSUBR and current transformer share only the raw axis.
    assert HISTORICAL_FEXPR.operand == CURRENT_TRANSFORMER.operand == OperandMode.RAW
    assert HISTORICAL_FEXPR.env != CURRENT_TRANSFORMER.env
    assert HISTORICAL_FEXPR.result != CURRENT_TRANSFORMER.result

    print("FEXPR-PROTOCOL-CUBE=PASS")
    print("DOMAIN=Core-post-D4-call-protocol")
    print("RELATION=Core-only")
    print("AXIS-A=operand-mode:eager/raw")
    print("AXIS-B=caller-context:none/explicit")
    print("AXIS-C=result-protocol:value/form-reeval")
    print("CUBE-CORNERS=8")
    print("DISTINCT-SIGNATURES=8")
    print("HISTORICAL-FEXPR=raw+explicit-caller-env+direct-value")
    print("CURRENT-TRANSFORMER=raw+no-direct-caller-env+form-reeval")
    print("FEXPR-FSUBR=RAW+ENV-TWO-CAPABILITIES")
    print("TRANSFORMER-RELATION=ORTHOGONAL")
    print("SHARED-PROVED-AXIS=raw-operands")
    print("NON-CONCLUSION=no-width-assigned")
    print("NON-CONCLUSION=no-coordinate-allocated")
    print("NON-CONCLUSION=historical-property-tags-are-not-authority")


if __name__ == "__main__":
    main()
