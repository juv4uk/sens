#!/usr/bin/env python3
"""#2507 — SENS-side opaque-ID Panini donor invariance consumer.

Consumes pinned donor graph artifacts from juv4uk/shiva-sutras without importing
its executable checker. The SENS witness replays the bounded adhikara law
independently and keeps D14 coordinate allocation empty.

Research only.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "benchmarks" / "d14-panini-donor-invariance" / "donor-lock.json"


@dataclass(frozen=True, order=True)
class Edge:
    src: str
    dst: str
    kind: str
    label: str


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def load_lock() -> dict[str, Any]:
    data = json.loads(LOCK.read_text(encoding="utf-8"))
    assert data["schema"] == "d14-panini-donor-lock/v1"
    assert data["authority"] == "research-only-donor-pin"
    assert data["d14_allocation"] == "NONE"
    return data


def verify_artifacts(upstream_root: Path, lock: dict[str, Any]) -> None:
    for rel, expected in lock["artifacts"].items():
        path = upstream_root / rel
        if not path.is_file():
            raise AssertionError(f"missing donor artifact: {rel}")
        actual = git_blob_sha1(path.read_bytes())
        if actual != expected:
            raise AssertionError(f"donor artifact drift {rel}: {actual} != {expected}")


def read_edges(path: Path) -> tuple[Edge, ...]:
    rows: list[Edge] = []
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        if set(reader.fieldnames or ()) != {"src", "dst", "kind", "label"}:
            raise AssertionError("edge schema drift")
        for row in reader:
            rows.append(Edge(row["src"], row["dst"], row["kind"], row["label"]))
    assert rows
    return tuple(rows)


def parse_ref(ref: str) -> tuple[int, int, int]:
    if ref.startswith("PS_"):
        ref = ref[3:].replace(",", ".")
    parts = ref.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise ValueError(ref)
    return tuple(map(int, parts))


def anchor_index(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    assert payload["authority"] == "textual-edition-anchor-only"
    assert payload["no_d14_allocation"] is True
    assert payload["relation_promotions"] == 0

    out: dict[str, dict[str, Any]] = {}
    for row in payload["anchors"]:
        assert row["relation_authority"] == "none"
        node = row["node_id"]
        assert node not in out
        out[node] = copy.deepcopy(row)
    return out


def derive_scope_children(
    anchors: dict[str, dict[str, Any]],
    relation: dict[str, Any],
) -> tuple[str, ...]:
    assert relation["authority"] == "commentarial-supported"
    assert relation["relation_kind"] == "adhikara"
    assert relation["no_d14_allocation"] is True
    assert relation["primary_relation_promotions"] == 0

    anchor = relation["anchor_node"]
    assert anchor in anchors

    start = parse_ref(relation["scope_claim"]["start"])
    end = parse_ref(relation["scope_claim"]["through"])
    assert parse_ref(anchors[anchor]["canonical_ref"]) == start

    children = []
    for node, row in anchors.items():
        pos = parse_ref(row["canonical_ref"])
        if pos[:2] == start[:2] and start < pos <= end:
            children.append(node)
    return tuple(sorted(children, key=lambda node: parse_ref(anchors[node]["canonical_ref"])))


def graph_adhikara_query(edges: tuple[Edge, ...], anchor: str) -> tuple[str, ...]:
    return tuple(sorted(edge.src for edge in edges if edge.kind == "adhikara" and edge.dst == anchor))


def rename_anchors(
    anchors: dict[str, dict[str, Any]],
    relation: dict[str, Any],
    mapping: dict[str, str],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    if set(mapping) != set(anchors) or set(mapping.values()) != set(anchors):
        raise AssertionError("mapping must be a full bijection")

    renamed = {}
    for old, row in anchors.items():
        new = mapping[old]
        copied = copy.deepcopy(row)
        copied["node_id"] = new
        renamed[new] = copied

    rel = copy.deepcopy(relation)
    rel["anchor_node"] = mapping[relation["anchor_node"]]
    return renamed, rel


def rename_edges(edges: tuple[Edge, ...], mapping: dict[str, str]) -> tuple[Edge, ...]:
    return tuple(
        Edge(mapping[e.src], mapping[e.dst], e.kind, e.label)
        for e in edges
    )


def deterministic_mapping(nodes: tuple[str, ...], seed: int) -> dict[str, str]:
    shuffled = list(nodes)
    random.Random(seed).shuffle(shuffled)
    return dict(zip(nodes, shuffled, strict=True))


def codebook(nodes: tuple[str, ...], seed: int) -> dict[str, str]:
    """Arbitrary 14-bit projection used only as a non-authoritative attack."""
    values = list(range(len(nodes)))
    random.Random(seed).shuffle(values)
    return {
        node: format(value, "014b")
        for node, value in zip(nodes, values, strict=True)
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--upstream-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--trials", type=int, default=64)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    lock = load_lock()
    upstream = args.upstream_root.resolve()
    verify_artifacts(upstream, lock)

    edges_path = upstream / "prototype/sutra_graph/curated_controls_edges.tsv"
    anchors_path = upstream / "prototype/sutra_graph/primary_text_anchors.json"
    relation_path = upstream / "prototype/sutra_graph/adhikara_6184_relation_evidence.json"

    edges = read_edges(edges_path)
    anchors_payload = json.loads(anchors_path.read_text(encoding="utf-8"))
    relation = json.loads(relation_path.read_text(encoding="utf-8"))
    anchors = anchor_index(anchors_payload)

    assert relation["authority"] == lock["relation_authority_ceiling"]
    assert relation["anchor_node"] == "6.1.84"

    anchor = relation["anchor_node"]
    direct = graph_adhikara_query(edges, anchor)
    derived = derive_scope_children(anchors, relation)

    assert derived == direct
    assert len(derived) == 5

    leave_one_out = 0
    direct_deletion_sensitive = 0
    target_edges = tuple(e for e in edges if e.kind == "adhikara" and e.dst == anchor)
    for victim in target_edges:
        reduced = tuple(e for e in edges if e != victim)
        reduced_direct = graph_adhikara_query(reduced, anchor)
        assert victim.src not in reduced_direct
        direct_deletion_sensitive += 1

        reconstructed = derive_scope_children(anchors, relation)
        assert victim.src in reconstructed
        leave_one_out += 1

    wrong_kind_edges = tuple(
        Edge(e.src, e.dst, "blocks", e.label) if e in target_edges[:1] else e
        for e in edges
    )
    assert graph_adhikara_query(wrong_kind_edges, anchor) != direct

    nodes = tuple(sorted(anchors))
    lawful = 0
    broken = 0
    nontrivial = 0
    reverse_checks = 0
    for seed in range(args.trials):
        mapping = deterministic_mapping(nodes, seed)
        reverse = {v: k for k, v in mapping.items()}
        if any(mapping[n] != n for n in nodes):
            nontrivial += 1

        ra, rr = rename_anchors(anchors, relation, mapping)
        re = rename_edges(edges, mapping)

        rderived = derive_scope_children(ra, rr)
        rdirect = graph_adhikara_query(re, rr["anchor_node"])
        assert rderived == rdirect

        recovered = tuple(reverse[node] for node in rderived)
        assert recovered == direct
        reverse_checks += 1
        lawful += 1

        br = copy.deepcopy(relation)
        br["anchor_node"] = mapping[anchor]
        try:
            bderived = derive_scope_children(anchors, br)
        except (AssertionError, ValueError):
            broken += 1
        else:
            if bderived != derived:
                broken += 1

    assert lawful == args.trials
    assert reverse_checks == args.trials
    assert nontrivial > 0
    assert broken > 0

    shortened = copy.deepcopy(relation)
    shortened["scope_claim"]["through"] = "6.1.96"
    shortened_children = derive_scope_children(anchors, shortened)
    assert "6.1.97" not in shortened_children
    assert shortened_children != derived

    cb_a = codebook(nodes, 1)
    cb_b = codebook(nodes, 2)
    assert cb_a != cb_b
    encoded_a = tuple(cb_a[node] for node in derived)
    encoded_b = tuple(cb_b[node] for node in derived)
    assert encoded_a != encoded_b
    assert derived == direct

    result = {
        "schema": "sens-d14-panini-donor-invariance/v1",
        "authority": "research-only",
        "donor": {
            "repository": lock["repository"],
            "revision": lock["revision"],
            "artifacts": lock["artifacts"],
            "relation_authority": relation["authority"],
        },
        "real_graph": {
            "nodes": len(anchors),
            "edges": len(edges),
            "adhikara_children": list(derived),
            "adhikara_child_count": len(derived),
        },
        "held_out": {
            "leave_one_out_reconstructed": leave_one_out,
            "direct_query_deletion_sensitive": direct_deletion_sensitive,
        },
        "relabel": {
            "trials": args.trials,
            "lawful_passes": lawful,
            "broken_transport_changes_or_fails": broken,
            "nontrivial_permutations": nontrivial,
        },
        "falsifiers": {
            "wrong_edge_kind": "REJECTED",
            "shortened_scope": "CHANGES-DERIVATION",
            "untransported_rename": "FAILS-OR-CHANGES",
        },
        "d14": {
            "forced_coordinates": 0,
            "allocation": "NONE",
            "arbitrary_codebook_a": encoded_a,
            "arbitrary_codebook_b": encoded_b,
            "codebooks_semantic_authority": False,
        },
        "non_conclusions": [
            "repo-curated/commentarial-supported graph is not full Panini grammar authority",
            "textual sutra numbers are provenance, not D14 coordinates",
            "successful held-out reconstruction does not allocate any D14 code",
            "D7 local ordinals do not imply graph edges",
        ],
    }
    (args.out / "result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# D14 opaque donor invariance — #2507",
        "",
        f"Pinned donor revision: {lock['revision']}",
        f"Real graph fixture: **{len(anchors)} nodes / {len(edges)} edges**",
        f"Bounded adhikara children: **{len(derived)}**",
        f"Leave-one-out reconstructed: **{leave_one_out}/{len(target_edges)}**",
        f"Direct-query deletion sensitivity: **{direct_deletion_sensitive}/{len(target_edges)}**",
        f"Lawful opaque-ID relabel: **{lawful}/{args.trials}**",
        f"Broken transport changes/fails: **{broken}** trials",
        "",
        "Wrong-edge-kind and shortened-scope controls are rejected.",
        "Two arbitrary 14-bit codebooks produce different bit labels but the same graph-law result.",
        "",
        "**D14 forced coordinates = 0. Allocation = NONE.**",
        "",
        "Interpretation: current evidence supports graph-law invariance under opaque IDs;",
        "it does not support numbering the graph into D14 yet.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
