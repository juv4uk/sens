#!/usr/bin/env python3
"""#1973 current selector closure/law-economics curve.

This harness measures the *economic shape* of one already-admitted semantic
family. It never infers or ratifies semantics from compression.

Source of truth:
  knowledge/d1-d6-foundation.json  (#3393 D1-D6 foundation within Contract 11.6)

Seed:
  D3:100 CAR
  D3:011 CDR

Current concrete lifts:
  D3 -> D4 selector children
  D4 -> D5 selector children
  D5 -> D6 selector children

For each allowed maximum width, compute closure to fixed point, validate every
generated child against current authority, and report structural/serialization
costs. JSON byte ratios are representation-specific descriptive metrics, not
semantic scores.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FOUNDATION = ROOT / "knowledge/d1-d6-foundation.json"

SEEDS = (("100", "CAR"), ("011", "CDR"))
LIFT_EVIDENCE = {
    (3, 4): ["#2055", "#3202", "#3272"],
    (4, 5): ["#3305", "#3331"],
    (5, 6): ["#3321", "#3393"],
}


def canonical_bytes(obj) -> int:
    data = json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return len(data)


def selector_name(coord: str) -> str:
    root = coord[:3]
    if root == "100":
        letters = ["A"]
    elif root == "011":
        letters = ["D"]
    else:
        raise ValueError(f"not a selector root: {coord}")
    for bit in coord[3:]:
        letters.append("A" if bit == "0" else "D")
    return "C" + "".join(letters) + "R"


def load_foundation() -> dict:
    data = json.loads(FOUNDATION.read_text(encoding="utf-8"))
    assert data["schema"] == "d1-d6-foundation-ratification/v1"
    assert data["status"] == "owner-ratified"
    assert data["authority"] == "#3393"
    assert data["domains"]["D3"]["residents"]["100"] == "CAR"
    assert data["domains"]["D3"]["residents"]["011"] == "CDR"
    return data


def expand_to_fixed_point(foundation: dict, max_width: int):
    closure: dict[tuple[int, str], str] = {
        (3, coord): name for coord, name in SEEDS
    }
    rounds = 0

    while True:
        pending: dict[tuple[int, str], str] = {}
        for (width, coord), _name in sorted(closure.items()):
            if width >= max_width:
                continue
            next_width = width + 1
            if next_width > max_width:
                continue

            residents = foundation["domains"][f"D{next_width}"]["residents"]
            for bit in ("0", "1"):
                child = coord + bit
                expected = selector_name(child)
                actual = residents.get(child)
                if actual != expected:
                    raise AssertionError(
                        f"D{next_width}:{child}: generated selector expects "
                        f"{expected}, authority has {actual!r}"
                    )
                key = (next_width, child)
                if key not in closure:
                    pending[key] = actual

        if not pending:
            break
        closure.update(pending)
        rounds += 1

    return closure, rounds


def law_description(max_width: int):
    if max_width <= 3:
        return {}
    lifts = []
    for width in range(3, max_width):
        evidence = LIFT_EVIDENCE[(width, width + 1)]
        lifts.append(
            {
                "from_width": width,
                "to_width": width + 1,
                "family": "selector",
                "coordinate_child": "parent || b",
                "semantic_child": {"0": "compose CAR", "1": "compose CDR"},
                "evidence": evidence,
            }
        )
    return {
        "generator": {
            "family": "selector",
            "roots": {"100": "CAR", "011": "CDR"},
            "suffix": {"0": "compose CAR", "1": "compose CDR"},
        },
        "admitted_lifts": lifts,
    }


def flat_projection(closure: dict[tuple[int, str], str]):
    return [
        {"width": width, "coordinate": coord, "resident": name}
        for (width, coord), name in sorted(closure.items())
    ]


def git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def compute_rows():
    foundation = load_foundation()
    seed_projection = [
        {"width": 3, "coordinate": coord, "resident": name}
        for coord, name in SEEDS
    ]
    seed_json_bytes = canonical_bytes(seed_projection)
    foundation_sha256 = hashlib.sha256(FOUNDATION.read_bytes()).hexdigest()

    rows = []
    previous_closure_count = None
    previous_law_bytes = 0

    for max_width in range(3, 7):
        closure, rounds = expand_to_fixed_point(foundation, max_width)
        flat = flat_projection(closure)
        laws = law_description(max_width)

        flat_bytes = canonical_bytes(flat)
        law_bytes = canonical_bytes(laws) if laws else 0
        model_bytes = seed_json_bytes + law_bytes

        closure_count = len(flat)
        generated = closure_count - len(SEEDS)
        new_ops = (
            0 if previous_closure_count is None
            else closure_count - previous_closure_count
        )
        added_law_bytes = law_bytes - previous_law_bytes

        frontier_residents = foundation["domains"][f"D{max_width}"]["residents"]
        frontier_selectors = sum(
            1 for (width, _coord) in closure if width == max_width
        )

        rows.append(
            {
                "stage": f"D3..D{max_width}",
                "max_width": max_width,
                "seed_rows": len(SEEDS),
                "closure_rows": closure_count,
                "generated_rows": generated,
                "new_generated_rows": new_ops,
                "expansion_rounds": rounds,
                "seed_json_bytes": seed_json_bytes,
                "law_json_bytes": law_bytes,
                "added_law_json_bytes": added_law_bytes,
                "model_json_bytes": model_bytes,
                "flat_projection_json_bytes": flat_bytes,
                "json_compression_ratio": (
                    f"{flat_bytes / model_bytes:.6f}" if model_bytes else ""
                ),
                "marginal_generated_per_added_law_byte": (
                    f"{new_ops / added_law_bytes:.9f}"
                    if added_law_bytes > 0
                    else ""
                ),
                "flat_coordinate_payload_bits": sum(
                    item["width"] for item in flat
                ),
                "generated_coordinate_payload_bits": sum(
                    item["width"] for item in flat if item["width"] > 3
                ),
                "frontier_total_residents": len(frontier_residents),
                "frontier_selector_rows": frontier_selectors,
                "frontier_non_selector_rows_unclassified": (
                    len(frontier_residents) - frontier_selectors
                ),
                "authority": "#3393 D1-D6 foundation within Contract 11.6",
                "family": "selector",
                "foundation_sha256": foundation_sha256,
                "git_sha": git_sha(),
            }
        )

        previous_closure_count = closure_count
        previous_law_bytes = law_bytes

    # Mandatory concrete current selector curve: 2 -> 6 -> 14 -> 30.
    assert [row["closure_rows"] for row in rows] == [2, 6, 14, 30]
    assert [row["new_generated_rows"] for row in rows] == [0, 4, 8, 16]
    assert rows[-1]["frontier_selector_rows"] == 16
    assert rows[-1]["frontier_non_selector_rows_unclassified"] == 48

    return rows


def write_tsv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=list(rows[0].keys()), delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="")
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()

    rows = compute_rows()

    for row in rows:
        print(
            f"{row['stage']:8s} closure={row['closure_rows']:2d} "
            f"new={row['new_generated_rows']:2d} "
            f"lawB={row['law_json_bytes']:4d} "
            f"flatB={row['flat_projection_json_bytes']:4d} "
            f"ratio={row['json_compression_ratio']}"
        )

    if args.check_only:
        print("CURRENT-SELECTOR-CLOSURE: PASS")
        return 0

    out = Path(args.out) if args.out else ROOT / "benchmarks/generator-economy/results/current-closure"
    out.mkdir(parents=True, exist_ok=True)
    write_tsv(out / "closure.tsv", rows)
    (out / "summary.json").write_text(
        json.dumps(
            {
                "schema": "sens-current-selector-closure/v1",
                "authority": "#3393 D1-D6 foundation within Contract 11.6",
                "benchmark_issue": "#1973",
                "theorem_consumer": "#3499",
                "semantic_rule": (
                    "compression never ratifies a law; every generated child is "
                    "validated against current authority before accounting"
                ),
                "rows": rows,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    final = rows[-1]
    pareto_semantic = {
        "schema": "sens-pareto-semantic-vector/v1",
        "source_issue": "#1973",
        "contract": "11.6",
        "scope": "selector-family:D3-D6",
        "completeness": "family-only",
        "authority": final["authority"],
        "git_sha": final["git_sha"],
        "family": final["family"],
        "foundation_sha256": final["foundation_sha256"],
        "metrics": {
            "seed_residents": final["seed_rows"],
            "closure_residents": final["closure_rows"],
            "generated_residents": final["generated_rows"],
            "law_bytes": final["law_json_bytes"],
            "seed_bytes": final["seed_json_bytes"],
            "model_bytes": final["model_json_bytes"],
            "flat_equivalent_bytes": final["flat_projection_json_bytes"],
            "frontier_selector_residents": final["frontier_selector_rows"],
            "frontier_non_selector_unclassified": final[
                "frontier_non_selector_rows_unclassified"
            ],
        },
        "warning": (
            "Contract 11.6 family-scoped selector accounting only. "
            "D7 is current but non-callable and is outside this closure. "
            "This artifact does not quantify whole-language independent facts, "
            "residue, or semantic size."
        ),
    }
    (out / "pareto-semantic.json").write_text(
        json.dumps(pareto_semantic, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"wrote {out / 'closure.tsv'}")
    print(f"wrote {out / 'summary.json'}")
    print(f"wrote {out / 'pareto-semantic.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
