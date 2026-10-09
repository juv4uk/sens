#!/usr/bin/env python3
"""#2472 — transformation-footprint audit for Phase-D countermodels.

Research-only archaeology: GO/RETURN evidence comes from an archived,
non-executable Rust research snapshot, never a current semantic test.
The live SETQ input is retained. This classifies transformation footprint,
not current D1-D9 authority or an allocated identity.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTROL = ROOT / "docs" / "archive" / "historical" / "retired-rust-tests" / "post_d4_control_derivation.rs.txt"
SETQ = ROOT / "crates" / "sens" / "tests" / "post_d4_setq_state_passing.rs"


def require(text: str, needle: str, label: str) -> None:
    assert needle in text, f"missing {label}: {needle!r}"


def main() -> None:
    control = CONTROL.read_text(encoding="utf-8")
    setq = SETQ.read_text(encoding="utf-8")

    # GO: all transfer state is carried by a synthetic driver local to the
    # transformed PROG region. No first-class continuation/store protocol is
    # needed merely to express the label machine.
    require(
        control,
        "(00001000 (state remaining acc)",
        "GO finite-state driver signature",
    )
    require(
        control,
        "(post-d4-go-driver",
        "GO recursive state transition",
    )

    # RETURN: the non-local exit witness requires an explicit exit-k to cross
    # nested helper calls. That is stronger than the local GO rewrite.
    require(
        control,
        "(00001000 (mode continue-k exit-k payload)",
        "RETURN helper protocol carrying exit-k",
    )
    require(
        control,
        "(post-d4-return-helper1\n         mode",
        "RETURN call-chain forwarding",
    )
    require(
        control,
        "(00001000 (exit-k)",
        "RETURN program creates explicit exit continuation",
    )

    # SETQ: observers that pre-date the update are explicitly transformed to
    # accept the current store. This changes the observer calling protocol.
    require(
        setq,
        "Pre-existing observers are transformed closures that receive the current",
        "SETQ transformed pre-existing observer statement",
    )
    require(
        setq,
        "(00001000 (location)\n    (00001000 (store)",
        "SETQ observer takes explicit store",
    )
    require(
        setq,
        "(00001000 (observer store)\n    (observer store))",
        "SETQ observer call passes explicit store",
    )

    rows = [
        (
            "GO",
            "LOCAL-REGION-REWRITE",
            "state parameter is confined to synthetic finite-state driver",
            "yes",
        ),
        (
            "RETURN",
            "CALLCHAIN-PROTOCOL-REWRITE",
            "exit-k must be introduced and forwarded across nested calls",
            "no",
        ),
        (
            "SETQ",
            "OBSERVER-PROTOCOL-REWRITE",
            "pre-existing observers are rewritten to accept current store",
            "no",
        ),
    ]

    print("POST-D4 TRANSFORMATION FOOTPRINT: PASS")
    print("operation\tfootprint\toriginal-interface-preserved-locally\tevidence")
    for op, footprint, evidence, local in rows:
        print(f"{op}\t{footprint}\t{local}\t{evidence}")

    print("FACT: GO has a strictly smaller transformation footprint than RETURN/SETQ")
    print("FACT: RETURN witness proves D4 expressibility via explicit CPS")
    print("FACT: SETQ witness proves D4 expressibility via explicit store passing")
    print("NON-CONCLUSION: RETURN=DERIVED-D4")
    print("NON-CONCLUSION: SETQ=DERIVED-D4")
    print("NON-CONCLUSION: any post-D4 address")


if __name__ == "__main__":
    main()
