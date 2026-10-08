#!/usr/bin/env python3
"""Read-only, fail-closed SENS migration agent shard planner.

Consumes the CANONICAL "migrate.py candidates" report (original unpaired
source Git blobs), never attempts semantic translation or any filesystem writes
except the explicitly requested JSON plan. A work shard is NOT an admission
manifest; only independent source provenance + Rust oracle authorize .sens.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys

SCRIPTS = str(Path(__file__).resolve().parent)
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
from migration_source_scope import archived_benchmark_source

SOURCE_SCHEMA = "sens-original-three-pass-eligibility/v1"
OUTPUT_SCHEMA = "sens-t5-disjoint-agent-workshards/v1"
SHARD_STATUS = "UNCLAIMED__BLOCKED_NOT_ADMITTED"
MAX_FILES_PER_SHARD = 100
HEX = set("0123456789abcdef")


class PlanError(ValueError):
    pass


def checked_path(text: object) -> str:
    if not isinstance(text, str) or not text or "\\" in text:
        raise PlanError("invalid original source path")
    path = PurePosixPath(text)
    if (path.is_absolute() or path.suffix != ".lisp" or
            any(part in (".", "..") for part in text.split("/")) or
            path.as_posix() != text or "//" in text):
        raise PlanError(f"unsafe or non-Lisp path: {text!r}")
    return text


def checked_source(row: object, *, status: str) -> dict:
    if not isinstance(row, dict):
        raise PlanError("source row must be an object")
    path = checked_path(row.get("path"))
    sha = row.get("source_git_blob_sha")
    if (not isinstance(sha, str) or len(sha) != 40 or
            any(char not in HEX for char in sha)):
        raise PlanError(f"missing/invalid source Git blob pin: {path}")
    if row.get("same_stem_sens_already_exists", False) is not False:
        raise PlanError(f"source is already paired: {path}")
    if row.get("source_is_executable_proven", False) is not False or (
            row.get("independent_semantic_oracle_passed", False) is not False):
        raise PlanError(f"report claims unauthorized semantic proof: {path}")
    if status == "BLOCKED" and (not isinstance(row.get("reason"), str)
                                 or not row["reason"].strip()):
        raise PlanError(f"blocked source missing blocker: {path}")
    return {"path": path, "source_git_blob_sha": sha,
            **({"reason": row["reason"]} if status == "BLOCKED" else {})}


def _git_bytes(root: Path, *args: str) -> bytes:
    try:
        p = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PlanError("Git HEAD provenance unavailable") from exc
    if p.returncode:
        raise PlanError("Git HEAD provenance unavailable: " +
                        p.stderr.decode("utf-8", "replace")[-250:])
    return p.stdout


def _git_source_index(root: Path, *, staged: bool) -> dict[str, tuple[str, str]]:
    args = ("ls-files", "--stage", "-z") if staged else (
        "ls-tree", "-r", "-z", "--full-tree", "HEAD"
    )
    result: dict[str, tuple[str, str]] = {}
    for record in _git_bytes(root, *args).split(b"\0"):
        if not record:
            continue
        try:
            meta, path_bytes = record.split(b"\t", 1)
            fields = meta.decode("ascii").split()
            path = path_bytes.decode("utf-8")
            if staged:
                mode, sha, stage = fields
                if stage != "0":
                    raise PlanError("unmerged Git index entry: " + path)
            else:
                mode, kind, sha = fields
                if kind != "blob":
                    continue
        except (UnicodeDecodeError, ValueError) as exc:
            raise PlanError("invalid Git tree/index entry") from exc
        if not path.endswith(".lisp"):
            continue
        if path in result:
            raise PlanError("duplicate Git original source: " + path)
        result[path] = (mode, sha)
    return result


def assert_original_git_head_parity(root: Path, report: dict) -> None:
    """Check the entire candidate claim against HEAD, stage-0, and real bytes.

    An attacker may forge BOTH cohort and canonical JSON SHA fields consistently;
    their equality is not evidence that those bytes are in the Git commit.
    No .sens output, source writes, network or semantic admission occurs here.
    """
    root = root.resolve(strict=True)
    top = _git_bytes(root, "rev-parse", "--show-toplevel").decode("utf-8").strip()
    if Path(top).resolve() != root:
        raise PlanError("repository root must be the checked Git worktree root")
    head = _git_source_index(root, staged=False)
    index = _git_source_index(root, staged=True)
    rows = report.get("blocked_sources", []) + report.get("mechanical_candidates", [])
    if not isinstance(rows, list):
        raise PlanError("source report original lists must be arrays")
    if len(rows) != report.get("summary", {}).get("scanned"):
        raise PlanError("Git validation needs exhaustive original source inventory")
    seen: set[str] = set()
    for row in rows:
        item = checked_source(row, status=("BLOCKED" if row.get("status") == "BLOCKED"
                                          else "CANDIDATE"))
        name, pin = item["path"], item["source_git_blob_sha"]
        if name in seen:
            raise PlanError(f"duplicate original source Git claim: {name}")
        seen.add(name)
        original = head.get(name)
        staged_row = index.get(name)
        if original is None or staged_row is None:
            raise PlanError(f"source absent from Git HEAD or index: {name}")
        if original[0] not in ("100644", "100755") or staged_row[0] != original[0]:
            raise PlanError(f"source type/mode changed in Git index: {name}")
        if original[1] != pin or staged_row[1] != pin:
            raise PlanError(f"source Git HEAD/index blob SHA mismatch: {name}")
        local = root
        for component in PurePosixPath(name).parts:
            local = local / component
            if local.is_symlink():
                raise PlanError(f"symlinked original Git source: {name}")
        if not local.is_file():
            raise PlanError(f"source missing from working tree: {name}")
        data = local.read_bytes()
        actual = hashlib.sha1(
            b"blob " + str(len(data)).encode("ascii") + b"\0" + data
        ).hexdigest()
        if actual != pin:
            raise PlanError(f"source worktree drift from Git HEAD: {name}")


def build_plan(report: dict, max_files: int = 25) -> dict:
    if not isinstance(report, dict) or report.get("schema") != SOURCE_SCHEMA:
        raise PlanError("unexpected candidate report schema")
    if report.get("source_era") != "auto":
        raise PlanError("only conservative W8 source-era auto reports admitted")
    if "read-only" not in str(report.get("mode", "")):
        raise PlanError("candidate report was not proven read-only")
    if not 1 <= max_files <= MAX_FILES_PER_SHARD:
        raise PlanError("max_files must be in 1..100")
    summary = report.get("summary")
    if not isinstance(summary, dict):
        raise PlanError("report summary missing")
    if (summary.get("physical_outputs_created") != 0 or
            summary.get("original_unpaired_executables_migrated_by_this_tool") != 0):
        raise PlanError("candidate report claims physical output/admission")
    cohorts = report.get("blocker_cohorts")
    candidates = report.get("mechanical_candidates")
    if not isinstance(cohorts, list) or not isinstance(candidates, list):
        raise PlanError("need exhaustive blocker_cohorts and mechanical_candidates")

    # Canonical rows are the source of truth. A cohort is only a scheduling
    # projection: its 40-hex pin and first symptom MUST match the real ledger.
    # Matching totals/path exclusivity alone cannot detect a substituted SHA.
    authoritative = report.get("blocked_sources")
    if not isinstance(authoritative, list):
        raise PlanError("missing canonical blocked_sources ledger")
    original_by_path: dict[str, tuple[str, str]] = {}
    for row in authoritative:
        if not isinstance(row, dict) or row.get("status") != "BLOCKED":
            raise PlanError("canonical blocked source has invalid status")
        item = checked_source(row, status="BLOCKED")
        if item["path"] in original_by_path:
            raise PlanError(f"duplicate canonical blocked source: {item['path']}")
        original_by_path[item["path"]] = (item["source_git_blob_sha"], item["reason"])
    if len(original_by_path) != summary.get("blocked"):
        raise PlanError("canonical blocked source count disagrees")

    # This classification is supplied by the SHA-pinned owner-reviewed
    # manifests in the existing candidates report. Do not trust a standalone
    # cohort label or an arbitrary path glob as semantic/data authority.
    # Current main canonical reporter exposes reviewed_nonprogram_sources; the
    # former nonprogram_classification name remains accepted for older reports,
    # but two simultaneous sources of authority must be byte-equivalent.
    records = report.get("reviewed_nonprogram_sources",
                         report.get("nonprogram_classification", []))
    if ("reviewed_nonprogram_sources" in report and
            "nonprogram_classification" in report and
            report["reviewed_nonprogram_sources"] != report["nonprogram_classification"]):
        raise PlanError("conflicting nonprogram source classifications")
    if not isinstance(records, list):
        raise PlanError("reviewed nonprogram classification must be a list")
    if summary.get("classified_nonprogram", 0) != len(records):
        raise PlanError("reviewed nonprogram summary/count disagreement")
    reviewed: dict[str, dict] = {}
    for record in records:
        if not isinstance(record, dict):
            raise PlanError("reviewed nonprogram entry must be a record")
        item = checked_source(record, status="CANDIDATE")
        path = item["path"]
        if path in reviewed:
            raise PlanError(f"duplicate reviewed nonprogram: {path}")
        if (record.get("source_class") != "NONPROGRAM_DATA_REVIEWED"
                or record.get("automatic_sens_companion") is not False
                or record.get("semantic_oracle_admitted") is not False):
            raise PlanError(f"unreviewed or executable data classification: {path}")
        canonical = original_by_path.get(path)
        if canonical is None or canonical[0] != item["source_git_blob_sha"]:
            raise PlanError(f"reviewed data source not in canonical blocked ledger or stale Git SHA: {path}")
        source_row = next(row for row in authoritative if row["path"] == path)
        # Reporter v1 overlays reviewed semantics onto source_scope, while
        # a historical candidate shape used source_class. Never trust a
        # classification that contradicts either field if both are present.
        source_kind = source_row.get("source_scope", source_row.get("source_class"))
        if (source_kind != "NONPROGRAM_DATA_REVIEWED"
                or (source_row.get("source_class", source_kind)
                    != "NONPROGRAM_DATA_REVIEWED")
                or source_row.get("automatic_sens_companion") is not False):
            raise PlanError(f"canonical original does not confirm nonprogram policy: {path}")
        reviewed[path] = item

    # A frozen historical benchmark is archive evidence even if its old
    # `(print 0)` becomes mechanically parseable after successor repairs.
    # Verify the claimed source scope against the already-merged path law.
    archives: dict[str, dict] = {}
    for row in [*authoritative, *candidates]:
        path = checked_path(row.get("path"))
        is_archive = archived_benchmark_source(path)
        if is_archive:
            if row.get("source_scope") != "ARCHIVED_BENCHMARK_NONPROGRAM":
                raise PlanError(f"archived source scope missing: {path}")
            item = checked_source(row, status=("BLOCKED" if row.get("status") == "BLOCKED"
                                               else "CANDIDATE"))
            if path in reviewed or path in archives:
                raise PlanError(f"archived/nonprogram source overlaps or duplicates: {path}")
            archives[path] = item
        elif row.get("source_scope") == "ARCHIVED_BENCHMARK_NONPROGRAM":
            raise PlanError(f"forged archive scope for active source: {path}")
    if ("archived_benchmark_data_sources" in summary and
            summary["archived_benchmark_data_sources"] != len(archives)):
        raise PlanError("archived source total disagrees with canonical report")

    seen: set[str] = set()
    groups: list[tuple[str, str, list[dict]]] = []
    sum_blocked = 0
    for cohort in cohorts:
        if not isinstance(cohort, dict):
            raise PlanError("cohort entry must be object")
        family = cohort.get("family")
        if (not isinstance(family, str) or not family or
                not all(c.isalnum() or c == "-" for c in family)):
            raise PlanError("invalid family tag")
        if cohort.get("status") != "BLOCKED_NOT_ORACLE_ADMITTED":
            raise PlanError(f"non-blocked cohort: {family}")
        source_rows = cohort.get("original_sources")
        if (not isinstance(source_rows, list) or not source_rows or
                cohort.get("count") != len(source_rows)):
            raise PlanError(f"invalid cohort count: {family}")
        action = cohort.get("next_action")
        if not isinstance(action, str) or not action.strip():
            raise PlanError(f"missing concrete next action: {family}")
        members = []
        for row in source_rows:
            if not isinstance(row, dict):
                raise PlanError("malformed cohort source")
            candidate = dict(row)
            candidate["reason"] = row.get("first_blocker")
            item = checked_source(candidate, status="BLOCKED")
            if item["path"] in seen:
                raise PlanError(f"duplicate source path: {item['path']}")
            canonical = original_by_path.get(item["path"])
            if canonical is None:
                raise PlanError(f"cohort source missing in canonical ledger: {item['path']}")
            if (item["source_git_blob_sha"], item["reason"]) != canonical:
                raise PlanError(f"cohort Git SHA or first blocker differs from canonical ledger: {item['path']}")
            seen.add(item["path"])
            members.append(item)
        sum_blocked += len(members)
        active = [item for item in members if item["path"] not in reviewed and item["path"] not in archives]
        if active:
            groups.append((family, action, sorted(active, key=lambda x: x["path"])))

    if seen != set(original_by_path):
        raise PlanError("cohorts do not cover canonical blocked sources exactly")

    pending = []
    archived_candidates = []
    for row in candidates:
        if not isinstance(row, dict) or row.get("status") != "CANDIDATE_NOT_ADMITTED":
            raise PlanError("mechanical candidate claims admission or invalid state")
        item = checked_source(row, status="CANDIDATE")
        if item["path"] in seen:
            raise PlanError(f"candidate duplicates blocked source: {item['path']}")
        seen.add(item["path"])
        if item["path"] in archives:
            archived_candidates.append(item)
        else:
            pending.append(item)
    if reviewed:
        groups.append(("reviewed-nonprogram-data",
            "Owner-reviewed immutable schema/ISA/evidence/expr records need a DATA format contract; NEVER publish or count as executable .sens migration.",
            sorted(({"path": path, "source_git_blob_sha": item["source_git_blob_sha"]}
                    for path, item in reviewed.items()), key=lambda x: x["path"])))
    if archives:
        groups.append(("archived-benchmark-data",
            "Frozen historical performance snapshots are NONPROGRAM evidence; preserve original bytes/measurements, NEVER publish executable .sens.",
            sorted(archives.values(), key=lambda x: x["path"])))
    if pending:
        groups.append(("oracle-pending",
            "Independent source-law, Rust D2 parser, behavior oracle and file SHA required; never publish on mechanical parity alone.",
            sorted(pending, key=lambda x: x["path"])))

    if (sum_blocked != summary.get("blocked") or
            len(pending) + len(archived_candidates) != summary.get("mechanical_candidates") or
            len(seen) != summary.get("original_unpaired_sources_scanned") or
            len(seen) != summary.get("scanned")):
        raise PlanError("exhaustive source/candidate counts disagree")
    # Three disjoint census classes; archived mechanical DATA is neither
    # blocked-source status nor executable candidate awaiting an oracle.
    # Never erase it just to make the headline blocked+pending sum match.
    if len(seen) != sum_blocked + len(pending) + len(archived_candidates):
        raise PlanError("archived mechanical candidate lost in source partition")
    if summary.get("unpaired_candidates_needing_original_oracle") != len(pending):
        raise PlanError("unpaired oracle candidate total does not match")
    if summary.get("already_paired_candidates") != 0:
        raise PlanError("paired candidates cannot enter original backlog")

    shards = []
    for family, action, entries in sorted(groups, key=lambda g: (-len(g[2]), g[0])):
        for i in range(0, len(entries), max_files):
            group = entries[i:i + max_files]
            shard_id = f"{family}-{(i // max_files) + 1:03d}"
            digest = hashlib.sha256()
            for item in group:
                digest.update(item["path"].encode("utf-8") + b"\0")
                digest.update(item["source_git_blob_sha"].encode("ascii") + b"\n")
            is_data = family in ("reviewed-nonprogram-data", "archived-benchmark-data")
            shards.append({
                "shard_id": shard_id, "family": family,
                "status": ("UNCLAIMED__NONPROGRAM_DATA_ONLY" if is_data else SHARD_STATUS),
                "claimed_by": None, "source_count": len(group),
                "sources": group, "input_sources_sha256": digest.hexdigest(),
                "next_action": action,
                "claim_template": f"CLAIM: {shard_id} / repo=juv4uk/sens / owner=AGENT / branch=BRANCH / PR=PENDING",
                "release_gate": ("DATA_CONTRACT_NO_EXECUTABLE_T5" if is_data
                                 else "NO_OUTPUT_UNTIL_INDEPENDENT_SEMANTIC_ORACLE"),
            })
    if sum(x["source_count"] for x in shards) != len(seen):
        raise PlanError("shards did not cover every original source")
    return {
        "schema": OUTPUT_SCHEMA,
        "source_schema": SOURCE_SCHEMA,
        "source_era": "auto",
        "mode": "NO_WRITE_NO_AUTO_ASSIGN_NO_ORACLE_CLAIMS",
        "summary": {
            "original_unpaired": len(seen),
            "blocked": sum_blocked,
            "mechanical_pending_oracle": len(pending),
            "archived_mechanical_nonprogram_originals": len(archived_candidates),
            "reviewed_nonprogram_originals": len(reviewed),
            "archived_benchmark_nonprogram_originals": len(archives),
            "executable_or_unclassified_originals": len(seen) - len(reviewed) - len(archives),
            "shards": len(shards),
            "files_per_shard_limit": max_files,
            "claimed": 0,
            "admitted": 0,
        },
        "shards": shards,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidates", type=Path, required=True,
                    help="JSON from scripts/migrate.py candidates --report")
    ap.add_argument("--out", type=Path, required=True,
                    help="deterministic exclusive work-shard plan, never .sens bytes")
    ap.add_argument("--max-files", type=int, default=25)
    ap.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1],
                    help="exact Git checkout whose HEAD, index and bytes must match every source")
    args = ap.parse_args(argv)
    if args.candidates.resolve() == args.out.resolve():
        print("BLOCKED: never overwrite original candidate report", file=sys.stderr)
        return 2
    try:
        candidates = json.loads(args.candidates.read_text(encoding="utf-8"))
        plan = build_plan(candidates, args.max_files)
        assert_original_git_head_parity(args.repo_root, candidates)
    except (OSError, ValueError, UnicodeError) as exc:
        print(f"BLOCKED: cannot make safe migration agent work shards: {exc}", file=sys.stderr)
        return 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.out.exists() or args.out.is_symlink():
        print("BLOCKED: output already exists; agent work plan must be new", file=sys.stderr)
        return 2
    # Exclusive creation; never clobber report or another agent's plan.
    try:
        with args.out.open("x", encoding="utf-8") as handle:
            json.dump(plan, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
    except OSError as exc:
        print(f"BLOCKED: cannot create plan: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(plan["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
