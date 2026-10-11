#!/usr/bin/env python3
"""Fail-closed finite abductive oracle; never selects or ratifies a D10 resident."""
from __future__ import annotations

import argparse
from copy import deepcopy
from itertools import combinations
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = ROOT / "knowledge/d10-abductive-minimal-explanations-v1.json"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"
ORACLE = ROOT / "tests/oracles/d10_abductive_minimal_explanations.pl"
EXPECTED_SCHEMA = "d10-abductive-minimal-explanations/v1"


class Blocked(ValueError):
    pass


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise Blocked(reason)


def horn_closure(case: dict, assumptions: set[str]) -> set[str]:
    derived = set(case["facts"]) | set(assumptions)
    while True:
        added = {
            rule["head"]
            for rule in case["rules"]
            if set(rule["body"]) <= derived and rule["head"] not in derived
        }
        if not added:
            return derived
        derived.update(added)


def coherent(case: dict, derived: set[str]) -> bool:
    return all(not set(forbidden) <= derived for forbidden in case["integrity_constraints"])


def solve_case(case: dict) -> list[list[str]]:
    atoms = sorted(set(case["abducibles"]))
    eligible: set[frozenset[str]] = set()
    for size in range(len(atoms) + 1):
        for candidate_tuple in combinations(atoms, size):
            candidate = frozenset(candidate_tuple)
            closure = horn_closure(case, set(candidate))
            if case["goal"] in closure and coherent(case, closure):
                eligible.add(candidate)
    minimal = [
        candidate for candidate in eligible
        if not any(other < candidate for other in eligible)
    ]
    return [
        sorted(candidate)
        for candidate in sorted(minimal, key=lambda item: (len(item), tuple(sorted(item))))
    ]


def encode_answers(answers: list[list[str]]) -> str:
    if not answers:
        return "NONE"
    return ";".join(",".join(explanation) if explanation else "EPS" for explanation in answers)


def verify_manifest(manifest: dict, inventory: dict, foundation: dict) -> dict:
    require(manifest.get("schema") == EXPECTED_SCHEMA, "SCHEMA: unsupported dossier version")
    require(manifest.get("status") == "SOURCE-GROUNDED-RESEARCH-HOLD-NOT-SELECTED",
            "STATUS: research must not imply D10 selection")
    base = manifest.get("baseline", {})
    require(base.get("selected_d10_at_creation") == 634, "BASELINE: immutable initial count changed")
    require(base.get("d10_inventory_blob_sha") == "65014431ac3e64633cd0be3630cfafc5e7a9aea3",
            "PROVENANCE: initial inventory blob must remain pinned as history")
    require(base.get("foundation_blob_sha") == "09d1d71c39d1484dfd005a5068dbb18b76f0f0d4",
            "PROVENANCE: foundation blob must remain pinned")
    require(inventory.get("domain") == "D10" and inventory.get("width") == 10
            and inventory.get("capacity") == 1024, "D10: current authority shape changed")
    require(len(inventory.get("rows", [])) == inventory.get("accounting", {}).get("selected_semantic_candidates"),
            "INVENTORY: row count/accounting disagree")
    require(len(inventory.get("rows", [])) >= base["selected_d10_at_creation"],
            "INVENTORY: current D10 is older than this immutable snapshot")
    require(inventory["accounting"].get("ratified_d10_residents") == 0,
            "RATIFICATION: this research dossier does not grant ratification")
    proposal = manifest["proposal"]
    require(proposal.get("d10_selection_delta") == 0
            and proposal.get("coordinate") is None
            and proposal.get("ratified") is False
            and proposal.get("physical_t5_authorized") is False,
            "AUTHORITY: research cannot assign a coordinate, select, ratify, or authorize T5")

    name = proposal["semantic_name"].upper()
    lower = {
        str(resident).upper()
        for domain in foundation["domains"].values()
        for resident in domain.get("residents", {}).values()
    }
    selected = {row["semantic_name"].upper() for row in inventory["rows"]}
    require(name not in lower, "DEDUP: exact name is already in ratified D1-D9")
    require(name not in selected, "DEDUP: exact name is already selected in D10")
    require(proposal.get("behavioral_dedup", "").startswith("PENDING"),
            "DEDUP: behavioral derivability must remain visibly unresolved")
    require(proposal.get("owner_review") == "PENDING",
            "OWNER: source evidence is not approval")
    require(proposal.get("status") == "HOLD-CORE-VS-LIBRARY-REVIEW",
            "CORE/LIBRARY: selection cannot precede the stated review")

    cases = manifest["oracle"].get("cases")
    require(isinstance(cases, list) and len(cases) == 12, "ORACLE: expected exactly 12 bounded cases")
    ids = [case.get("id") for case in cases]
    require(len(set(ids)) == len(ids), "ORACLE: duplicate case identifier")
    require(ids == manifest["oracle"].get("case_ids"), "ORACLE: manifest case index drift")
    for case in cases:
        require(case["id"] and case["goal"], "ORACLE: empty ID or goal")
        require(len(case["abducibles"]) == len(set(case["abducibles"])), "ORACLE: duplicate abducible")
        atom_set = set(case["facts"]) | set(case["abducibles"])
        for rule in case["rules"]:
            require(bool(rule.get("head")) and isinstance(rule.get("body"), list),
                    "ORACLE: malformed Horn rule")
            atom_set.add(rule["head"])
            atom_set.update(rule["body"])
        for forbidden in case["integrity_constraints"]:
            require(bool(forbidden), "ORACLE: forbidden conjunction cannot be empty in this fragment")
            require(set(forbidden) <= atom_set, "ORACLE: constraint contains an undeclared atom")
        require(solve_case(case) == case.get("expected"),
                "ORACLE: embedded expected result is false: " + case["id"])
        for explanation in case["expected"]:
            require(explanation == sorted(explanation), "ORACLE: explanation atoms are not canonical")
    return {"cases": len(cases), "candidate": name, "selected_delta": 0, "ratified": 0}


