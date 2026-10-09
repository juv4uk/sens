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
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
from migration_source_scope import scope
ARGS = [
    "--foundation", "knowledge/d1-d9-foundation.json",
    "--domain-surfaces", "crates/sens/src/domain_surface_registry_generated.rs",
    "--semantic-generated", "crates/sens/src/semantic_registry_generated.rs",
    "--semantic-registry", "crates/sens/src/semantic_registry.rs",
    "--necessary-forms", "crates/sens/src/eval/necessary_forms_generated.rs",
    "--historical-map", "contracts/core1-historical-sid-map.lisp",
    "--text7", "crates/sens/src/text7_projection_generated.rs",
]

# First blocking symptom only. This is scheduling metadata, NEVER evidence that
# a Lisp record is an executable, or that a domain law has been admitted.
BLOCKER_ACTIONS = {
    "w8-provenance": "Pin original source Git blob and prove legacy SID8 vs ratified current D8 before an explicit --source-era retry.",
    "host-effect": "Prove host I/O/effect semantics and independent old/current observable parity; do not guess PRINT mappings.",
    "unmapped-function": "Resolve function identity against owner-ratified D1-D9 and historical successor ledger; unknown stays BLOCKED.",
    "d2-or-domain-data": "Inspect non-binary token and classify executable vs schema/archive/typed D2-as-data before any conversion.",
    "lexical-binding": "Prove lambda/define variable binding and call-head scope; keep symbolic locals blocked without a law.",
    "numeric-law": "Prove exact-width numeric representation and operations before emitting any words.",
    "text-or-quote": "Prove D7 Text7/quoted-data handling and code/data boundaries; no raw text masquerading as a program.",
    "other-unproved": "Review exact source/reason and request one authoritative law plus Rust D2 and independent oracle proof.",
}


def blocker_family(reason: str) -> str:
    """Stable first-symptom classification; does NOT attest executable meaning."""
    if not isinstance(reason, str):
        raise ValueError("blocker reason must be text")
    r = reason.casefold()
    if ("ambiguous" in r or "ambiguity" in r or "двознач" in r) and any(
        marker in r for marker in ("w8", "d8", "8-bit", "eight-bit", "8 bit")
    ):
        return "w8-provenance"
    if any(marker in r for marker in ("print", "host-effect", "host effect", "unproven io", "host io")):
        return "host-effect"
    if any(marker in r for marker in ("binding", "bound", "lambda", "local variable", "dynamic call", "lexical")):
        return "lexical-binding"
    if any(marker in r for marker in ("numeric", "number-width", "integer literal", "number-law")):
        return "numeric-law"
    if any(marker in r for marker in ("text7", "quoted", "quote datum", "string literal", "text law")):
        return "text-or-quote"
    if (r.startswith("word ") or "non-bit" in r or "not a binary" in r
            or "structural d2" in r or "d2-as-data" in r):
        return "d2-or-domain-data"
    if any(marker in r for marker in ("unmapped", "unknown function", "unratified function",
                                       "function head", "missing successor")):
        return "unmapped-function"
    return "other-unproved"


def blocker_cohorts(blocked_sources: list[dict]) -> list[dict]:
    """Build exhaustive disjoint source-blob-locked cohorts in stable order."""
    by_family: dict[str, list[dict]] = {}
    seen: set[str] = set()
    for row in blocked_sources:
        path = row["path"]
        if path in seen:
            raise ValueError(f"duplicate unpaired original source in ledger: {path}")
        seen.add(path)
        if row["status"] != "BLOCKED" or row["same_stem_sens_already_exists"]:
            raise ValueError(f"not an unpaired BLOCKED source: {path}")
        family = blocker_family(row["reason"])
        by_family.setdefault(family, []).append({
            "path": path,
            "source_git_blob_sha": row["source_git_blob_sha"],
            "first_blocker": row["reason"],
        })
    return [
        {
            "family": family,
            "count": len(rows),
            "next_action": BLOCKER_ACTIONS[family],
            "original_sources": sorted(rows, key=lambda row: row["path"]),
            "status": "BLOCKED_NOT_ORACLE_ADMITTED",
        }
        for family, rows in sorted(by_family.items(),
                                   key=lambda item: (-len(item[1]), item[0]))
    ]



