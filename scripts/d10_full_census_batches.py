#!/usr/bin/env python3
"""Shard the entire F1-F4 census, preserving every source candidate ID.

Namesake rows stay separate: surface resemblance never proves equivalence.
This tool only schedules evidence work. It never issues PASS or ratifies.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILTER = ROOT / "knowledge/d10-filter"
IN_FILES = ("accepted-queue.tsv", "rejected.tsv", "escalated.tsv")
COLUMNS = (
    "batch", "priority", "candidate_id", "semantic_name", "prior_bucket",
    "prior_reason", "next_evidence_action", "donor_provenance",
    "source_pin", "has_semantic_law", "witness_state", "semantic_dedup_state",
)
TASKS = (
    "REPLAY_WITNESS_AND_BEHAVIORAL_DEDUP",
    "VERIFY_DONOR_PROVENANCE_PIN",
    "DEFINE_EXACT_SEMANTIC_LAW",
    "RESTORE_DONOR_PROVENANCE",
    "REPAIR_FAILED_ORACLE",
    "REVIEW_PROVED_DUPLICATE",
    "REVIEW_DEMONSTRATED_F4_CONFLICT",
    "REVIEW_UNKNOWN_HOLD",
    "OWNER_BULK_REVIEW_ONLY",
)


def require(ok, reason):
    if not ok:
        raise ValueError("D10_FULL_BATCH_BLOCKED: " + reason)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def action_for(row, bucket):
    if bucket == "accepted":
        return TASKS[8]
    if bucket == "escalated":
        return TASKS[6]
    reason = row["reason"]
    if reason in ("EXCLUDE_NO_WITNESS", "HOLD_NOT_RUN", "HOLD_DEDUP_UNPROVEN"):
        return TASKS[0]
    if reason == "HOLD_UNVERIFIED_PIN":
        return TASKS[1]
    if reason == "HOLD_NO_SEMANTIC_LAW":
        return TASKS[2]
    if reason == "EXCLUDE_NO_PROVENANCE":
        return TASKS[3]
    if reason == "REJECT_FAILED_WITNESS":
        return TASKS[4]
    if reason == "EXCLUDE_DUP":
        return TASKS[5]
    return TASKS[7]


def partition(partitions, batch_size):
    require(isinstance(batch_size, int) and batch_size > 0, "invalid batch size")
    seen = set()
    queue = []
    for bucket in ("accepted", "rejected", "escalated"):
        for row in partitions[bucket]:
            ident = row["candidate_id"]
            require(ident and ident not in seen, "duplicate or empty candidate identity")
            seen.add(ident)
            action = action_for(row, bucket)
            queue.append({
                "batch": "",
                "priority": str(TASKS.index(action) + 1),
                "candidate_id": ident,
                "semantic_name": row["semantic_name"],
                "prior_bucket": bucket,
                "prior_reason": row["reason"],
                "next_evidence_action": action,
                "donor_provenance": row["donor_provenance"],
                "source_pin": row["source_pin"],
                "has_semantic_law": str(bool(row["semantic_law"].strip())).lower(),
                "witness_state": row["witness_verdict"] or "HOLD_NOT_RUN",
                "semantic_dedup_state": row["semantic_dedup_certificate"] or "HOLD_DEDUP_UNPROVEN",
            })
    queue.sort(key=lambda r: (
        int(r["priority"]), r["candidate_id"], r["semantic_name"].casefold()
    ))
    for index, row in enumerate(queue):
        row["batch"] = "full-batch-%03d" % (index // batch_size + 1)
    require(len(queue) == len(seen), "conservation failure")
    return queue


def write_tsv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS, delimiter="\t",
                                lineterminator="\n", extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def run(root, output, batch_size=64):
    base = root.resolve() / "knowledge/d10-filter"
    summary = json.loads((base / "filter-run-summary.json").read_text(encoding="utf-8"))
    require(summary["schema"] == "d10-unified-filter-run/v1", "source summary schema")
    partitions = {}
    for filename, bucket in zip(IN_FILES, ("accepted", "rejected", "escalated")):
        path = base / filename
        raw = path.read_bytes()
        require(summary["files_sha256"][filename] == digest(raw),
                "input SHA drift: " + filename)
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t", strict=True)
            require(reader.fieldnames is not None
                    and all(name in reader.fieldnames for name in
                            ("candidate_id", "semantic_name", "semantic_law",
                             "donor_provenance", "source_pin", "reason",
                             "witness_verdict", "semantic_dedup_certificate")),
                    "input TSV schema: " + filename)
            rows = list(reader)
        require(all(None not in row and all(v is not None for v in row.values())
                    for row in rows), "malformed TSV: " + filename)
        partitions[bucket] = rows
    require({bucket: len(rows) for bucket, rows in partitions.items()}
            == summary["mechanical_partition"], "input partition count drift")
    queue = partition(partitions, batch_size)
    output.mkdir(parents=True, exist_ok=True)
    all_path = output / "full-work.tsv"
    write_tsv(all_path, queue)
    hashes = {"full-work.tsv": digest(all_path.read_bytes())}
    batches = sorted(set(r["batch"] for r in queue))
    for name in batches:
        path = output / (name + ".tsv")
        write_tsv(path, [r for r in queue if r["batch"] == name])
        hashes[path.name] = digest(path.read_bytes())
    result = {
        "schema": "d10-full-census-batches/v1",
        "authority": "PROOF-WORK-ONLY-NO-AUTOMATIC-D10-SELECTION",
        "source_inventory": summary["current_inventory"],
        "source_candidate_rows": len(queue),
        "batches": len(batches),
        "batch_size": batch_size,
        "action_counts": dict(sorted(Counter(r["next_evidence_action"] for r in queue).items())),
        "files_sha256": hashes,
        "ratifications": 0,
        "automatic_semantic_approvals": 0,
    }
    require(sum(result["action_counts"].values()) == len(queue), "batch count drift")
    (output / "summary.json").write_text(
        json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def self_test():
    base = dict(candidate_id="a", semantic_name="A", semantic_law="law",
                donor_provenance="knowledge/a:1", source_pin="a"*40,
                reason="EXCLUDE_NO_WITNESS", witness_verdict="",
                semantic_dedup_certificate="")
    partitions = {"accepted": [], "rejected": [base, dict(base, candidate_id="b",
                  semantic_name="A")], "escalated": []}
    queue = partition(partitions, 1)
    require(len(queue) == 2 and queue[0]["semantic_name"] == queue[1]["semantic_name"],
            "namesakes were incorrectly deduplicated")
    require([r["batch"] for r in queue] == ["full-batch-001", "full-batch-002"],
            "batching drift")
    require(all(r["next_evidence_action"] == TASKS[0] for r in queue),
            "missing witness classified as PASS")
    partitions["rejected"].append(dict(base, candidate_id="a"))
    try:
        partition(partitions, 64)
    except ValueError:
        pass
    else:
        raise ValueError("D10_FULL_BATCH_BLOCKED: duplicate-ID mutant escaped")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--self-test", action="store_true")
    options = parser.parse_args()
    try:
        if options.self_test:
            self_test()
        if options.output_dir is None:
            require(options.self_test, "--output-dir required")
            print("D10-FULL-BATCH-SELFTEST PASS")
        else:
            print(json.dumps(
                run(options.root, options.output_dir, options.batch_size),
                sort_keys=True, ensure_ascii=False))
    except (OSError, KeyError, TypeError, ValueError, csv.Error) as exc:
        raise SystemExit(str(exc))


if __name__ == "__main__":
    main()
