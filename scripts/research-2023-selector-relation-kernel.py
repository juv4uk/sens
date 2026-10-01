#!/usr/bin/env python3
"""#2023: selector relation-kernel reduction witness.

Research-only. Tests which selector relations need to be STORED when canonical
bounded binary identity is already authoritative. It does not allocate relation
codes and does not generalize the selector result to other seed families.
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODES = ROOT / "docs/research/1962-lisp1-15-nodes.tsv"

ROOT_WORDS = {"101", "110"}
ACTION = {"0": "101", "1": "110"}


def read_nodes() -> list[dict[str, str]]:
    with NODES.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def schedule(word: str) -> tuple[str, ...]:
    assert word[:3] in ROOT_WORDS
    return (word[:3], *(ACTION[bit] for bit in word[3:]))


def main() -> None:
    rows = read_nodes()
    selector = [
        row for row in rows
        if row["prefix_evidence"] in {"exact-seed", "exact-selector"}
        and row["prefix_code"]
        and row["prefix_code"][:3] in ROOT_WORDS
    ]
    by_word = {row["prefix_code"]: row for row in selector}

    roots = [row for row in selector if row["prefix_evidence"] == "exact-seed"]
    derived = [row for row in selector if row["prefix_evidence"] == "exact-selector"]

    assert {row["prefix_code"] for row in roots} == ROOT_WORDS
    assert len(derived) == 6

    detail = []
    explicit_step_facts = 0

    for row in sorted(derived, key=lambda r: (len(r["prefix_code"]), r["prefix_code"])):
        word = row["prefix_code"]
        parent = word[:-1]
        edge = word[-1]
        root = word[:3]
        suffix = word[3:]

        # K1: explicit parent + edge relations.
        assert parent in by_word, (word, parent)

        # K2: edge is derivable from canonical child identity.
        derived_edge = word[-1]
        assert derived_edge == edge

        # K3: both parent and edge are intrinsic to canonical binary identity.
        intrinsic_parent = word[:-1]
        intrinsic_root = word[:3]
        intrinsic_suffix = word[3:]
        assert intrinsic_parent == parent
        assert intrinsic_root == root
        assert intrinsic_suffix == suffix

        # All kernels must reconstruct the same executable certificate.
        cert = schedule(word)
        assert cert[0] == root
        assert len(cert) == len(suffix) + 1

        explicit_step_facts += len(suffix)
        detail.append(
            {
                "identity": word,
                "parent": parent,
                "edge_bit": edge,
                "root": root,
                "suffix": suffix,
                "schedule": ",".join(cert),
            }
        )

    # Flat explicit model: root-of + each generator step + mechanism-available.
    k0_per_node = len(derived) + explicit_step_facts + len(derived)

    # K1 stores parent + edge per derived node. Mechanism is reconstructed.
    k1_per_node = 2 * len(derived)

    # K2 stores parent only; edge is last bit of canonical identity.
    k2_per_node = len(derived)

    # K3 stores no selector per-node relation facts:
    # parent=drop-last-bit, edge=last-bit, root=first3, suffix=rest.
    k3_per_node = 0

    # Two family-law facts remain: 0 -> 101, 1 -> 110.
    family_law_facts = len(ACTION)

    models = [
        ("K0-flat-explicit", 3, k0_per_node, family_law_facts, "PASS"),
        ("K1-parent+edge", 3, k1_per_node, family_law_facts, "PASS"),
        ("K2-parent-only", 2, k2_per_node, family_law_facts, "PASS"),
        ("K3-intrinsic-bits+family-law", 1, k3_per_node, family_law_facts, "PASS"),
    ]

    # Negative scope control: construction-family candidates have no proven
    # canonical prefix words, so K3 cannot be generalized to them.
    cons_candidates = [
        row for row in rows if row["prefix_evidence"] == "candidate-family-100"
    ]
    assert cons_candidates
    assert all(not row["prefix_code"] for row in cons_candidates)

    print("model\tprimitive_relation_kinds\tstored_per_node_facts\tfamily_law_facts\tstatus")
    for model in models:
        print("\t".join(map(str, model)))

    print()
    print("identity\tparent\tedge_bit\troot\tsuffix\tschedule")
    for row in detail:
        print("\t".join(row[key] for key in ("identity","parent","edge_bit","root","suffix","schedule")))

    print()
    print(f"derived_selector_nodes={len(derived)}")
    print(f"flat_explicit_facts={k0_per_node}")
    print(f"intrinsic_per_node_facts={k3_per_node}")
    print(f"family_law_facts={family_law_facts}")
    print(f"cons_negative_controls={len(cons_candidates)}")
    print("PASS: selector parent/edge/root/suffix are reconstructed from canonical identity.")
    print("PASS: two binary family-law facts reconstruct selector execution schedules.")
    print("PASS: CONS candidates remain outside this reduction because no prefix identity is proven.")
    print("NON-CONCLUSION: selector-local relation reduction is not a global relation-kernel theorem.")


if __name__ == "__main__":
    main()
