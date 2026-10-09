#!/usr/bin/env python3
"""D10 Prolog constraint research gate: source-grade HOLD + REAL SWI witness.

DO NOT increment canonical D10 selected or allocate a coordinate from this
research. No .sens/T5 writer, D2 control or pseudo-Prolog Python oracle.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
DOSSIER = REPO / "knowledge/d10-prolog-constraint-hobbies-research-v1.json"
INVENTORY = REPO / "knowledge/d10-v1-semantic-inventory.json"
ORACLE = REPO / "tests/d10_prolog_constraint_oracle.pl"
STATUS = "SOURCE_GROUNDED_RESEARCH_HOLD"
FIELDS = {
    "UNIFY-WITH-OCCURS-CHECK": ("unify_with_occurs_check/2", "/unify_with_occurs_check"),
    "DELAYED-TERM-DISEQUALITY": ("dif/2", "/dif"),
    "COPY-RESIDUAL-CONSTRAINTS": ("copy_term/3", "/copy_term"),
}


class Blocked(ValueError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise Blocked(reason)


def inspect(dossier: dict, inventory: dict) -> dict:
    require(dossier.get("schema") == "d10-prolog-constraint-hobby-research/v1",
            "SCHEMA: research dossier version unknown")
    require(dossier.get("status") == STATUS, "STATUS: never label research admitted")
    intake = dossier.get("intake", {})
    require(isinstance(intake, dict), "INTAKE: object missing")
    require(intake.get("selected_delta") == 0 and intake.get("coordinate_delta") == 0,
            "SELECTION: research cannot mint a D10 slot")
    require(intake.get("ratified_at_intake") == 0, "RATIFICATION: owner action absent")
    require(intake.get("selected_at_intake") == 630, "INTAKE: expected frozen baseline 630")
    require(bool(re.fullmatch("[0-9a-f]{40}", str(intake.get("inventory_blob_sha")))),
            "PROVENANCE: original selected inventory Git blob required")
    require(inventory.get("domain") == "D10" and inventory.get("width") == 10
            and inventory.get("capacity") == 1024, "D10: unexpected inventory authority")
    summary = inventory.get("accounting", {})
    require(summary.get("ratified_d10_residents") == 0, "RATIFICATION: no approval assumed")
    require(summary.get("selected_semantic_candidates", -1) >= 630,
            "INTAKE: current inventory older than frozen snapshot")
    rows = inventory.get("rows", [])
    require(len(rows) == summary.get("selected_semantic_candidates"),
            "INVENTORY: selected count and real rows disagree")
    existing = {r.get("semantic_name") for r in rows}
    require(len(existing) == len(rows), "INVENTORY: duplicate semantic spellings require owner review")
    proof = dossier.get("proof_conditions", {})
    require(proof.get("self_hosted_sens_runtime_executed") is False,
            "SELFHOST: false SENS runtime proof")
    require(proof.get("ratified") is False and proof.get("d1_d9_behavioral_dedup") == "PENDING"
            and str(proof.get("d10_behavioral_dedup", "")).startswith("PENDING")
            and proof.get("owner_core_vs_library") == "PENDING",
            "DEDUP: owner or behavioral proof cannot be inferred")
    require(proof.get("blocked_original_source") is None,
            "MIGRATION: never fabricate a blocked executable source")
    proposals = dossier.get("proposals")
    require(isinstance(proposals, list) and len(proposals) == len(FIELDS),
            "PROPOSAL: exactly three disjoint source-backed research laws")
    seen_ids: set[str] = set()
    seen_surfaces: set[str] = set()
    seen_labels: set[str] = set()
    semantic_names = set()
    for row in proposals:
        name = row.get("semantic_name")
        require(name in FIELDS and name not in semantic_names, "DEDUP: duplicate/unknown law")
        semantic_names.add(name)
        require(name not in existing, f"DEDUP: {name} already selected in current D10")
        expected_donor, url_fragment = FIELDS[name]
        require(row.get("width") == 10 and row.get("coordinate") is None
                and row.get("ratified") is False and row.get("selected") is False,
                "COORDINATE: D10 research may not allocate nor ratify")
        require(row.get("status") == "RESEARCH_HOLD_BEHAVIORAL_DEDUP",
                "STATUS: no automatic core selection")
        require(row.get("exact_name_d10_snapshot_duplicate") is False,
                "DEDUP: recorded exact-name collision")
        require(row.get("migration_block") is None,
                "MIGRATION: candidate may not pretend to fix a source without proof")
        require(row.get("mechanism_only") is False,
                "OWNERSHIP: hardware-only mechanism is not a language root")
        require(row.get("id", "").startswith("D10P-PROLOG-")
                and row["id"] not in seen_ids, "ID: distinct stable proposal ID required")
        seen_ids.add(row["id"])
        surfaces = row.get("surfaces", {})
        require(isinstance(surfaces, dict)
                and isinstance(surfaces.get("uk"), str)
                and 2 <= len(surfaces["uk"]) <= 10
                and isinstance(surfaces.get("укр"), str)
                and len(surfaces["укр"]) >= 5
                and surfaces.get("sym") is None
                and surfaces["uk"] not in seen_surfaces,
                "SURFACE: nonambiguous Ukrainian surface required; no invented binary code")
        seen_surfaces.add(surfaces["uk"])
        require(surfaces.get("LISP") == expected_donor, "DONOR: wrong predicate")
        donor = row.get("donor", {})
        require(donor.get("manual", "").startswith("https://www.swi-prolog.org/pldoc/")
                and url_fragment in donor["manual"]
                and donor.get("git_sha") is None
                and donor.get("reason_no_sha"),
                "PROVENANCE: real public manual url and truthful unpinned source status required")
        require(isinstance(row.get("semantic_law"), str)
                and len(row["semantic_law"]) > 80
                and row.get("arity") in (2, 3)
                and isinstance(row.get("derivable"), str)
                and len(row["derivable"]) > 25,
                "LAW: arity/behavior/derivability needs real evidence")
        pos, neg = row.get("positive_cases"), row.get("falsifiers")
        require(isinstance(pos, list) and len(pos) >= 2
                and isinstance(neg, list) and len(neg) >= 1
                and all(isinstance(x, str) and x for x in pos + neg),
                "ORACLE: >=2 positive cases and >=1 falsifier required")
        for tag in pos + neg:
            require(tag not in seen_labels, "ORACLE: duplicate witness ID across roots")
            seen_labels.add(tag)
    require(semantic_names == set(FIELDS), "PROPOSAL: roots not exhaustive")
    oracle = dossier.get("oracle", {})
    expected = oracle.get("expected_tags")
    require(isinstance(expected, list) and len(expected) == oracle.get("expected_tag_count")
            and set(expected) == seen_labels and len(expected) == len(set(expected)),
            "ORACLE: case coverage must match exact semantically described witnesses")
    require(oracle.get("independence_caveat", "").startswith("Real SWI donor oracle"),
            "INDEPENDENCE: don't falsely claim independent SENS or second oracle")
    return {
        "status": "PASS_RESEARCH_HOLD_NOT_SELECTED",
        "selected_current": len(rows),
        "selected_delta": 0,
        "ratified_d10": 0,
        "proposals": len(proposals),
        "donor_witness_cases": len(expected),
        "full_behavioral_d1_d9_d10_dedup": "PENDING",
        "sens_runtime_oracle": "NOT_EXECUTED",
        "source_provenance": "REAL_SWI_MANUAL_URL_WITH_RUNTIME_WITNESS_UNPINNED_GIT",
    }


def mutation_tests(dossier: dict, inventory: dict) -> int:
    mutations = []
    def mutate(fn):
        candidate = deepcopy(dossier)
        fn(candidate)
        mutations.append(candidate)
    mutate(lambda x: x["intake"].__setitem__("selected_delta", 1))
    mutate(lambda x: x["proof_conditions"].__setitem__("ratified", True))
    mutate(lambda x: x["proof_conditions"].__setitem__("self_hosted_sens_runtime_executed", True))
    mutate(lambda x: x["proof_conditions"].__setitem__("blocked_original_source", "fake.lisp"))
    mutate(lambda x: x["proposals"][0].__setitem__("coordinate", "0000000000"))
    mutate(lambda x: x["proposals"][0].__setitem__("selected", True))
    mutate(lambda x: x["proposals"][1].__setitem__("status", "SELECTED"))
    mutate(lambda x: x["proposals"][1]["donor"].__setitem__("manual", "https://example.invalid/fake"))
    mutate(lambda x: x["proposals"][2]["surfaces"].__setitem__("uk", x["proposals"][0]["surfaces"]["uk"]))
    mutate(lambda x: x["proposals"][2].__setitem__("semantic_name", x["proposals"][1]["semantic_name"]))
    mutate(lambda x: x["proposals"][0].__setitem__("falsifiers", []))
    mutate(lambda x: x["oracle"].__setitem__("expected_tag_count", 0))
    for i, mutated in enumerate(mutations):
        try:
            inspect(mutated, inventory)
        except Blocked:
            continue
        raise Blocked(f"MUTATION: expected fail-closed on adversarial variant {i+1}")
    return len(mutations)


def run_swi_oracle(dossier: dict) -> dict:
    executable = shutil.which("swipl")
    require(executable is not None, "DONOR: real SWI-Prolog unavailable; do not emulate with Python")
    proc = subprocess.run(
        [executable, "-q", "-s", str(ORACLE), "-g", "main", "-t", "halt"],
        cwd=REPO, capture_output=True, text=True, timeout=45,
    )
    require(proc.returncode == 0 and not proc.stderr,
            "DONOR: SWI oracle rejected witnesses:\n" + proc.stderr[-1000:])
    lines = proc.stdout.strip().splitlines()
    require(len(lines) >= 2 and re.fullmatch(r"SWI_VERSION\|\d+\.\d+\.\d+", lines[0]),
            "DONOR: real exact runtime version witness missing")
    observed = []
    for line in lines[1:]:
        require(line.startswith("PASS|"), "DONOR: unrecognized or failed witness output")
        observed.append(line[5:])
    expected = dossier["oracle"]["expected_tags"]
    require(observed == expected, "DONOR: 13 exact cases/ordering differ from source-graded dossier")
    return {
        "version": lines[0].split("|", 1)[1],
        "cases_passed": len(observed),
        "case_ids": observed,
        "donor_oracle_sha256": hashlib.sha256(ORACLE.read_bytes()).hexdigest(),
        "runtime": executable,
        "sens_native_oracle": "NOT_EXECUTED",
        "independent_second_donor": "NOT_EXECUTED",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true",
                    help="strict dossier + 12 fail-closed adversarial mutations")
    ap.add_argument("--run-oracle", action="store_true",
                    help="require executable real SWI-Prolog, no simulated fallback")
    ap.add_argument("--report", type=Path,
                    help="optional proof JSON outside source repository only")
    args = ap.parse_args(argv)
    try:
        dossier = json.loads(DOSSIER.read_text(encoding="utf-8"))
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        result = inspect(dossier, inventory)
        result["mutations_blocked"] = mutation_tests(dossier, inventory) if args.self_test else 0
        result["donor_runtime"] = run_swi_oracle(dossier) if args.run_oracle else {
            "status": "NOT_EXECUTED"}
        if args.report is not None:
            dest = args.report.resolve()
            require(not dest.is_relative_to(REPO) and not dest.exists(),
                    "OUTPUT: report must be external and no-clobber")
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open("x", encoding="utf-8") as fh:
                json.dump(result, fh, ensure_ascii=False, indent=2)
                fh.write("\n")
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (Blocked, OSError, ValueError, subprocess.TimeoutExpired) as error:
        print("D10 RESEARCH BLOCKED: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
