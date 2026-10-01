#!/usr/bin/env python3
"""#1964: typed equivalence guard for domain-graph research.

Research-only. Three claims must remain distinct:

    implementation equality
    observational equality on a declared domain
    semantic identity

Only proven semantic identity permits graph-node quotient.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/research/1962-equivalence-evidence.tsv"
TRI = {"yes", "no", "unknown"}


@dataclass(frozen=True)
class Relation:
    left: str
    right: str
    implementation_equal: str
    observational_equal: str
    observational_domain: str
    semantic_identity: str
    evidence: str
    note: str

    @property
    def may_share_executable_path(self) -> bool:
        return self.implementation_equal == "yes"

    @property
    def may_quotient_semantic_nodes(self) -> bool:
        return self.semantic_identity == "yes"


def read_relations() -> list[Relation]:
    with EVIDENCE.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))

    out: list[Relation] = []
    for row in rows:
        for field in ("implementation_equal", "observational_equal", "semantic_identity"):
            assert row[field] in TRI, (field, row[field])

        if row["observational_equal"] == "yes":
            assert row["observational_domain"], row

        out.append(Relation(**row))
    return out


def main() -> None:
    relations = read_relations()

    print(
        "left\tright\timpl-equal\tobservational-equal\tobservational-domain\t"
        "semantic-identity\tshare-path\tquotient"
    )
    for rel in relations:
        print(
            f"{rel.left}\t{rel.right}\t{rel.implementation_equal}\t"
            f"{rel.observational_equal}\t{rel.observational_domain or '-'}\t"
            f"{rel.semantic_identity}\t{int(rel.may_share_executable_path)}\t"
            f"{int(rel.may_quotient_semantic_nodes)}"
        )

        # Core law: no weaker relation silently upgrades to semantic identity.
        if rel.semantic_identity != "yes":
            assert not rel.may_quotient_semantic_nodes

    by_pair = {(r.left, r.right): r for r in relations}

    second_cadr = by_pair[("second", "cadr")]
    assert second_cadr.may_share_executable_path
    assert second_cadr.observational_domain == "proper-list"
    assert second_cadr.semantic_identity == "no"
    assert not second_cadr.may_quotient_semantic_nodes

    fourth_cadddr = by_pair[("fourth", "cadddr")]
    assert fourth_cadddr.may_share_executable_path
    assert fourth_cadddr.semantic_identity == "unknown"
    assert not fourth_cadddr.may_quotient_semantic_nodes

    pair_list = by_pair[("pair", "list")]
    assert pair_list.implementation_equal == "no"
    assert pair_list.observational_domain == "exactly-two-arguments"
    assert pair_list.semantic_identity == "no"
    assert not pair_list.may_quotient_semantic_nodes

    print(
        "\nRESULT: evidence is typed and corpus-driven; "
        "path sharing remains independent from semantic quotient."
    )


if __name__ == "__main__":
    main()
