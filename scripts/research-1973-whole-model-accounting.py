#!/usr/bin/env python3
"""#1973: first whole-model accounting over the bounded #1962/#1972 corpus.

Research-only. This does not allocate identities or change production semantics.
It separates semantic nodes, explicit execution rows, generator actions, and
semantic quotient so that mechanism compression cannot be mistaken for meaning
deletion.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs/research/1972-generator-first-residue.tsv"

FIELDS = (
    "model",
    "semantic_nodes",
    "explicit_execution_rows",
    "generated_paths",
    "generator_action_rules",
    "unresolved_nodes",
    "execution_coverage_nodes",
    "execution_rows_avoided_vs_flat",
    "semantic_identities_eliminated",
    "status",
)


def read_rows() -> list[dict[str, str]]:
    with LEDGER.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def main() -> None:
    rows = read_rows()
    semantic_nodes = len(rows)
    roots = [row for row in rows if row["semantic_class"] == "seed-root"]
    generated = [row for row in rows if row["semantic_class"] == "generated-path"]
    unresolved = [row for row in rows if row["semantic_class"] == "unresolved"]
    proven_residue = [row for row in rows if row["semantic_class"] == "irreducible-residue"]

    assert semantic_nodes == 34
    assert len(roots) == 8
    assert len(generated) == 6
    assert len(unresolved) == 20
    assert not proven_residue

    generated_roots = {row["root"] for row in generated}
    assert generated_roots == {"101", "110"}

    # The proven selector local action uses exactly two suffix actions:
    # append 0 => compose CAR, append 1 => compose CDR.
    selector_action_rules = 2

    models = [
        {
            "model": "flat-explicit-donor",
            "semantic_nodes": semantic_nodes,
            "explicit_execution_rows": semantic_nodes,
            "generated_paths": 0,
            "generator_action_rules": 0,
            "unresolved_nodes": 0,
            "execution_coverage_nodes": semantic_nodes,
            "execution_rows_avoided_vs_flat": 0,
            "semantic_identities_eliminated": 0,
            "status": "complete-donor-not-authority",
        },
        {
            "model": "proven-root-plus-path",
            "semantic_nodes": semantic_nodes,
            "explicit_execution_rows": len(roots),
            "generated_paths": len(generated),
            "generator_action_rules": selector_action_rules,
            "unresolved_nodes": len(unresolved),
            "execution_coverage_nodes": len(roots) + len(generated),
            "execution_rows_avoided_vs_flat": len(generated),
            "semantic_identities_eliminated": 0,
            "status": "incomplete-proven-only",
        },
        {
            "model": "hybrid-keep-unresolved-explicit",
            "semantic_nodes": semantic_nodes,
            "explicit_execution_rows": len(roots) + len(unresolved),
            "generated_paths": len(generated),
            "generator_action_rules": selector_action_rules,
            "unresolved_nodes": len(unresolved),
            "execution_coverage_nodes": semantic_nodes,
            "execution_rows_avoided_vs_flat": len(generated),
            "semantic_identities_eliminated": 0,
            "status": "complete-accounting-bound-no-new-allocation",
        },
    ]

    # Hard safety checks: current evidence deletes mechanism rows, not meanings.
    assert models[2]["explicit_execution_rows"] == 28
    assert models[2]["execution_rows_avoided_vs_flat"] == 6
    assert all(model["semantic_identities_eliminated"] == 0 for model in models)

    writer = csv.DictWriter(
        sys.stdout, fieldnames=FIELDS, delimiter="\t", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(models)

    print(
        "# RESULT: proven selector generation trades 6 descendant execution rows "
        "for 2 suffix-action rules while deleting 0 semantic identities.",
        file=sys.stderr,
    )
    print(
        "# NOTE: the 20 unresolved nodes remain explicit only as a conservative "
        "accounting bound; this does not prove irreducible residue or authorize allocation.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
