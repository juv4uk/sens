#!/usr/bin/env python3
"""Build a complete, deterministic D10 research work queue in one pass.

Does not invent witnesses, turn HOLD into PASS, allocate coordinates, or ratify.
The 721-name database is an archived input; current D10 may have grown.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from check_d10_candidate_database import verify as verify_catalog

ROOT = Path(__file__).resolve().parents[1]
FIELDS = (
    "batch", "priority", "semantic_name", "candidate_origin",
    "source_status", "next_action", "source_records",
    "proposal_ids", "witness_state", "semantic_dedup_state",
)
ACTIONS = (
    "REVIEW_IDENTITY_COLLISION",
    "RESOLVE_SOURCE_HOLD",
    "REPLAY_WITNESS_AND_PROVE_DISTINCTNESS",
    "DEFINE_EXACT_LAW_AND_WITNESS",
    "RECOVER_SOURCE_AND_LAW",
)


def require(condition, reason):
    if not condition:
        raise ValueError("D10_BATCH_BLOCKED: " + reason)


def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def safe_path(root, path):
    if not path or Path(path).is_absolute():
        raise ValueError("D10_BATCH_BLOCKED: invalid path")
    value = (root / path).resolve()
    require(value.is_relative_to(root.resolve()) and value.is_file(),
            "source not found within root: " + str(path))
    return value


def has_exact_law(record):
    law = record.get("observable_law")
    if isinstance(law, str) and law.strip():
        return True
    provenance = record.get("source_provenance", [])
    if isinstance(provenance, list):
        return any(
            isinstance(source, dict)
            and isinstance(source.get("semantic_law"), str)
            and source["semantic_law"].strip()
            and not source["semantic_law"].startswith("Поведінка визначена джерелом")
            for source in provenance
        )
    return False


def source_count(record):
    refs = record.get("source_provenance", [])
    return len(refs) if isinstance(refs, list) else int(bool(refs))


def compile_tasks(pending, current, batch_size=64):
    require(isinstance(batch_size, int) and batch_size >= 1, "bad batch size")
    chosen = {}
    for row in current:
        name = row["semantic_name"].casefold()
        require(name not in chosen, "duplicate current semantic name")
        chosen[name] = row

    seen = set()
    already_accounted = []
    tasks = []
    for candidate in pending:
        name = candidate["semantic_name"]
        key = name.casefold()
        require(key not in seen, "duplicate pending name")
        seen.add(key)
        require(candidate.get("selected") is False and candidate.get("ratified") is False
                and candidate.get("coordinate") is None,
                "pending candidate already claims authority: " + name)
        proposals = candidate.get("proposals", [])
        require(isinstance(proposals, list) and all(isinstance(p, str) for p in proposals),
                "bad proposal identities: " + name)
        selected = chosen.get(key)
        if selected is not None and selected.get("proposal_id") in proposals:
            # Exact proposal ID + exact surface identity, not merely same name.
            # This tracks a source proposal already transferred into v8+.
            already_accounted.append(name)
            continue

        refs = source_count(candidate)
        status = candidate.get("source_status", "")
        origin = candidate.get("candidate_origin", "")
        require(isinstance(status, str) and isinstance(origin, str),
                "malformed candidate state")
        if selected is not None:
            action = ACTIONS[0]
        elif status.startswith("HOLD") or status.startswith("RESEARCH_HOLD") \
                or status in ("MECHANISM-ONLY", "PROJECTION"):
            action = ACTIONS[1]
        elif refs and has_exact_law(candidate):
            action = ACTIONS[2]
        elif refs:
            action = ACTIONS[3]
        else:
            action = ACTIONS[4]
        tasks.append({
            "batch": "",
            "priority": str(ACTIONS.index(action) + 1),
            "semantic_name": name,
            "candidate_origin": origin,
            "source_status": status,
            "next_action": action,
            "source_records": str(refs),
            "proposal_ids": ",".join(proposals),
            "witness_state": "HOLD_NOT_RUN",
            "semantic_dedup_state": "HOLD_DEDUP_UNPROVEN",
        })
    tasks.sort(key=lambda row: (
        int(row["priority"]), row["semantic_name"].casefold(),
        row["candidate_origin"]
    ))
    for i, row in enumerate(tasks):
        row["batch"] = "batch-%03d" % (i // batch_size + 1)
    require(len(tasks) + len(already_accounted) == len(pending),
            "candidate conservation")
    require(len({r["semantic_name"].casefold() for r in tasks}) == len(tasks),
            "work item loss or duplication")
    return tasks, already_accounted


def write_tsv(path, tasks):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, delimiter="\t",
                                lineterminator="\n", extrasaction="raise")
        writer.writeheader()
        writer.writerows(tasks)


def run(root, out_dir, batch_size=64):
    root = root.resolve()
    catalog_path = safe_path(root, "knowledge/d10-candidate-database-v1.json")
    catalog_raw = catalog_path.read_bytes()
    catalog = json.loads(catalog_raw)
    # Reuse existing source SHA, ledger conservation, name-overlap and
    # coordinate-collision checks. Never bypass their fail-closed verdict.
    verify_catalog(catalog, root)
    pointer = json.loads(safe_path(root, "knowledge/d10-current-inventory.json").read_text())
    current = pointer["canonical_current"]
    invpath = safe_path(root, current["path"])
    invraw = invpath.read_bytes()
    require(git_blob(invraw) == current["git_blob"], "current inventory SHA")
    inventory = json.loads(invraw)
    residents = inventory["rows"]
    require(len(residents) == current["selected"], "selected count drift")
    placed = [r.get("coordinate") for r in residents if r.get("coordinate") is not None]
    ratified = sum(r.get("ratified_resident") is True for r in residents)
    require((len(placed), len(residents) - len(placed), ratified) ==
            (current["placed"], current["unplaced"], current["ratified"]),
            "current canonical accounting drift")
    require(inventory["capacity"] == 1024 and inventory["width"] == 10,
            "D10 width/capacity drift")
    tasks, already = compile_tasks(catalog["pending"], residents, batch_size)
    out_dir.mkdir(parents=True, exist_ok=True)
    all_path = out_dir / "all-work.tsv"
    write_tsv(all_path, tasks)
    batch_ids = list(dict.fromkeys(row["batch"] for row in tasks))
    outputs = {"all-work.tsv": hashlib.sha256(all_path.read_bytes()).hexdigest()}
    for batch in batch_ids:
        path = out_dir / (batch + ".tsv")
        write_tsv(path, [row for row in tasks if row["batch"] == batch])
        outputs[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    summary = {
        "schema": "d10-batch-work/v1",
        "authority": "RESEARCH-WORK-ONLY-NO-SELECTION-OR-RATIFICATION",
        "source_catalog_blob": git_blob(catalog_raw),
        "canonical_inventory_blob": current["git_blob"],
        "canonical_selected": len(residents),
        "canonical_unplaced": current["unplaced"],
        "canonical_remaining": 1024 - len(residents),
        "source_pending": len(catalog["pending"]),
        "already_transferred_by_exact_proposal": len(already),
        "still_pending_work": len(tasks),
        "batch_size": batch_size,
        "batches": len(batch_ids),
        "tasks_by_action": dict(sorted(Counter(r["next_action"] for r in tasks).items())),
        "files_sha256": outputs,
        "executed_witnesses_created": 0,
        "new_semantic_selections": 0,
        "new_coordinates": 0,
        "new_ratifications": 0,
    }
    require(sum(summary["tasks_by_action"].values()) == len(tasks),
            "action partition lost candidates")
    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    return summary


def self_test():
    current = [{"semantic_name": "A", "proposal_id": "D10P-A"}]
    pending = [
        {"semantic_name": "A", "proposals": ["D10P-A"], "selected": False,
         "ratified": False, "coordinate": None},
        {"semantic_name": "B", "proposals": ["D10P-B"], "selected": False,
         "ratified": False, "coordinate": None, "source_status": "pending-review",
         "observable_law": "law", "source_provenance": "source@sha"},
        {"semantic_name": "C", "proposals": [], "selected": False,
         "ratified": False, "coordinate": None, "source_status": "HOLD-D2"},
    ]
    tasks, moved = compile_tasks(pending, current, 1)
    require(moved == ["A"] and len(tasks) == 2, "selftest conservation")
    require([r["batch"] for r in tasks] == ["batch-001", "batch-002"],
            "selftest batching")
    require({r["semantic_name"]: r["next_action"] for r in tasks} ==
            {"B": ACTIONS[2], "C": ACTIONS[1]}, "selftest gate assignment")
    try:
        compile_tasks([pending[0], pending[0]], current)
    except ValueError:
        pass
    else:
        raise ValueError("D10_BATCH_BLOCKED: duplicate escaped")
    collision = dict(pending[0], proposals=["DIFFERENT"])
    tasks, moved = compile_tasks([collision], current)
    require(len(tasks) == 1 and not moved
            and tasks[0]["next_action"] == ACTIONS[0],
            "selftest name collision silently dropped")
    altered = dict(pending[1], selected=True)
    try:
        compile_tasks([altered], current)
    except ValueError:
        pass
    else:
        raise ValueError("D10_BATCH_BLOCKED: unproved admission escaped")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
        if args.output_dir is None:
            require(args.self_test, "output-dir required unless self-testing")
            print("D10-BATCH-SELFTEST PASS")
            return
        result = run(args.root, args.output_dir, args.batch_size)
        print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise SystemExit(str(error))


if __name__ == "__main__":
    main()
