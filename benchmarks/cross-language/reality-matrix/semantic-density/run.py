#!/usr/bin/env python3
"""Strict SENS law-generated semantic-density baseline for Reality Matrix #3680.

This baseline deliberately counts only the current selector theorem family whose
generated coordinates can be cross-checked against ratified D4/D5/D6 authority.
It does NOT count D7 geometry, D6 gauge placements, historical coordinates, or
merely-related D5 families as "generated".

No bit-normalized density is emitted because laws themselves do not yet have a
canonical bit encoding.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
FOUNDATION = ROOT / "knowledge" / "d1-d7-foundation.json"
D4 = ROOT / "knowledge" / "d4-cleanroom.json"
D5 = ROOT / "knowledge" / "d5-ratified.json"
D6 = ROOT / "knowledge" / "d6-ratified.json"
FORECAST = ROOT / "scripts" / "research-2322-generative-domain-forecast.py"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_forecast():
    spec = importlib.util.spec_from_file_location("sens_selector_forecast", FORECAST)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {FORECAST}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True, type=Path)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    foundation = load_json(FOUNDATION)
    d4 = load_json(D4)
    d5 = load_json(D5)
    d6 = load_json(D6)
    forecast = load_forecast()

    if foundation["status"] != "owner-ratified":
        raise RuntimeError("D1-D7 foundation is not owner-ratified")
    if foundation["research_domains"] != ["D8"]:
        raise RuntimeError("expected D8-only research boundary")

    _rows, generated_words = forecast.build(3, 7)

    d3_roots = set(forecast.ROOTS)
    if d3_roots != {"011", "100"}:
        raise RuntimeError(f"unexpected selector roots: {sorted(d3_roots)}")
    d3_residents = foundation["domains"]["D3"]["residents"]
    if {d3_residents[word] for word in d3_roots} != {"CAR", "CDR"}:
        raise RuntimeError("current D3 roots no longer resolve to CAR/CDR")

    d4_name_to_coord = {name: coord for coord, name in d4["residents"].items()}
    d4_strict = {
        d4_name_to_coord[name]
        for name in d4["classification"]["generated_selectors"]
    }
    if d4_strict != set(generated_words["D4"]):
        raise RuntimeError(
            f"D4 theorem set drift: ledger={sorted(d4_strict)} "
            f"forecast={generated_words['D4']}"
        )

    d5_strict: set[str] = set()
    for pair in d5["pairs"]:
        if (
            pair.get("relation_class") == "SEMANTIC-GENERATOR"
            and pair.get("law_kind") == "selector-projection-composition"
        ):
            d5_strict.update(member["coordinate"] for member in pair["members"])
    if d5_strict != set(generated_words["D5"]):
        raise RuntimeError(
            f"D5 theorem set drift: ledger={sorted(d5_strict)} "
            f"forecast={generated_words['D5']}"
        )

    d6_strict = {
        row["coordinate"]
        for row in d6["rows"]
        if row.get("coordinate_basis") == "proved-selector-generator"
    }
    if d6_strict != set(generated_words["D6"]):
        raise RuntimeError(
            f"D6 theorem set drift: ledger={sorted(d6_strict)} "
            f"forecast={generated_words['D6']}"
        )

    if generated_words["D7"]:
        raise RuntimeError("D7 must not inherit selector residents under Contract 11.6")

    generated_by_domain = {
        "D4": len(d4_strict),
        "D5": len(d5_strict),
        "D6": len(d6_strict),
        "D7": 0,
    }
    derived = sum(generated_by_domain.values())

    resident_counts = {
        name: len(domain["residents"])
        for name, domain in foundation["domains"].items()
    }
    scope_d4_d6 = sum(resident_counts[name] for name in ("D4", "D5", "D6"))
    all_d1_d7 = sum(resident_counts.values())

    if generated_by_domain != {"D4": 4, "D5": 8, "D6": 16, "D7": 0}:
        raise RuntimeError(f"strict generated count drift: {generated_by_domain}")
    if scope_d4_d6 != 112:
        raise RuntimeError(f"D4-D6 admitted scope drift: {scope_d4_d6}")
    if all_d1_d7 != 252:
        raise RuntimeError(f"D1-D7 admitted total drift: {all_d1_d7}")

    result = {
        "schema": "sens-reality-matrix-semantic-density/v1",
        "scope": "strict current selector theorem only",
        "authority": {
            "foundation": str(FOUNDATION.relative_to(ROOT)),
            "d4": str(D4.relative_to(ROOT)),
            "d5": str(D5.relative_to(ROOT)),
            "d6": str(D6.relative_to(ROOT)),
            "generator": str(FORECAST.relative_to(ROOT)),
        },
        "independent_roots": 2,
        "root_coordinates": sorted(d3_roots),
        "law_count_sensitivity": {
            "law_family_count": 1,
            "branch_choice_count": 2,
            "explanation": (
                "One selector-composition law family has two admitted branch choices: "
                "compose CAR or compose CDR. Both count conventions are reported."
            ),
        },
        "generated_by_domain": generated_by_domain,
        "derived_residents": derived,
        "admitted_residents_scope_d4_d6": scope_d4_d6,
        "admitted_residents_all_d1_d7": all_d1_d7,
        "coverage_scope_d4_d6": derived / scope_d4_d6,
        "coverage_all_d1_d7": derived / all_d1_d7,
        "residents_per_root": derived / 2,
        "residents_per_law_family": derived / 1,
        "residents_per_law_branch_choice": derived / 2,
        "canonical_description_bits": None,
        "bit_normalized_density": None,
        "excluded_from_generated_count": [
            "D4 derived/bootstrap residents that are not selector-law children",
            "D5 non-selector semantic-generator/local-algebra/historical families",
            "D6 owner-ratified law-anchored coordinates",
            "D6 owner-ratified S4 gauge coordinates",
            "all D7 sound/text residents",
            "all D8 research candidates",
        ],
    }

    (args.out_dir / "strict-baseline.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# Strict law-generated semantic-density baseline",
        "",
        "Only theorem-backed current selector descendants are counted as generated.",
        "No bit-normalized score is reported because law encoding is not canonical.",
        "",
        f"- roots: {result['independent_roots']} (D3 CAR/CDR)",
        f"- generated D4/D5/D6: 4 / 8 / 16 = {derived}",
        f"- D4-D6 admitted residents: {scope_d4_d6}",
        f"- strict generator coverage in its admitted target scope: {derived / scope_d4_d6:.2%}",
        f"- all D1-D7 admitted residents: {all_d1_d7}",
        f"- strict generated share of all D1-D7: {derived / all_d1_d7:.2%}",
        f"- residents/root: {derived / 2:.1f}",
        f"- residents/law-family: {derived:.1f}",
        f"- residents/branch-choice if the two law branches are counted separately: {derived / 2:.1f}",
        "",
        "D7 contributes zero to this strict selector metric; that is deliberate, not a claim",
        "that D7 lacks structure. Its geometry needs its own normalized theorem certificates",
        "before it can enter a cross-system generated-density comparison.",
        "",
    ]
    (args.out_dir / "report.md").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