# Coordinate-specific first-blocker queues refine the existing broad family
# census. They preserve the family contract and never infer program meaning.
COORDINATE_OWNER = {
    "w8-provenance": "#4459",
    "unmapped-function": "#4577",
    "d2-or-domain-data": "#4460",
    "host-effect": "#4449",
    "lexical-binding": "#4449",
    "numeric-law": "#4449",
    "text-or-quote": "#4449",
    "other-unproved": "#4449",
}


def first_blocker_coordinate(reason: str, family: str) -> str:
    """Split major shared laws by EXACT historical word, not guessed semantics."""
    if family == "w8-provenance":
        match = re.search(r"\b([01]{8})\b", reason)
        return match.group(1) if match else "unknown-w8"
    if family == "d2-or-domain-data":
        match = re.search(r"\bword\s+(\d+)\b", reason, re.I)
        if match:
            return "word" + match.group(1)
        if "d2" in reason.casefold():
            return "D2"
    if family == "unmapped-function":
        match = re.search(r"\b([01]{8})\b", reason)
        if match:
            return match.group(1)
    return "other"


def blocker_coordinate_cohorts(blocked_sources: list[dict]) -> list[dict]:
    """Full SHA-pinned first-error partition, exact W8 and word-position slices.

    A source in this partition may have MANY later blockers. This is NOT
    an executable-program classification or independent oracle certification.
    """
    grouped: dict[tuple[str, str], list[dict]] = {}
    seen = set()
    for row in blocked_sources:
        path, sha = row["path"], row.get("source_git_blob_sha")
        if path in seen:
            raise ValueError("duplicate exact-coordinate original path")
        seen.add(path)
        if (row["status"] != "BLOCKED" or row["same_stem_sens_already_exists"]
                or not isinstance(sha, str)
                or not re.fullmatch(r"[0-9a-f]{40}", sha)):
            raise ValueError("coordinate cohort needs unpaired BLOCK and exact Git blob")
        family = blocker_family(row["reason"])
        coordinate = first_blocker_coordinate(row["reason"], family)
        grouped.setdefault((family, coordinate), []).append({
            "path": path,
            "source_git_blob_sha": sha,
            "first_blocker": row["reason"],
        })
    return [
        {
            "family": family, "coordinate": coordinate,
            "count": len(members), "owner_issue": COORDINATE_OWNER[family],
            "next_action": BLOCKER_ACTIONS[family],
            "status": "FIRST_BLOCK_ONLY_NOT_SEMANTICALLY_ADMITTED",
            "example_paths": sorted(m["path"] for m in members)[:5],
            "original_sources": sorted(members, key=lambda m: m["path"]),
        }
        for (family, coordinate), members in sorted(
            grouped.items(), key=lambda x: (-len(x[1]), x[0][0], x[0][1])
        )
    ]


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


# Reviewed non-executable Lisp records, sourced from separate SHA-pinned
# manifests (#4460). This overlays the RESEARCH work queue only; it does
# NOT modify SENS semantics or suppress the raw canonical migration scan.
NONPROGRAM_MANIFESTS = (
    ("domain-table", "knowledge/migration-nonprogram-domain-tables-2026-10-08.json", 9),
    ("comment-only-loader", "knowledge/migration-nonprogram-comment-only-loaders-2026-10-08.json", 2),
    ("isa", "knowledge/migration-nonprogram-isa-manifest-2026-10-08.json", 25),
    ("schema", "knowledge/migration-nonprogram-schema-manifest-2026-10-08.json", 21),
    ("evidence", "knowledge/migration-nonprogram-evidence-manifest-2026-10-08.json", 8),
    ("expr-record", "knowledge/migration-nonprogram-expr-records-2026-10-08.json", 13),
    ("knowledge-record", "knowledge/migration-nonprogram-knowledge-records-2026-10-08.json", 14),
)


def _checked_nonprogram_entry(root: Path, path: str, expected_sha: str) -> dict:
    """Reject invalid manifests, source changes and fake .sens admission."""
    rel = Path(path)
    if (rel.is_absolute() or ".." in rel.parts or "." in rel.parts
            or rel.suffix != ".lisp" or not rel.parts):
        raise ValueError(f"unsafe nonprogram source path: {path}")
    source = root / rel
    if not source.is_file() or source.is_symlink():
        raise ValueError(f"missing/symlink nonprogram source: {path}")
    if (len(expected_sha) != 40 or
            not all(c in "0123456789abcdef" for c in expected_sha)):
        raise ValueError(f"bad source Git SHA: {path}")
    actual = git_blob_sha(source)
    if actual != expected_sha:
        raise ValueError(f"nonprogram source drift: {path}: {actual} != {expected_sha}")
    if source.with_suffix(".sens").exists() or source.with_suffix(".sens").is_symlink():
        raise ValueError(f"nonprogram source has unproven physical pair: {path}")
    return {"path": rel.as_posix(), "source_git_blob_sha": actual,
            "source_class": "NONPROGRAM_DATA_REVIEWED",
            "semantic_oracle_admitted": False, "automatic_sens_companion": False}


