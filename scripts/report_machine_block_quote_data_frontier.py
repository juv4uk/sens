#!/usr/bin/env python3
"""Read-only, fail-closed historical QUOTE-data blocker census.

Research witness ONLY. No conversion, D7 semantic admission, new D10 slots,
physical T5 claim, or changes to the source. The historical observable
fixture is inspected as Python AST, never executed by this checker.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "lib/machine/block.lisp"
ORACLE = ROOT / "tests/test_machine_block_historical_oracle.py"
TEXT7 = ROOT / "crates/sens/src/text7_projection_generated.rs"
SOURCE_BLOB = "200201b741787c4e144ad4194848acf51d7b439e"
CASES = (
    "empty", "one_nested", "append", "concat", "forms", "identity",
    "append_empty", "concat_left_empty", "concat_right_empty",
)
# These are SOURCE/OBSERVABLE atoms. They are not new D7 identities/codes.
EXPECTED_ATOMS = ("mov", "r1", "r2", "branch", "L1", "ret", "label", "L2", "nop")


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def extract_historical_expected(text: str) -> dict:
    tree = ast.parse(text, filename="test_machine_block_historical_oracle.py")
    matches = [
        statement.value
        for statement in tree.body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and statement.targets[0].id == "EXPECTED"
    ]
    if len(matches) != 1:
        raise ValueError("historical oracle requires exactly one EXPECTED")
    expected = ast.literal_eval(matches[0])
    if not isinstance(expected, dict) or tuple(expected.keys()) != CASES:
        raise ValueError("historical oracle nine named cases changed; new owner review required")
    return expected


def symbol_leaves(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [atom for member in value for atom in symbol_leaves(member)]
    raise ValueError("unadmitted historical observable payload (not nested list/symbol)")


def census(original: bytes, oracle: str, projection: str) -> dict:
    if git_blob(original) != SOURCE_BLOB:
        raise ValueError("original historical Git blob drifted; abort")
    cases = extract_historical_expected(oracle)
    by_case = {name: list(dict.fromkeys(symbol_leaves(cases[name]))) for name in CASES}
    unique = tuple(dict.fromkeys(
        symbol for case in CASES for symbol in by_case[case]
    ))
    if set(unique) != set(EXPECTED_ATOMS) or len(unique) != len(EXPECTED_ATOMS):
        raise ValueError("observed historical symbol set changed; no silent new data identity")

    if by_case["empty"]:
        raise ValueError("physical empty case must have no quoted atom-data gap")
    blocked = [name for name in CASES if by_case[name]]
    if len(blocked) != 8:
        raise ValueError("physical historical quote-data frontier must remain explicit 1+8")

    # Projection evidence only: the current generated UPC-7 layouts do NOT
    # encode uppercase ASCII L (case-preserving labels L1/L2).
    # Never lowercase source data: doing so would change historical values.
    uppercase = [x for x in unique if any(c.isascii() and c.isupper() for c in x)]
    if uppercase != ["L1", "L2"]:
        raise ValueError("the uppercase-label witness changed")
    if re.search(r'\("L",\s*Some\(', projection) or re.search(
        r'\("L[12]",\s*Some\(', projection
    ):
        raise ValueError("Text7 uppercase label layout changed; re-review D7 source law")

    return {
        "schema": "machine-block-quote-data-frontier/v1",
        "status": "RESEARCH_BLOCKED_NOT_AN_ADMISSION",
        "original_source": "lib/machine/block.lisp",
        "original_git_blob": SOURCE_BLOB,
        "independent_observer_cases": len(cases),
        "physical_empty_case_current_candidate": "SEPARATELY_TESTED_NOT_ADMITTED",
        "quote_symbol_data_blocked_cases": blocked,
        "unique_historical_quote_atoms": list(unique),
        "quoted_atoms_by_observation": by_case,
        "case_sensitive_nonrepresentable_labels": uppercase,
        "required_owner_laws": [
            "D2-structured QUOTE data carrier distinct from binder/reference Text7",
            "case-preserving D7 value projection for historical uppercase labels",
            "quoted Text7 payload must preserve Value::Symbol, not a generic D2/D7 list",
            "independent Rust physical T5 versus historical nine-case parity",
        ],
        "ratified_d10_residents_added": 0,
        "physical_originals_certified": 0,
        "release_admitted": False,
    }


def main() -> None:
    report = census(
        ORIGINAL.read_bytes(),
        ORACLE.read_text(encoding="utf-8"),
        TEXT7.read_text(encoding="utf-8"),
    )
    print(json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
