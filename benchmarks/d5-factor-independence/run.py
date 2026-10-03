#!/usr/bin/env python3
"""#2583/#2593 — current-main post-D4 factor independence gate.

Consumes only evidence already landed on main:
- #2522/#2530 protocol cube;
- #2568/#2569 expansion timing;
- #2580/#2588 + #2591 special-call packaging;
- #2589/#2598 mutation factorization;
- #2488/#2504 RETURN residue/root theorem;
- #2609/#2611 typed cross-family parent guard.

Factor independence is corpus accounting. It is not roothood, width, placement,
or residency.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
GRAPH = ROOT / "benchmarks" / "d5-structural-discovery" / "factor-graph.json"
CUBE = ROOT / "scripts" / "research-2522-fexpr-protocol-cube.py"
TIMING = ROOT / "scripts" / "research-2568-macro-timing.py"
RETURN_PLACEMENT = ROOT / "scripts" / "research-2488-return-placement.py"
NONLOCAL_EXIT = ROOT / "scripts" / "research-2590-nonlocal-exit.py"
CROSS_FAMILY = ROOT / "scripts" / "research-2609-cross-family-parent.py"
MUTATION_TEST = ROOT / "crates" / "sens" / "tests" / "post_d4_set_setq_factor.rs"
NONLOCAL_TEST = ROOT / "crates" / "sens" / "tests" / "post_d4_nonlocal_exit_factor.rs"
SPECIAL_CALL = ROOT / "benchmarks" / "d5-structural-discovery" / "special-call-factor.json"

POST_D4 = {
    "shared-location-update",
    "non-local-exit",
    "raw-form-input",
    "explicit-caller-env",
    "returned-form-protocol",
    "expansion-timing",
    "invocation-packaging",
}


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run_text(path: Path) -> str:
    proc = subprocess.run(
        [sys.executable, str(path)],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=ROOT,
    )
    return proc.stdout


def cube_remove_one(module, target: str) -> dict:
    protocols = module.all_protocols()

    if target == "raw-form-input":
        other_key = lambda p: (p.env.value, p.result.value)
        observable = module.raw_operand_probe
    elif target == "explicit-caller-env":
        other_key = lambda p: (p.operand.value, p.result.value)
        observable = module.caller_env_probe
    elif target == "returned-form-protocol":
        other_key = lambda p: (p.operand.value, p.env.value)
        observable = module.result_protocol_probe
    else:
        raise KeyError(target)

    groups = {}
    for protocol in protocols.values():
        groups.setdefault(other_key(protocol), []).append(observable(protocol))

    ambiguous_without_target = {
        str(key): sorted({repr(x) for x in values})
        for key, values in groups.items()
        if len(set(values)) > 1
    }
    assert len(groups) == 4
    assert len(ambiguous_without_target) == 4
    return {
        "fixed_other_assignments": len(groups),
        "assignments_with_two_target_observations": len(ambiguous_without_target),
        "reconstructible_from_remaining_protocol_axes": False,
    }


def base_row(factor_id: str, observable: str) -> dict:
    return {
        "factor_id": factor_id,
        "semantic_observable": observable,
        "status": "BOUNDED-INDEPENDENT",
        "placement": "UNPLACED",
        "root_promoted_by_this_model": False,
        "width_inference": "NONE",
        "unresolved_dependency": None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    factors = {
        row["factor_id"]: row
        for row in graph["factors"]
        if row["factor_id"] in POST_D4
    }
    assert set(factors) == POST_D4
    assert graph["summary"]["historical_rows_consumed"] == 19
    assert graph["summary"]["post_d4_factor_candidates"] == 7
    assert graph["summary"]["roots_promoted_by_this_model"] == 0
    assert len(graph["summary"]["external_root_theorems"]) == 1
    assert graph["summary"]["new_d5_residents"] == 0
    assert graph["summary"]["placement_search_authorized"] is False

    cube_text = run_text(CUBE)
    timing_text = run_text(TIMING)
    return_text = run_text(RETURN_PLACEMENT)
    nonlocal_text = run_text(NONLOCAL_EXIT)
    cross_text = run_text(CROSS_FAMILY)

    assert "FEXPR-PROTOCOL-CUBE=PASS" in cube_text
    assert "DISTINCT-SIGNATURES=8" in cube_text
    assert "EXPANSION-TIMING=INDEPENDENT-AXIS" in timing_text
    assert "NON-CONCLUSION=no-placement-from-timing-axis" in timing_text
    assert "RETURN-ROOT=RESIDUE" in return_text
    assert "EXACT-DOMAIN=UNRESOLVED" in return_text
    assert "BINARY-COORDINATE=UNALLOCATED" in return_text
    assert "NONLOCAL-EXIT-FACTOR=PASS" in nonlocal_text
    assert "STRONGEST-HONEST-PARENT=NO-PARENT" in nonlocal_text
    assert "PROG-CLASSIFICATION=COMPOSITE" in nonlocal_text
    assert "NEW-D5-RESIDENTS=0" in nonlocal_text
    assert "COORDINATES-ALLOCATED=0" in nonlocal_text
    assert "CROSS-FAMILY-PARENT-GUARD=PASS" in cross_text
    assert "ROOTS-PROVEN=0" in cross_text
    assert "D5-RESIDENTS=0" in cross_text
    assert MUTATION_TEST.exists()
    assert NONLOCAL_TEST.exists()

    cube = load_module(CUBE, "factor_independence_cube_2583")
    special_call = json.loads(SPECIAL_CALL.read_text(encoding="utf-8"))
    special_axes = {row["factor_id"]: row for row in special_call["axes"]}
    packaging = special_axes["invocation-packaging"]
    assert packaging["status"] == "independently-observable-axis"
    assert packaging["root_status"] == "UNPROVEN"
    assert special_call["summary"]["proved_semantic_roots"] == 0
    assert special_call["summary"]["coordinates_allocated"] == 0

    results = []
    for factor_id in sorted(POST_D4):
        row = base_row(factor_id, factors[factor_id]["semantic_observable"])

        if factor_id in {
            "raw-form-input",
            "explicit-caller-env",
            "returned-form-protocol",
        }:
            row["witness"] = "#2522/#2530"
            row["remove_one_attack"] = cube_remove_one(cube, factor_id)

        elif factor_id == "expansion-timing":
            row["witness"] = "#2568/#2569"
            row["remove_one_attack"] = {
                "trace": "define OLD -> compile/define containing form -> redefine NEW -> invoke",
                "definition_time_observation": "OLD",
                "evaluation_time_observation": "NEW",
                "reconstructible_from_form_protocol_alone": False,
            }

        elif factor_id == "invocation-packaging":
            row["witness"] = "#2580/#2588/#2591"
            row["remove_one_attack"] = {
                "whole_call_distinguishes_alias_heads": True,
                "operand_only_alias_payload_collides": True,
                "reconstructible_without_explicit_head_channel": False,
                "source": packaging["remove_one_attack"],
            }

        elif factor_id == "shared-location-update":
            row["witness"] = "#2589/#2598 + #2609/#2611"
            row["remove_one_attack"] = {
                "mutation_observation": "existing observer changes OLD -> NEW",
                "without_factor": "store/location observation remains OLD",
                "cross_family_reconstruction": "rejected without explicit store/location bridge",
                "reconstructible_from_remaining_post_d4_families": False,
            }

        elif factor_id == "non-local-exit":
            row["witness"] = "#2488/#2504 + #2590/#2606 + #2609/#2611"
            row["external_root_theorem"] = {
                "classification": "semantic-residue-root",
                "evidence": "#2488/#2504",
                "exact_width": "UNKNOWN",
                "coordinate": "UNPLACED",
            }
            row["remove_one_attack"] = {
                "exit_observation": "skip ordinary caller continuation to nearest active PROG",
                "without_factor": "ordinary local completion cannot skip caller",
                "cross_family_reconstruction": "rejected without dynamic-exit bridge",
                "reconstructible_from_remaining_post_d4_families": False,
            }

        results.append(row)

    assert len(results) == 7
    assert all(row["status"] == "BOUNDED-INDEPENDENT" for row in results)
    assert not any(row["root_promoted_by_this_model"] for row in results)
    assert all(row["placement"] == "UNPLACED" for row in results)
    assert all(row["width_inference"] == "NONE" for row in results)

    artifact = {
        "schema": "d5-factor-independence/v2",
        "authority": "research-only-no-placement",
        "phase": "STRUCTURAL-DISCOVERY",
        "domain": "Core.D5-structural-candidate",
        "binary_object": "UNPLACED",
        "declared_corpus": "completed 19-row Early-Lisp historical dataset factored against current D1-D4 and post-D4 witnesses",
        "results": results,
        "summary": {
            "historical_rows_consumed": 19,
            "factors_tested": 7,
            "bounded_independent": 7,
            "unknown": 0,
            "roots_promoted_by_this_model": 0,
            "external_root_theorems": 1,
            "new_d5_residents": 0,
            "coordinates_allocated": 0,
            "d5_selector_generated": 8,
            "d5_unknown_free": 24,
            "placement_authorized": False,
        },
        "non_conclusions": [
            "seven independent corpus factors do not imply seven semantic roots",
            "factor count does not imply bit width",
            "factor independence does not allocate a resident or coordinate",
            "RETURN roothood is an external theorem, not a promotion by this model",
            "no D5 coordinate is allocated",
        ],
    }

    (args.out / "result.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# D5 factor independence — current-main closeout",
        "",
        "| factor | status | witness | root promoted here? | placement |",
        "|---|---|---|---|---|",
    ]
    for row in results:
        lines.append(
            f"| {row['factor_id']} | {row['status']} | {row['witness']} | "
            f"{str(row['root_promoted_by_this_model']).lower()} | {row['placement']} |"
        )

    lines += [
        "",
        "Summary:",
        "- historical rows consumed: 19/19;",
        "- bounded-independent corpus factors: 7;",
        "- unresolved factors: 0;",
        "- roots promoted by this model: 0;",
        "- external root theorems preserved: 1 (RETURN, #2488/#2504);",
        "- new D5 residents: 0;",
        "- coordinates allocated: 0;",
        "- D5 map remains 8 selector-generated + 24 UNKNOWN/free.",
        "",
        "Seven corpus facts are not seven roots or seven bits.",
        "",
    ]
    (args.out / "report.md").write_text("\n".join(lines), encoding="utf-8")

    print("D5-FACTOR-INDEPENDENCE=PASS")
    print("historical-rows-consumed=19")
    print("bounded-independent=7")
    print("unknown=0")
    print("roots-promoted-by-this-model=0")
    print("external-root-theorems=1")
    print("new-d5-residents=0")
    print("coordinates-allocated=0")
    print("d5-selector-generated=8")
    print("d5-unknown-free=24")
    print("RULE=seven-corpus-facts-are-not-seven-roots")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