def load_nonprogram_classification(root: Path) -> dict[str, dict]:
    """Read ONLY the reviewed fixed cohort manifests, no dynamic wildcard."""
    rows: dict[str, dict] = {}
    for cohort, name, expected_count in NONPROGRAM_MANIFESTS:
        manifest = root / name
        if not manifest.exists():
            continue  # independently merged cohorts may arrive later
        if not manifest.is_file() or manifest.is_symlink():
            raise ValueError(f"unsafe nonprogram manifest: {name}")
        record = json.loads(manifest.read_text(encoding="utf-8"))
        if (record.get("schema") != "sens-migration-nonprogram-manifest/1"
                or record.get("automatic_sens_companion") is not False
                or record.get("issue") != 4460):
            raise ValueError(f"nonprogram authority mismatch: {name}")
        entries = record.get("entries")
        if not isinstance(entries, list) or len(entries) != expected_count:
            raise ValueError(f"nonprogram cohort size changed: {name}")
        for item in entries:
            row = _checked_nonprogram_entry(
                root, item["path"], item["git_blob_sha1"]
            )
            path = row["path"]
            if path in rows:
                raise ValueError(f"duplicate nonprogram source path: {path}")
            # A fixed reviewed cohort is not permission to designate arbitrary
            # executable source as DATA.
            # These are old Lisp *load markers* containing comments only,
            # NOT zero-argument programs to encode as physical T5.
            # Exact path and SHA are both required; a crafted manifest cannot
            # exempt any other active library file from executable migration.
            if cohort == "comment-only-loader":
                if path not in {"lib/core2.lisp", "lib/surface/ukr.lisp"}:
                    raise ValueError(f"unreviewed comment-only loader path: {path}")
                lines = (root / path).read_text(encoding="utf-8").splitlines()
                if any(line.strip() and not line.lstrip().startswith(";") for line in lines):
                    raise ValueError(f"comment-only loader contains executable forms: {path}")
            if cohort == "domain-table" and path not in {
                    f"lib/domains/d{n}.lisp" for n in range(1, 10)}:
                raise ValueError(f"mis-scoped domain-table source: {path}")
            if cohort == "isa" and not path.startswith("lib/machine/isa/"):
                raise ValueError(f"mis-scoped ISA catalogue: {path}")
            if cohort == "schema" and not path.startswith(
                    ("contracts/", "lib/", "tests/fixtures/")):
                raise ValueError(f"mis-scoped schema data: {path}")
            if cohort == "evidence" and not path.startswith(
                    ("evidence/", "tests/fixtures/")):
                raise ValueError(f"mis-scoped evidence data: {path}")
            if cohort == "expr-record" and not path.startswith("tests/fixtures/"):
                raise ValueError(f"mis-scoped test-record envelope: {path}")
            if cohort == "knowledge-record" and (not path.startswith("knowledge/") or path.count("/") != 1):
                raise ValueError(f"mis-scoped knowledge data record: {path}")
            row["cohort"] = cohort
            rows[path] = row
    return rows


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
        "source_scope": scope(rel.as_posix()),
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
    return result


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
        # Overlay reviewed source-type manifests onto the RAW three-pass result.
        # Never mutate a migrator admission, source blob or physical file.
        classified = load_nonprogram_classification(root)
        by_path = {row["path"]: row for row in rows}
        if len(by_path) != len(rows):
            raise RuntimeError("duplicate original paths in migration ledger")
        for path, proof in classified.items():
            row = by_path.get(path)
            if row is None:
                raise RuntimeError(f"classified nonprogram absent from original census: {path}")
            if row["source_scope"] == "ARCHIVED_BENCHMARK_NONPROGRAM":
                raise RuntimeError(f"overlapping nonprogram source classifications: {path}")
            row["source_scope"] = proof["source_class"]
            row["classification_cohort"] = proof["cohort"]
            row["automatic_sens_companion"] = False
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
        archived = [r for r in unpaired if r["source_scope"] == "ARCHIVED_BENCHMARK_NONPROGRAM"]
        actionable = [r for r in unpaired if r["source_scope"] not in (
            "ARCHIVED_BENCHMARK_NONPROGRAM", "NONPROGRAM_DATA_REVIEWED")]
        blocked = len(rows) - len(candidates)
        if len(rows) != report["summary"]["files_seen"] or blocked != report["summary"]["files_blocked"]:
            raise RuntimeError("migrator report totals inconsistent")
        blocked_sources = sorted(
            (row for row in rows if row["status"] == "BLOCKED"),
            key=lambda row: row["path"],
        )
        cohorts = blocker_cohorts(blocked_sources)
        exact_cohorts = blocker_coordinate_cohorts(blocked_sources)
        # A separate actionable queue excludes reviewed DATA/archived
        # snapshots while preserving the complete raw BLOCK ledger.
        actionable_blocked = [r for r in blocked_sources if r["source_scope"]
                              not in ("NONPROGRAM_DATA_REVIEWED",
                                      "ARCHIVED_BENCHMARK_NONPROGRAM")]
        actionable_cohorts = blocker_cohorts(actionable_blocked)
        archived_sources = [r for r in rows
                            if r["source_scope"] == "ARCHIVED_BENCHMARK_NONPROGRAM"]
        if len(classified) + len(archived_sources) > len(rows):
            raise RuntimeError("nonprogram source accounting overlaps")
        if sum(x["count"] for x in exact_cohorts) != blocked:
            raise RuntimeError("exact coordinate cohort total differs from blocked corpus")
        if sum(cohort["count"] for cohort in cohorts) != blocked:
            raise RuntimeError("source blocker cohort totals inconsistent")
        if len({row["path"] for row in rows}) != len(rows):
            raise RuntimeError("duplicate original source in migration ledger")
        return {
            "schema": "sens-original-three-pass-eligibility/v1",
            "authority": "candidate discovery only; parser/codec parity is NOT oracle parity",
            "mode": "read-only canonical migrator dry-run",
            "summary": {
                "scanned": len(rows),
                "original_unpaired_sources_scanned": len(rows),
                "already_paired_sources_excluded": len(excluded),
                "classified_nonprogram": len(classified),
                "classified_nonprogram_by_cohort": {
                    cohort: sum(1 for item in classified.values()
                                if item["cohort"] == cohort)
                    for cohort, _, _ in NONPROGRAM_MANIFESTS
                    if any(item["cohort"] == cohort for item in classified.values())
                },
                "archived_benchmark_data_sources": len(archived_sources),
                "executable_or_unclassified_unpaired": (
                    len(rows) - len(classified) - len(archived_sources)
                ),
                "actionable_blocked_sources": len(actionable_blocked),
                "blocked": blocked,
                "blocker_family_counts": {cohort["family"]: cohort["count"] for cohort in cohorts},
                "exact_blocker_coordinates": len(exact_cohorts),
                "mechanical_candidates": len(candidates),
                "already_paired_candidates": len(candidates)-len(unpaired),
                "unpaired_candidates_needing_original_oracle": len(actionable),
                "archived_nonprogram_mechanical_candidates": len(archived),
                "nonarchive_mechanical_unproved": len(actionable),
                "original_unpaired_executables_migrated_by_this_tool": 0,
                "physical_outputs_created": 0,
            },
            "source_era": "auto",
            "authority": "original unpaired current D1-D9 source; candidate only; no oracle admission",
            "already_paired_sources_excluded": excluded,
            "reviewed_nonprogram_sources": sorted(
                classified.values(), key=lambda item: item["path"]),
            "actionable_blocker_cohorts": actionable_cohorts,
            "classification_rule": (
                "immutable DATA catalogues/records and archived benchmark "
                "snapshots are not executable program migrations; raw "
                "three-pass totals never change; remaining sources require "
                "owner-ratified semantic law and independent oracle proof"
            ),
            "mechanical_candidates": candidates,
            "archived_nonprogram_candidates": archived,
            "actionable_not_yet_oracle_proven_candidates": actionable,
            "blocked_sources": blocked_sources,
            "blocker_cohorts": cohorts,
            "exact_blocker_cohorts": exact_cohorts,
            "unpaired_blocker_sample": blocked_sources[:20],
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
