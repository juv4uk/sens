#!/usr/bin/env python3
"""Derive a complete #4086 silicon census from existing machine projections.

This tool is downstream only:
- admitted-iclass-index.lisp owns the pinned #175 evidence pair inventory;
- admission-iclass-projection.lisp owns the current structured-admission subset;
- the optional real-silicon ledger owns physical execution observations.

The census classifies every pinned (extension, ICLASS) pair without creating a
second ISA/admission authority.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "lib/machine/encoding/admitted-iclass-index.lisp"
PROJECTION = ROOT / "lib/machine/encoding/admission-iclass-projection.lisp"

# The generated pinned index is a data projection, not executable Lisp.
# Current rows use the exact D8 record head; archived snapshots used the
# explicit pair tag. Accept both data-record envelopes without treating
# either head as callable semantic authority.
PAIR_RE = re.compile(r'^\s*\((?:pair|00101110)\s+([^\s()]+)\s+"([^"]+)"\)\s*$')
PARTIAL_RE = re.compile(
    r'^\s*\(partial\s+([^\s()]+)\s+"([^"]+)"\s+\(heads\s+([^)]*)\)\)\s*$'
)
PARTIAL_COUNT_RE = re.compile(r'^\s*\(partial-pair-count\s+#b([01]+)\)\s*$')

# Admitted forms intentionally not physically executed by the generic owner
# sweep until they have a dedicated bounded side-effect/control-flow witness.
DECODE_ONLY_ICLASSES = {
    "CALL_NEAR",
    "CLD",
    "RDTSC",
    "REP_MOVSB",
    "REP_MOVSQ",
    "REP_STOSB",
    "REP_STOSQ",
    "STD",
}

PHYSICAL_PRECEDENCE = {
    "platform-gated": 1,
    "execute-safe": 2,
}


class CensusError(RuntimeError):
    pass


def load_pairs(path: Path = INDEX) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = PAIR_RE.match(line)
        if match:
            pairs.append((match.group(1), match.group(2)))
    if len(pairs) != 1176:
        raise CensusError(f"expected 1176 pinned evidence pairs, found {len(pairs)}")
    if len(set(pairs)) != len(pairs):
        raise CensusError("pinned evidence pair inventory contains duplicates")
    return pairs


def load_projection(path: Path = PROJECTION) -> tuple[dict[tuple[str, str], list[str]], dict[str, tuple[str, str]]]:
    pairs: dict[tuple[str, str], list[str]] = {}
    head_to_pair: dict[str, tuple[str, str]] = {}
    declared_pair_count: int | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        count_match = PARTIAL_COUNT_RE.match(line)
        if count_match:
            if declared_pair_count is not None:
                raise CensusError("duplicate partial-pair-count in admission projection")
            declared_pair_count = int(count_match.group(1), 2)
            continue

        match = PARTIAL_RE.match(line)
        if not match:
            continue
        pair = (match.group(1), match.group(2))
        heads = match.group(3).split()
        if pair in pairs:
            raise CensusError(f"duplicate partial projection row: {pair}")
        pairs[pair] = heads
        for head in heads:
            previous = head_to_pair.get(head)
            if previous is not None and previous != pair:
                raise CensusError(f"admission head {head!r} maps to both {previous} and {pair}")
            head_to_pair[head] = pair

    if declared_pair_count is None:
        raise CensusError("admission projection missing partial-pair-count")
    if len(pairs) != declared_pair_count:
        raise CensusError(
            f"admission projection declares {declared_pair_count} partial pairs, found {len(pairs)}"
        )
    return pairs, head_to_pair

def load_ledger(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CensusError(f"cannot read physical ledger {path}: {exc}") from exc
    if not isinstance(value, dict) or not isinstance(value.get("rows"), list):
        raise CensusError("physical ledger must contain object field rows[]")
    return value


def expression_heads(expression: str, known_heads: dict[str, tuple[str, str]]) -> set[str]:
    found: set[str] = set()
    for head in known_heads:
        if re.search(r"\(" + re.escape(head) + r"(?=[\s)])", expression):
            found.add(head)
    return found


def physical_pair_evidence(
    ledger: dict[str, Any] | None,
    head_to_pair: dict[str, tuple[str, str]],
) -> dict[tuple[str, str], dict[str, Any]]:
    if ledger is None:
        return {}

    evidence: dict[tuple[str, str], dict[str, Any]] = {}
    for index, raw in enumerate(ledger["rows"]):
        if not isinstance(raw, dict):
            raise CensusError(f"physical ledger row {index} must be an object")
        classification = raw.get("classification")
        if classification not in PHYSICAL_PRECEDENCE:
            continue
        expression = raw.get("expression")
        row_id = raw.get("id", f"row-{index}")
        if not isinstance(expression, str):
            raise CensusError(f"physical ledger row {row_id!r} missing expression")

        for head in expression_heads(expression, head_to_pair):
            pair = head_to_pair[head]
            slot = evidence.setdefault(
                pair,
                {
                    "classification": classification,
                    "witness_ids": [],
                    "heads": set(),
                },
            )
            if PHYSICAL_PRECEDENCE[classification] > PHYSICAL_PRECEDENCE[slot["classification"]]:
                slot["classification"] = classification
            slot["witness_ids"].append(str(row_id))
            slot["heads"].add(head)

    for slot in evidence.values():
        slot["witness_ids"] = sorted(set(slot["witness_ids"]))
        slot["heads"] = sorted(slot["heads"])
    return evidence


def build_census(
    evidence_pairs: list[tuple[str, str]],
    admitted_pairs: dict[tuple[str, str], list[str]],
    physical: dict[tuple[str, str], dict[str, Any]],
    ledger: dict[str, Any] | None,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []

    for extension, iclass in evidence_pairs:
        pair = (extension, iclass)
        admission_heads = admitted_pairs.get(pair, [])
        physical_slot = physical.get(pair)

        if not admission_heads:
            classification = "unsupported-current-grammar"
        elif physical_slot is not None:
            classification = physical_slot["classification"]
        elif iclass in DECODE_ONLY_ICLASSES:
            classification = "decode-only-safety"
        else:
            classification = "unknown"

        row: dict[str, Any] = {
            "id": f"{extension}:{iclass}",
            "extension": extension,
            "iclass": iclass,
            "classification": classification,
            "admission_heads": admission_heads,
        }

        if physical_slot is not None:
            row["physical_witness_ids"] = physical_slot["witness_ids"]
            row["physical_heads"] = physical_slot["heads"]
        if classification == "decode-only-safety":
            row["reason"] = "admitted-but-withheld-from-generic-silicon-execution"
        if classification == "unsupported-current-grammar":
            row["reason"] = "pinned-evidence-pair-has-no-current-structured-admission"
        if classification == "unknown":
            row["blocking_issue"] = "#4086"

        rows.append(row)

    return {
        "schema": "sens-real-silicon-census-v1",
        "source_evidence": "lib/machine/encoding/admitted-iclass-index.lisp",
        "source_admission": "lib/machine/encoding/admission-iclass-projection.lisp",
        "source_physical_ledger_schema": ledger.get("schema") if ledger else None,
        "sens_commit": ledger.get("sens_commit", "derived-without-physical-ledger") if ledger else "derived-without-physical-ledger",
        "cpu_model": ledger.get("cpu_model", "not-observed") if ledger else "not-observed",
        "target": ledger.get("target", "x86_64-current-admission-census") if ledger else "x86_64-current-admission-census",
        "census_complete": True,
        "census_total": len(rows),
        "rows": rows,
    }


def self_test() -> None:
    # Regression: the live generated index uses \`(00101110 EXT "ICLASS")\`.
    # Retain compatibility with archived \`(pair EXT "ICLASS")\` snapshots too.
    for line in (
        '(00101110 X86-BASE "ADD")',
        '(pair X86-BASE "ADD")',
    ):
        match = PAIR_RE.match(line)
        assert match is not None, f"index row must parse: {line}"
        assert match.groups() == ("X86-BASE", "ADD")

    evidence = [("X86-BASE", "ADD"), ("X86-BASE", "CALL_NEAR"), ("AVX", "VADDPS")]
    admitted = {
        ("X86-BASE", "ADD"): ["add-r64-r64"],
        ("X86-BASE", "CALL_NEAR"): ["call-rel32"],
    }
    head_to_pair = {
        "add-r64-r64": ("X86-BASE", "ADD"),
        "call-rel32": ("X86-BASE", "CALL_NEAR"),
    }
    ledger = {
        "schema": "test-ledger",
        "sens_commit": "deadbeef",
        "cpu_model": "test-cpu",
        "target": "test-target",
        "rows": [
            {
                "id": "add",
                "expression": "(x (add-r64-r64 rax rcx) (ret))",
                "classification": "execute-safe",
            }
        ],
    }
    physical = physical_pair_evidence(ledger, head_to_pair)
    census = build_census(evidence, admitted, physical, ledger)
    by_id = {row["id"]: row for row in census["rows"]}
    assert census["census_complete"] is True
    assert census["census_total"] == 3
    assert by_id["X86-BASE:ADD"]["classification"] == "execute-safe"
    assert by_id["X86-BASE:CALL_NEAR"]["classification"] == "decode-only-safety"
    assert by_id["AVX:VADDPS"]["classification"] == "unsupported-current-grammar"
    print("silicon-census-self-test-ok")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    try:
        evidence_pairs = load_pairs()
        admitted_pairs, head_to_pair = load_projection()
        ledger = load_ledger(args.ledger)
        physical = physical_pair_evidence(ledger, head_to_pair)
        census = build_census(evidence_pairs, admitted_pairs, physical, ledger)
    except CensusError as exc:
        print(f"silicon-census-error: {exc}", file=sys.stderr)
        return 1

    payload = json.dumps(census, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        sys.stdout.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main()))
PARTIAL_RE = re.compile(
    r'^\s*\(partial\s+([^\s()]+)\s+"([^"]+)"\s+\(heads\s+([^)]*)\)\)\s*$'
)
PARTIAL_COUNT_RE = re.compile(r'^\s*\(partial-pair-count\s+#b([01]+)\)\s*$')

# Admitted forms intentionally not physically executed by the generic owner
# sweep until they have a dedicated bounded side-effect/control-flow witness.
DECODE_ONLY_ICLASSES = {
    "CALL_NEAR",
    "CLD",
    "RDTSC",
    "REP_MOVSB",
    "REP_MOVSQ",
    "REP_STOSB",
    "REP_STOSQ",
    "STD",
}

PHYSICAL_PRECEDENCE = {
    "platform-gated": 1,
    "execute-safe": 2,
}


class CensusError(RuntimeError):
    pass


def load_pairs(path: Path = INDEX) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = PAIR_RE.match(line)
        if match:
            pairs.append((match.group(1), match.group(2)))
    if len(pairs) != 1176:
        raise CensusError(f"expected 1176 pinned evidence pairs, found {len(pairs)}")
    if len(set(pairs)) != len(pairs):
        raise CensusError("pinned evidence pair inventory contains duplicates")
    return pairs


def load_projection(path: Path = PROJECTION) -> tuple[dict[tuple[str, str], list[str]], dict[str, tuple[str, str]]]:
    pairs: dict[tuple[str, str], list[str]] = {}