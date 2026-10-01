#!/usr/bin/env python3
"""#1972: conservative generator-first residue ledger.

Research-only. Absence of a known generator is NOT evidence of irreducibility.
This script allocates nothing and changes no production semantic authority.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODES = ROOT / "docs/research/1962-lisp1-15-nodes.tsv"
EQUIV = ROOT / "docs/research/1962-equivalence-evidence.tsv"
CONS_NEGATIVE = ROOT / "scripts/research-1965-cons-family.py"

FIELDS = (
    "node", "era", "semantic_class", "root", "canonical_path",
    "path_shared_with", "equivalence_evidence", "generator_evidence",
    "residue_reason", "status",
)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def equivalence_index() -> dict[str, list[dict[str, str]]]:
    index: dict[str, list[dict[str, str]]] = {}
    for row in read_tsv(EQUIV):
        for key in ("left", "right"):
            index.setdefault(row[key], []).append(row)
    return index


def sharing(node: str, index: dict[str, list[dict[str, str]]]) -> tuple[str, str]:
    peers, evidence = [], []
    for row in index.get(node, []):
        if row["implementation_equal"] != "yes":
            continue
        peer = row["right"] if row["left"] == node else row["left"]
        peers.append(peer)
        evidence.append(
            f"implementation-equal; observational={row['observational_equal']}"
            f"@{row['observational_domain'] or '-'}; semantic={row['semantic_identity']}"
        )
    return ",".join(sorted(set(peers))), " | ".join(evidence)


def classify(row: dict[str, str], eq_index: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    node = row["id"]
    evidence = row["prefix_evidence"]
    path = row["prefix_code"]
    shared_with, eq_evidence = sharing(node, eq_index)

    if evidence == "exact-seed":
        cls, root, gen, reason, status = (
            "seed-root", row["seed3_code"], "exact-seed", "-", "proven"
        )
    elif evidence == "exact-selector":
        cls, root, gen, reason, status = (
            "generated-path", path[:3], "exact-selector", "-", "proven"
        )
    else:
        cls = "unresolved"
        root = evidence.removeprefix("candidate-family-") if evidence.startswith("candidate-family-") else "-"
        gen = evidence or "-"
        if root == "100" and CONS_NEGATIVE.exists():
            gen += "; bounded-negative-cons-family"
            reason = (
                "CONS strong generator not proven; negative family evidence "
                "does not prove irreducibility"
            )
            status = "unresolved-not-strong-semantic"
        elif evidence == "unresolved-multiparent":
            reason = "multiple typed parents; no canonical generator/irreducibility proof"
            status = "unresolved"
        else:
            reason = "no proven generator and no irreducibility proof"
            status = "unresolved"

    return {
        "node": node,
        "era": row["era"],
        "semantic_class": cls,
        "root": root,
        "canonical_path": path or "-",
        "path_shared_with": shared_with or "-",
        "equivalence_evidence": eq_evidence or "-",
        "generator_evidence": gen,
        "residue_reason": reason,
        "status": status,
    }


def main() -> None:
    eq_index = equivalence_index()
    rows = [classify(row, eq_index) for row in read_tsv(NODES)]
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["semantic_class"]] = counts.get(row["semantic_class"], 0) + 1

    assert counts.get("seed-root") == 8
    assert counts.get("generated-path", 0) >= 6
    assert counts.get("irreducible-residue", 0) == 0
    assert counts.get("unresolved", 0) > 0

    cadr = next(row for row in rows if row["node"] == "cadr")
    assert "second" in cadr["path_shared_with"]
    assert "semantic=no" in cadr["equivalence_evidence"]

    for node in ("list", "append"):
        row = next(item for item in rows if item["node"] == node)
        assert row["semantic_class"] == "unresolved"
        assert "does not prove irreducibility" in row["residue_reason"]

    writer = csv.DictWriter(sys.stdout, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)

    print(
        "# summary " + " ".join(f"{k}={counts[k]}" for k in sorted(counts)),
        file=sys.stderr,
    )
    print(
        "# PASS: zero proven irreducible residue at this stage; unresolved is not allocation.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