def self_test(manifest: dict, inventory: dict, foundation: dict) -> None:
    verify_manifest(manifest, inventory, foundation)
    mutations = [
        ("coordinate", lambda d: d["proposal"].update(coordinate="0000000000")),
        ("selection_delta", lambda d: d["proposal"].update(d10_selection_delta=1)),
        ("ratification", lambda d: d["proposal"].update(ratified=True)),
        ("physical_t5", lambda d: d["proposal"].update(physical_t5_authorized=True)),
        ("hold_status", lambda d: d["proposal"].update(status="SELECTED")),
        ("owner_review", lambda d: d["proposal"].update(owner_review="APPROVED")),
        ("empty_constraint", lambda d: d["oracle"]["cases"][0].update(integrity_constraints=[[]])),
        ("wrong_expected", lambda d: d["oracle"]["cases"][0].update(expected=[["rain", "sprinkler"]])),
    ]
    for name, mutate in mutations:
        changed = deepcopy(manifest)
        mutate(changed)
        try:
            verify_manifest(changed, inventory, foundation)
        except (Blocked, KeyError):
            continue
        raise Blocked("SELF-TEST: mutation was accepted: " + name)
    print("D10 abductive finite model: PASS 12/12 expected cases")
    print("D10 abductive fail-closed metadata: PASS 8/8 negative mutations")
    print("D10 selection: 0; coordinate: null; ratified: 0; SENS runtime parity: NOT TESTED")


def run_swipl(executable: str, manifest: dict) -> None:
    completed = subprocess.run(
        [executable, "-q", "-s", str(ORACLE)],
        cwd=ROOT, capture_output=True, text=True, timeout=90, check=False,
    )
    if completed.returncode != 0:
        raise Blocked("SWI-Prolog oracle failed:\n" + completed.stdout + "\n" + completed.stderr)
    observed = {}
    for line in completed.stdout.splitlines():
        if not line.startswith("RESULT|"):
            if line.strip():
                raise Blocked("SWI-Prolog oracle emitted unexpected output: " + line)
            continue
        parts = line.split("|", 2)
        require(len(parts) == 3, "SWI-Prolog oracle malformed output")
        case_id, encoded = parts[1], parts[2]
        require(case_id not in observed, "SWI-Prolog oracle duplicate case output")
        observed[case_id] = encoded

    case_ids = [case["id"] for case in manifest["oracle"]["cases"]]
    require(list(observed) == case_ids, "SWI-Prolog oracle case list/order diverges from dossier")
    mismatches = []
    for case in manifest["oracle"]["cases"]:
        expected = encode_answers(solve_case(case))
        if observed[case["id"]] != expected:
            mismatches.append(f"{case['id']}: Prolog={observed[case['id']]} Python={expected}")
    require(not mismatches, "CROSS-ORACLE mismatch:\n" + "\n".join(mismatches))
    print(f"D10 abductive independent SWI-Prolog oracle: PASS {len(case_ids)}/{len(case_ids)}")
    print("SWI-Prolog is a test donor only; not SENS runtime parity or D10 ratification.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--swipl", default=None, help="Run the independent SWI-Prolog oracle")
    args = parser.parse_args()
    manifest = read_json(DOSSIER)
    inventory = read_json(INVENTORY)
    foundation = read_json(FOUNDATION)
    result = verify_manifest(manifest, inventory, foundation)
    print("D10 abductive source/authority gate: PASS", json.dumps(result, sort_keys=True))
    if args.self_test:
        self_test(manifest, inventory, foundation)
    if args.swipl:
        run_swipl(args.swipl, manifest)


if __name__ == "__main__":
    main()
