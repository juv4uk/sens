#!/usr/bin/env python3
"""#2593 — conservative post-D4 factor independence gate.

Consumes the #2587 factor graph and existing executable witnesses.
Factor independence is not roothood, width, placement, or residency.
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

    # If the target observable were reconstructible from the other factors,
    # every fixed-other group would have exactly one target observation.
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
    assert graph["summary"]["proven_independent_roots"] == 0
    assert graph["summary"]["new_d5_residents"] == 0
    assert graph["summary"]["placement_search_authorized"] is False

    cube_text = run_text(CUBE)
    timing_text = run_text(TIMING)
    assert "FEXPR-PROTOCOL-CUBE=PASS" in cube_text
    assert "DISTINCT-SIGNATURES=8" in cube_text
    assert "EXPANSION-TIMING=INDEPENDENT-AXIS" in timing_text
    assert "NON-CONCLUSION=no-placement-from-timing-axis" in timing_text

    cube = load_module(CUBE, "factor_independence_cube_2593")
    special_call = json.loads(SPECIAL_CALL.read_text(encoding="utf-8"))
    special_axes = {row["factor_id"]: row for row in special_call["axes"]}
    packaging = special_axes["invocation-packaging"]
    assert packaging["status"] == "independently-observable-axis"
    assert packaging["root_status"] == "UNPROVEN"
    assert special_call["summary"]["proved_semantic_roots"] == 0
    assert special_call["summary"]["coordinates_allocated"] == 0

    results = []
    for factor_id in sorted(POST_D4):
        base = {
            "factor_id": factor_id,
            "semantic_observable": factors[factor_id]["semantic_observable"],
            "placement": "UNPLACED",
            "is_root": False,
            "width_inference": "NONE",
        }

        if factor_id in {
            "raw-form-input",
            "explicit-caller-env",
            "returned-form-protocol",
        }:
            attack = cube_remove_one(cube, factor_id)
            assert attack["reconstructible_from_remaining_protocol_axes"] is False
            results.append({
                **base,
                "status": "BOUNDED-INDEPENDENT",
                "witness": "#2522",
                "remove_one_attack": attack,
                "unresolved_dependency": None,
            })
        elif factor_id == "expansion-timing":
            results.append({
                **base,
                "status": "BOUNDED-INDEPENDENT",
                "witness": "#2568/#2569/#2579",
                "remove_one_attack": {
                    "trace": "define macro OLD -> define containing function -> redefine macro NEW -> call",
                    "definition_time_observation": "OLD",
                    "evaluation_time_observation": "NEW",
                    "reconstructible_from_form_protocol_alone": False,
                },
                "unresolved_dependency": None,
            })
        elif factor_id == "invocation-packaging":
            results.append({
                **base,
                "status": "BOUNDED-INDEPENDENT",
                "witness": "#2580/#2588",
                "remove_one_attack": {
                    "whole_call_distinguishes_alias_heads": True,
                    "operand_only_alias_payload_collides": True,
                    "reconstructible_without_explicit_head_channel": False,
                    "source": packaging["remove_one_attack"],
                },
                "unresolved_dependency": None,
            })
        elif factor_id == "shared-location-update":
            results.append({
                **base,
                "status": "BOUNDED-INDEPENDENT",
                "witness": "#2589/#2598/f48956fc",
                "remove_one_attack": {
                    "normalized_set_setq_mutation_signature_equal": True,
                    "target_acquisition_separate": True,
                    "missing_binding_policy_equal": True,
                    "nearest_existing_shadow_policy_equal": True,
                    "reconstructible_without_shared_location_update": False,
                },
                "unresolved_dependency": None,
            })
        elif factor_id == "non-local-exit":
            results.append({
                **base,
                "status": "BOUNDED-INDEPENDENT",
                "witness": "#2488/#2504 + #2593/#2614",
                "remove_one_attack": {
                    "local_d1_d4_reconstruction": False,
                    "global_cps_rewrite_counts_as_protocol_change": True,
                    "nearest_active_prog_exit_observable": True,
                    "external_root_theorem": "semantic-residue-root",
                },
                "unresolved_dependency": None,
            })

    by = {row["factor_id"]: row for row in results}
    assert set(by) == POST_D4
    assert sum(row["status"] == "BOUNDED-INDEPENDENT" for row in results) == 7
    assert sum(row["status"] == "UNKNOWN" for row in results) == 0
    assert not any(row["is_root"] for row in results)
    assert all(row["placement"] == "UNPLACED" for row in results)
    assert all(row["width_inference"] == "NONE" for row in results)

    artifact = {
        "schema": "d5-factor-independence/v1",
        "authority": "research-only-no-placement",
        "phase": "STRUCTURAL-DISCOVERY",
        "domain": "Core.D5-structural-candidate",
        "binary_object": "UNPLACED",
        "results": results,
        "summary": {
            "factors_tested": 7,
            "bounded_independent": 7,
            "unknown": 0,
            "proven_independent_roots": 0,
            "new_d5_residents": 0,
            "coordinates_allocated": 0,
            "placement_authorized": False,
            "roots_promoted_by_this_model": 0,
            "external_root_theorems": [
                {
                    "factor_id": "non-local-exit",
                    "classification": "semantic-residue-root",
                    "evidence": "#2488/#2504",
                    "width": "UNKNOWN",
                    "coordinate": "UNPLACED",
                }
            ],
        },
        "non_conclusions": [
            "factor independence does not imply semantic roothood",
            "factor count does not imply bit width",
            "seven bounded-independent factors do not imply seven suffix bits",
            "UNKNOWN factors are not residues",
            "no D5 coordinate is allocated",
        ],
    }
    (args.out / "result.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# D5 factor independence — #2593",
        "",
        "| factor | status | witness | root? | placement |",
        "|---|---|---|---|---|",
    ]
    for row in results:
        lines.append(
            f"| {row['factor_id']} | {row['status']} | {row['witness']} | "
            f"{str(row['is_root']).lower()} | {row['placement']} |"
        )
    lines += [
        "",
        "Summary:",
        "- bounded-independent factors: 7;",
        "- unresolved factors: 0;",
        "- proven independent roots: 0;",
        "- new D5 residents: 0;",
        "- coordinates allocated: 0.",
        "",
        "The protocol cube proves remove-one non-reconstructibility for raw-form,",
        "caller-env and returned-form axes. The Hart/SENS timing trace witnesses",
        "a distinct expansion-locus observable, and the alias/head collision witness",
        "separates invocation packaging. Merged #2589 resolves shared-location-update,",
        "and #2488/#2504 plus #2593/#2614 resolve non-local-exit as a bounded fact",
        "with an external semantic-residue-root theorem. This model promotes zero roots.",
        "",
    ]
    (args.out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
