#!/usr/bin/env python3
"""Expose actual old-source candidates from the existing fail-closed T5 census.

Read-only. A parse/codec-admissible dry-run is NOT semantic admission:
only independent source-law and Rust oracle parity can authorize publication.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MIGRATOR = ROOT / "scripts/migrate-three-pass.py"
ARGS = [
    "--foundation", "knowledge/d1-d9-foundation.json",
    "--domain-surfaces", "crates/sens/src/domain_surface_registry_generated.rs",
    "--semantic-generated", "crates/sens/src/semantic_registry_generated.rs",
    "--semantic-registry", "crates/sens/src/semantic_registry.rs",
    "--necessary-forms", "crates/sens/src/eval/necessary_forms_generated.rs",
    "--historical-map", "contracts/core1-historical-sid-map.lisp",
    "--text7", "crates/sens/src/text7_projection_generated.rs",
]

def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def categorize(row: dict, root: Path) -> dict:
    rel = Path(row["path"])
    if rel.is_absolute() or ".." in rel.parts or rel.suffix != ".lisp":
        raise ValueError("untrusted migrator path")
    source = root / rel
    if not source.is_file() or source.is_symlink():
        raise ValueError("source is not a regular tracked file")
    pair = source.with_suffix(".sens")
    result = {
        "path": rel.as_posix(),
        "source_git_blob_sha": git_blob_sha(source),
        "same_stem_sens_already_exists": pair.exists() or pair.is_symlink(),
        "source_is_executable_proven": False,
        "independent_semantic_oracle_passed": False,
    }
    if row["status"] == "would-write":
        result.update(
            status="CANDIDATE_NOT_ADMITTED",
            destination=rel.with_suffix(".sens").as_posix(),
            proposed_physical_sha256=row["physical_sha256"],
            proposed_typed_word_sha256=row["typed_word_sha256"],
            proposed_bytes=row["bytes"],
            proposed_words=row["semantic_word_count"],
            passes=row["passes"],
        )
    elif row["status"] == "blocked":
        result.update(status="BLOCKED", reason=row.get("reason", "unknown"))
    else:
        raise ValueError(f"unexpected dry-run status {row['status']!r}")
    # Preserve the exact FIRST failing token/coordinate. This is lexical
    # evidence for assigning work, never a proposed semantic translation.
    if row["status"] == "blocked":
        for field in ("token", "line", "column"):
            if field in row:
                result[field] = row[field]
    return result


# A blocker cohort is a FIRST-ERROR partition, not the set of all blockers
# in a program. One source may need several distinct ratified laws after the
# first blocker is resolved. In particular: do NOT call it "executable".
BLOCKER_LANES = {
    "W8_ERA_AMBIGUITY": ("#4459", "Prove original Git SHA / source era before choosing legacy or current D8"),
    "LEGACY_SUCCESSOR": ("#4577", "Prove exact owner-audited historical successor and current domain"),
    "D2_STRUCTURE_AS_DATA": ("#4462", "Prove whether structural D2 is misplaced data, not executable"),
    "NON_BINARY_WORD": ("#4460", "Separate source program from catalogue/schema/archive and admit literal law"),
    "HOST_EFFECT": ("#4449", "Prove host/IO effects and observable parity or retain BLOCK"),
    "TEXT7_OR_NUMERIC_LAW": ("#4449", "Prove exact typed text/number semantic law, not phoneme bytes as functions"),
    "OTHER_UNPROVEN": ("#4449", "Investigate exact source and independently verify its semantic role"),
}


def first_blocker_identity(row: dict) -> tuple[str, str]:
    """Conservative signature of the first BLOCK, never an admission."""
    reason = str(row.get("reason", ""))
    token = str(row.get("token", ""))
    match = re.search(r"ambiguous W8 executable head ([01]{8})", reason)
    if match:
        return "W8_ERA_AMBIGUITY", match.group(1)
    match = re.search(r"legacy-unmapped SID8/Sens8 ([01]{8})", reason)
    if match:
        return "LEGACY_SUCCESSOR", match.group(1)
    if re.search(r"D2 word [01]{2}|structural control only", reason):
        return "D2_STRUCTURE_AS_DATA", "D2"
    match = re.search(r"\bword (\d+):.*(?:exact|binary|0/1|0/1 word)", reason, re.I)
    if match:
        return "NON_BINARY_WORD", "word" + match.group(1)
    if re.search(r"\b(?:print|display|read-file|host|I/O|IO effect)\b", reason + " " + token, re.I):
        return "HOST_EFFECT", "side-effect"
    if re.search(r"Text7|D24|numeric|digit|number|character|string", reason, re.I):
        return "TEXT7_OR_NUMERIC_LAW", "typed-data"
    if re.search(r"legacy-unmapped|unratified|no current .*resident", reason, re.I):
        return "LEGACY_SUCCESSOR", "unmapped-surface"
    return "OTHER_UNPROVEN", "other"


def first_blocker_cohorts(rows: list[dict]) -> dict:
    """Cover every original blocked path exactly once with a SHA-pinned cohort.

    Cohort counts prioritize shared laws but do not mean any file is a
    convertible executable. No original is modified by this function.
    """
    blocked = [r for r in rows if r["status"] == "BLOCKED"]
    cohorts: dict[tuple[str, str], list[dict]] = {}
    for row in blocked:
        path = row["path"]
        sha = row.get("source_git_blob_sha")
        if not isinstance(path, str) or not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise ValueError("first blocker requires exact original file and Git blob SHA")
        if row.get("same_stem_sens_already_exists"):
            raise ValueError("paired file cannot enter an original blocker cohort")
        family, coordinate = first_blocker_identity(row)
        member = {"path": path, "source_git_blob_sha": sha, "reason": str(row.get("reason", "unknown"))}
        for field in ("token", "line", "column"):
            if field in row:
                member[field] = row[field]
        cohorts.setdefault((family, coordinate), []).append(member)
    all_paths = [member["path"] for members in cohorts.values() for member in members]
    if len(all_paths) != len(set(all_paths)) or len(all_paths) != len(blocked):
        raise ValueError("non-disjoint or incomplete original blocker partition")
    groups = []
    for (family, coordinate), members in sorted(
        cohorts.items(), key=lambda item: (-len(item[1]), item[0][0], item[0][1])
    ):
        ordered = sorted(members, key=lambda x: x["path"])
        issue, proof = BLOCKER_LANES[family]
        groups.append({
            "family": family, "coordinate": coordinate,
            "first_blocked_sources": len(ordered),
            "owner_issue": issue, "required_proof": proof,
            "example_paths": [x["path"] for x in ordered[:5]],
            "original_sources": ordered,
            "not_executable_or_semantic_admission": True,
        })
    families = {}
    for group in groups:
        families[group["family"]] = families.get(group["family"], 0) + group["first_blocked_sources"]
    return {
        "method": "FIRST failing lexical/domain constraint per exact original SHA; other later blockers not tested",
        "status": "TRIAGE_ONLY_NO_ORACLE",
        "first_blocked_total": len(blocked),
        "cohorts": groups,
        "source_counts_by_family": dict(sorted(families.items(), key=lambda x: (-x[1], x[0]))),
        "semantically_admitted_executable_sources": 0,
    }


def build_report(root: Path = ROOT) -> dict:
    with tempfile.TemporaryDirectory(prefix="sens-original-candidate-") as td:
        report_path = Path(td) / "migration.json"
        output_dir = Path(td) / "no-physical-output"
        proc = subprocess.run(
            [sys.executable, str(root / "scripts/migrate-three-pass.py"),
             str(root), "--out", str(output_dir), *ARGS,
             "--report", str(report_path), "--dry-run",
             "--unpaired-only", "--source-era", "auto"],
            cwd=root, capture_output=True, text=True, timeout=210
        )
        if not report_path.exists():
            raise RuntimeError(f"no dry-run report: {proc.stderr[-2000:]}")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if proc.returncode not in (0, 2):
            raise RuntimeError(f"dry-run crashed ({proc.returncode}): {proc.stderr[-2000:]}")
        if report["mode"] != "dry-run" or report["summary"]["files_written"] != 0:
            raise RuntimeError("unexpected write-capable migration report")
        if list(output_dir.rglob("*.sens")) if output_dir.exists() else []:
            raise RuntimeError("dry-run emitted physical output")
        rows = [categorize(row, root) for row in report["files"]]
        # The migrator's --unpaired-only contract must be enforced in BOTH
        # producer and consumer; counting a new paired canary as old progress is
        # a factual error, even if the physical bytes round-trip.
        if any(row["same_stem_sens_already_exists"] for row in rows):
            raise RuntimeError("unpaired original census included already paired .lisp")
        excluded = report.get("skipped_paired_paths", [])
        if len(excluded) != report["summary"].get("files_skipped_paired"):
            raise RuntimeError("paired-source exclusion count mismatch")
        if len(set(excluded)) != len(excluded):
            raise RuntimeError("duplicate paired-source exclusion")
        for excluded_path in excluded:
            rel = Path(excluded_path)
            if rel.is_absolute() or ".." in rel.parts or rel.suffix != ".lisp":
                raise RuntimeError("unsafe paired-source exclusion path")
            if not (root / rel.with_suffix(".sens")).is_file():
                raise RuntimeError("excluded pair is missing")
        candidates = [r for r in rows if r["status"] == "CANDIDATE_NOT_ADMITTED"]
        unpaired = [r for r in candidates if not r["same_stem_sens_already_exists"]]
        blocked = len(rows) - len(candidates)
        if len(rows) != report["summary"]["files_seen"] or blocked != report["summary"]["files_blocked"]:
            raise RuntimeError("migrator report totals inconsistent")
        blocker_partition = first_blocker_cohorts(rows)
        if blocker_partition["first_blocked_total"] != blocked:
            raise RuntimeError("first blocker partition count mismatch")
        return {
            "schema": "sens-original-three-pass-eligibility/v1",
            "authority": "candidate discovery only; parser/codec parity is NOT oracle parity",
            "mode": "read-only canonical migrator dry-run",
            "summary": {
                "scanned": len(rows),
                "original_unpaired_sources_scanned": len(rows),
                "already_paired_sources_excluded": len(excluded),
                "blocked": blocked,
                "mechanical_candidates": len(candidates),
                "already_paired_candidates": len(candidates)-len(unpaired),
                "unpaired_candidates_needing_original_oracle": len(unpaired),
                "original_unpaired_executables_migrated_by_this_tool": 0,
                "physical_outputs_created": 0,
                "blocker_cohorts": len(blocker_partition["cohorts"]),
            },
            "source_era": "auto",
            "authority": "original unpaired current D1-D9 source; candidate only; no oracle admission",
            "already_paired_sources_excluded": excluded,
            "first_blocker_partition": blocker_partition,
            "mechanical_candidates": candidates,
            "unpaired_blocker_sample": [r for r in rows if r["status"] == "BLOCKED" and not r["same_stem_sens_already_exists"]][:20],
            "required_evidence": [
                "prove original file is an executable SENS program, not an archive/catalogue",
                "prove exact historical function successor, D1/D2/w8 era and no host/IO effects",
                "run actual three-pass CLI to same-stem packed T5 without overwriting source",
                "Rust exact-domain oracle parity including wrong-domain negatives and digest",
                "merge only after focused and independent physical+syntax CI green",
            ],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = build_report()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary":result["summary"],"candidates":result["mechanical_candidates"]},ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
