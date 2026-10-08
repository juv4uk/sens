#!/usr/bin/env python3
"""Reveal the NEXT canonical blocker after W8 chronology, without publishing T5.

The main auto resolver is never changed. Historical mode is used ONLY in a
disposable dry run to observe hypothetical second blockers for Git-SHA-verified
pre-D8 originals; same historical source bytes do not authorize legacy semantics.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
SCHEMA = "sens-w8-provenance-next-barrier/v1"

spec = importlib.util.spec_from_file_location(
    "sens_immutable_w8_audit", ROOT / "scripts/audit_w8_source_era.py")
if spec is None or spec.loader is None:
    raise RuntimeError("canonical immutable W8 auditor required")
origin = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = origin
spec.loader.exec_module(origin)


class TriageError(ValueError):
    pass


def source_git_blob(path: Path) -> str:
    payload = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload).hexdigest()


def next_barrier(reason: str) -> tuple[str, str]:
    """Classify the SECOND observed error, never guess a semantic successor."""
    m = re.search(r"legacy-unmapped SID8/Sens8 ([01]{8})", reason)
    if m:
        return "UNMAPPED_LEGACY_SID8", m.group(1)
    m = re.search(r"ambiguous W8 executable head ([01]{8})", reason)
    if m:
        return "STILL_W8_AMBIGUOUS", m.group(1)
    # D2 control words cannot be indexed lexical data words.
    if re.search(r"D2 word|structural control", reason):
        return "D2_STRUCTURE_UNPROVED", "D2"
    m = re.search(r"\bword\s+(\d+)\b", reason, re.I)
    if m:
        return "NON_BINARY_OR_UNTYPED", "word" + m.group(1)
    if re.search(r"print|host|I/O|read-all", reason, re.I):
        return "HOST_EFFECT_UNPROVED", "effect"
    if re.search(r"unbound|lambda|binding|dynamic|passthrough", reason, re.I):
        return "BINDING_UNPROVED", "binding"
    return "OTHER_UNPROVED", "other"


def join_provenance_and_legacy(proof: dict, replay: dict, root: Path) -> dict:
    if proof.get("schema") != origin.SCHEMA:
        raise TriageError("wrong historical source provenance schema")
    if proof.get("baseline_pre_d8_commit") != origin.BASELINE:
        raise TriageError("source Git chronology uses an unreviewed baseline")
    if replay.get("mode") != "dry-run" or replay.get("source_era") != "legacy":
        raise TriageError("second barrier requires only isolated LEGACY dry-run")
    if not replay.get("only_unpaired"):
        raise TriageError("second barrier must exclude all already-paired sources")
    summary = replay.get("summary", {})
    if summary.get("files_written") != 0:
        raise TriageError("legacy replay must never publish a physical .sens")
    rows = replay.get("files")
    if not isinstance(rows, list) or len(rows) != summary.get("files_seen"):
        raise TriageError("incomplete canonical legacy dry-run ledger")
    lookup = {}
    for row in rows:
        path = row.get("path")
        if not isinstance(path, str) or path in lookup:
            raise TriageError("duplicate or malformed replay source")
        lookup[path] = row
    approved = []
    already_seen = set()
    all_first_w8 = proof.get("sources")
    if not isinstance(all_first_w8, list):
        raise TriageError("source audit has no original-file list")
    for evidence in all_first_w8:
        path = evidence.get("path")
        if not isinstance(path, str) or path in already_seen:
            raise TriageError("duplicate or malformed W8 source")
        already_seen.add(path)
        if evidence.get("provenance") != "SAME_BLOB_BEFORE_D8_RATIFICATION":
            continue
        sha = evidence.get("source_git_blob_sha")
        if (Path(path).is_absolute() or ".." in Path(path).parts
                or not path.endswith(".lisp") or not isinstance(sha, str)
                or not re.fullmatch(r"[0-9a-f]{40}", sha)):
            raise TriageError("unsafe or unpinned W8 historical source")
        if not (root / path).is_file() or (root / path).is_symlink():
            raise TriageError("historical source disappeared or became a link")
        if source_git_blob(root / path) != sha:
            raise TriageError("source SHA drift between provenance and canonical replay")
        row = lookup.get(path)
        if row is None or row.get("status") not in ("blocked", "would-write"):
            raise TriageError("historical original missing from legacy dry-run")
        if row["status"] == "would-write":
            family, coordinate = "MECHANICAL_CANDIDATE_ONLY", "candidate"
            next_reason = "T5 mechanical packing only; independent semantic oracle NOT proven"
        else:
            next_reason = str(row.get("reason", ""))
            if not next_reason:
                raise TriageError("legacy BLOCK has no auditable next reason")
            family, coordinate = next_barrier(next_reason)
        approved.append({
            "path": path,
            "source_git_blob_sha": sha,
            "w8_first_blocker": evidence["w8_first_blocker"],
            "next_family": family,
            "next_coordinate": coordinate,
            "next_reason": next_reason,
            "status": "HYPOTHETICAL_LEGACY_DRY_RUN_ONLY",
            "current_source_era_permission": False,
            "current_semantic_oracle": "NOT_VERIFIED",
        })
    count_same = proof.get("summary", {}).get("SAME_BLOB_BEFORE_D8_RATIFICATION")
    if count_same != len(approved):
        raise TriageError("missing SHA-pinned pre-D8 originals in successor triage")
    approved.sort(key=lambda r: (r["next_family"], r["next_coordinate"], r["path"]))
    buckets: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for item in approved:
        buckets[(item["next_family"], item["next_coordinate"])].append(item)
    cohorts = [
        {
            "family": family, "coordinate": coordinate,
            "count": len(members),
            "source_paths": [member["path"] for member in members],
            "example_paths": [member["path"] for member in members[:5]],
        }
        for (family, coordinate), members in sorted(
            buckets.items(), key=lambda t: (-len(t[1]), t[0][0], t[0][1])
        )
    ]
    return {
        "schema": SCHEMA,
        "mode": "READ_ONLY_HYPOTHETICAL_LEGACY_NO_AUTHORIZATION",
        "historical_git_baseline": origin.BASELINE,
        "summary": {
            "w8_first_blocked_originals": len(all_first_w8),
            "chronology_proven_same_blob": len(approved),
            "hypothetical_mechanical_candidates_only": sum(
                item["next_family"] == "MECHANICAL_CANDIDATE_ONLY" for item in approved
            ),
            "hypothetical_second_blocked": sum(
                item["next_family"] != "MECHANICAL_CANDIDATE_ONLY" for item in approved
            ),
            "next_barrier_cohorts": len(cohorts),
            "current_semantic_admissions": 0,
            "physical_outputs_created": 0,
        },
        "next_barrier_cohorts": cohorts,
        "sources": approved,
        "interpretation": (
            "Source byte age is not original opcode semantics. Hypothetical "
            "legacy dry-run is not authorization to select source-era legacy "
            "on a real migration; no original executable/oracle parity admitted."
        ),
    }



SOURCE_KINDS = frozenset({
    "UNCLASSIFIED_NEEDS_SOURCE_PROOF",
    "NONPROGRAM_DATA_REVIEWED",
    "ARCHIVED_BENCHMARK_NONPROGRAM",
})
NONPROGRAM_KINDS = frozenset({
    "NONPROGRAM_DATA_REVIEWED", "ARCHIVED_BENCHMARK_NONPROGRAM",
})


def add_owner_reviewed_source_scope(next_report: dict, census: dict) -> dict:
    """Separate real original-source DATA work from still-unproved programs.

    This is a second, SHA-concordant JOIN with the existing canonical read-only
    corpus. No source-kind inference from filenames, error text or opcode width.
    Existing raw hypothetical legacy cohorts remain intact for audit.
    """
    summary = census.get("summary")
    blocked = census.get("blocked_sources")
    mechanical = census.get("mechanical_candidates")
    if (not isinstance(summary, dict) or not isinstance(blocked, list)
            or not isinstance(mechanical, list)):
        raise TriageError("canonical source-scope original ledger unavailable")
    if (len(blocked) != summary.get("blocked")
            or len(mechanical) != summary.get("mechanical_candidates")
            or len(blocked) + len(mechanical) != summary.get("scanned")
            or summary.get("original_unpaired_sources_scanned") != summary.get("scanned")):
        raise TriageError("canonical source-scope original count disagreement")
    if census.get("source_era") != "auto" or (
        summary.get("physical_outputs_created") != 0
        or summary.get("original_unpaired_executables_migrated_by_this_tool") != 0
    ):
        raise TriageError("source-kind authority must be no-write source-era auto")
    # An immutable archived file can become *mechanically* representable
    # after a newly audited historical successor is linked. It remains DATA,
    # never an executable admission. Do not lose it merely because its first
    # status moved from BLOCKED to CANDIDATE_NOT_ADMITTED.
    by_path: dict[str, dict] = {}
    for expected_status, rows in (
            ("BLOCKED", blocked), ("CANDIDATE_NOT_ADMITTED", mechanical)):
        for row in rows:
            if not isinstance(row, dict):
                raise TriageError("canonical source row is malformed")
            path = row.get("path")
            sha = row.get("source_git_blob_sha")
            scope = row.get("source_scope")
            if not isinstance(path, str) or path in by_path:
                raise TriageError("duplicate/malformed canonical source scope")
            if (row.get("status") != expected_status
                    or row.get("same_stem_sens_already_exists") is not False
                    or row.get("independent_semantic_oracle_passed") is not False
                    or row.get("source_is_executable_proven") is not False
                    or not isinstance(sha, str)
                    or not re.fullmatch(r"[0-9a-f]{40}", sha)
                    or scope not in SOURCE_KINDS):
                raise TriageError("unapproved original SHA, semantic admission or source scope")
            by_path[path] = row
    # Reviewed DATA entries must have independent source-specific owner
    # records in the canonical manifest overlay, not just a forged row label.
    reviewed = census.get("reviewed_nonprogram_sources")
    if not isinstance(reviewed, list):
        raise TriageError("missing owner-reviewed original DATA ledger")
    reviewed_by_path: dict[str, str] = {}
    for row in reviewed:
        if not isinstance(row, dict) or not isinstance(row.get("path"), str):
            raise TriageError("malformed owner-reviewed DATA record")
        path = row["path"]
        if path in reviewed_by_path:
            raise TriageError("duplicate owner-reviewed DATA source")
        if (row.get("source_class") != "NONPROGRAM_DATA_REVIEWED"
                or row.get("automatic_sens_companion") is not False
                or row.get("semantic_oracle_admitted") is not False):
            raise TriageError("unapproved executable semantics in DATA manifest")
        reviewed_by_path[path] = row.get("source_git_blob_sha")
    if len(reviewed_by_path) != summary.get("classified_nonprogram"):
        raise TriageError("reviewed DATA manifest total changed")
    for path, sha in reviewed_by_path.items():
        canonical = by_path.get(path)
        if canonical is None or canonical["source_git_blob_sha"] != sha or (
                canonical["source_scope"] != "NONPROGRAM_DATA_REVIEWED"):
            raise TriageError("DATA classification Git SHA differs from canonical original")
    for path, row in by_path.items():
        if row["source_scope"] == "NONPROGRAM_DATA_REVIEWED" and path not in reviewed_by_path:
            raise TriageError("DATA source lacks an owner-reviewed SHA-pinned manifest")
    # Do not guess ARCHIVED from a generic benchmarks/ prefix. Only the
    # canonical scope law can classify one exact historical snapshot path.
    from migration_source_scope import archived_benchmark_source
    archived_count = 0
    for path, row in by_path.items():
        law = archived_benchmark_source(path)
        if law != (row["source_scope"] == "ARCHIVED_BENCHMARK_NONPROGRAM"):
            raise TriageError("archive source-scope contradicts canonical path law")
        archived_count += int(law)
    if archived_count != summary.get("archived_benchmark_data_sources"):
        raise TriageError("archived source-scope total changed")

    source_rows = next_report.get("sources")
    if not isinstance(source_rows, list) or len(source_rows) != next_report.get(
            "summary", {}).get("chronology_proven_same_blob"):
        raise TriageError("missing next-barrier historical source rows")
    mapped = []
    seen: set[str] = set()
    cohorts: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for record in source_rows:
        path = record.get("path")
        if not isinstance(path, str) or path in seen:
            raise TriageError("duplicate/malformed historical source row")
        seen.add(path)
        canonical = by_path.get(path)
        if (canonical is None
                or canonical["source_git_blob_sha"] != record.get("source_git_blob_sha")):
            raise TriageError("historical next-barrier Git SHA differs from canonical source")
        kind = canonical["source_scope"]
        lane = ("DATA_CONTRACT_NO_EXECUTABLE_T5" if kind in NONPROGRAM_KINDS
                else "EXECUTABLE_OR_UNCLASSIFIED_NEEDS_ORACLE")
        member = {**record, "source_scope": kind, "work_lane": lane,
                  "release_admitted": False}
        mapped.append(member)
        cohorts[(lane, member["next_family"], member["next_coordinate"])].append(member)
    grouped = [
        {
            "work_lane": lane, "family": family, "coordinate": coordinate,
            "count": len(members),
            "original_sources": [
                {"path": r["path"], "source_git_blob_sha": r["source_git_blob_sha"]}
                for r in sorted(members, key=lambda r: r["path"])
            ],
            "status": "REVIEW_QUEUE_NO_SEMANTIC_ADMISSION",
        }
        for (lane, family, coordinate), members in sorted(
            cohorts.items(), key=lambda z: (-len(z[1]), z[0][0], z[0][1], z[0][2])
        )
    ]
    data_only = sum(x["work_lane"] == "DATA_CONTRACT_NO_EXECUTABLE_T5" for x in mapped)
    executable_unknown = len(mapped) - data_only
    if sum(x["count"] for x in grouped) != len(mapped):
        raise TriageError("source-kind partition lost a historical original")
    updated = dict(next_report)
    updated["sources"] = mapped
    updated["source_scope_next_barrier_cohorts"] = grouped
    updated["summary"] = {
        **next_report["summary"],
        "data_only_next_barrier_originals": data_only,
        "executable_or_unclassified_next_barrier_originals": executable_unknown,
        "source_scoped_next_barrier_cohorts": len(grouped),
    }
    updated["source_scope_policy"] = (
        "Existing owner-reviewed SHA-pinned DATA and archived BENCHMARK "
        "sources are DATA ONLY; remaining sources are UNCLASSIFIED, not "
        "certified executable. No automatic source-era or T5 publication."
    )
    return updated


def canonical_legacy_replay(repo: Path, td: Path) -> dict:
    report = td / "legacy-report.json"
    target = td / "no-binaries"
    args = [
        sys.executable, str(repo / "scripts/migrate-three-pass.py"), str(repo),
        "--out", str(target), "--report", str(report),
        "--foundation", str(repo / "knowledge/d1-d9-foundation.json"),
        "--dry-run", "--unpaired-only", "--source-era", "legacy",
    ]
    p = subprocess.run(args, cwd=repo, capture_output=True, text=True,
                       check=False, timeout=230)
    if p.returncode not in (0, 2) or not report.is_file():
        raise TriageError("canonical three-pass legacy preview missing/crashed: " +
                          p.stderr[-300:])
    result = json.loads(report.read_text(encoding="utf-8"))
    if target.exists() and list(target.rglob("*.sens")):
        raise TriageError("dry-run physically published a .sens")
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=ROOT)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    repo = args.repo.resolve()
    out = args.out.resolve()
    if out.is_relative_to(repo) or out.is_symlink():
        print("BLOCKED: report must remain outside repository", file=sys.stderr)
        return 2
    try:
        with tempfile.TemporaryDirectory(prefix="sens-w8-second-barrier-") as tmp:
            census = origin.original_census(repo)
            old = origin.tree_blobs(repo, origin.BASELINE)
            proof = origin.report(repo, census, old, origin.current_tracked_blobs(repo))
            replay = canonical_legacy_replay(repo, Path(tmp))
            result = join_provenance_and_legacy(proof, replay, repo)
            result = add_owner_reviewed_source_scope(result, census)
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            raise TriageError("will not overwrite existing report")
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
    except (OSError, TriageError, origin.EvidenceError, ValueError, subprocess.TimeoutExpired) as e:
        print("BLOCKED: " + str(e), file=sys.stderr)
        return 2
    print(json.dumps(result["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
