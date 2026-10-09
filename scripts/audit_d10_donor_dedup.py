#!/usr/bin/env python3
"""Read-only D10 donor source audit. A Lisp DEFINE is NOT a new D10 resident.

For genuine source-grounded research only: count definitions, ratified D1-D9
surface matches, and previously selected D10 source rows. Report unmatched
definitions for a separate semantic/manual review (never a candidate count).
No domain coordinates, no files written, no emitted .sens, no migration credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DONORS = {
    "lib/quantity.lisp": ("548bfc4092e8809a373d5397c6eafa884ac5ccef", 42),
    "lib/translation.lisp": ("6c3118daba896c64255efbb93c926a58d2f19829", 31),
    "lib/reason.lisp": ("dadc52a2f40f2f30ad77642898afb81980044c08", 37),
    "lib/si.lisp": ("2b94f1ea6d2fb05c084c3a0d863c14119a5ba11f", 29),
}
DEFINE = re.compile(r"^\(000010(?:01|11) ([^\s()]+)", re.MULTILINE)
SURFACE = re.compile(r"\((?:en|LISP)\s+([^\s()]+)\)")
SOURCE_ROW = {"SELECT-D10-CANDIDATE"}
SCHEMA = "sens-d10-source-dedup-triage/v1"


def blob_sha(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def definitions(content: str) -> list[tuple[str, int]]:
    # Both historical DEFINE and DEFINE-value words are present in actual
    # author libraries: reason.lisp uses 00001011, not 00001001.
    found = []
    for line_number, line in enumerate(content.splitlines(), 1):
        hit = DEFINE.match(line)
        if hit:
            found.append((hit.group(1), line_number))
    names = [name for name, _ in found]
    if len(names) != len(set(names)):
        raise ValueError("duplicate top-level source definition")
    return found


def domain_surfaces(root: Path) -> dict[str, list[str]]:
    """Human aliases indicate possible duplication; they NEVER prove behavior."""
    known: dict[str, set[str]] = {}
    for width in range(1, 10):
        path = root / "lib/domains" / f"d{width}.lisp"
        text = path.read_text(encoding="utf-8")
        for hit in SURFACE.finditer(text):
            known.setdefault(hit.group(1).lower(), set()).add(f"D{width}")
    return {k: sorted(v) for k, v in known.items()}


def previous_d10_source_rows(root: Path) -> dict[tuple[str, str], list[str]]:
    """Scan tracked manifests, not one cherry-picked harvest or old total."""
    inventory = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--", "knowledge/d10-*.json"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    known: dict[tuple[str, str], set[str]] = {}
    for raw_path in inventory.stdout.split(b"\0"):
        if not raw_path:
            continue
        rel = raw_path.decode("utf-8")
        candidate = root / rel
        if not candidate.is_file():
            raise ValueError("tracked D10 ledger missing: " + rel)
        data = json.loads(candidate.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            continue
        rows = data.get("rows", ())
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            source = row.get("source_file")
            name = row.get("source_name")
            selected = row.get("decision") in SOURCE_ROW or row.get("selected_d10_candidate") is True
            if (isinstance(source, str) and isinstance(name, str)
                    and selected):
                known.setdefault((source, name), set()).add(rel)
    return {key: sorted(v) for key, v in known.items()}


def audit(root: Path) -> dict:
    surfaces = domain_surfaces(root)
    harvested = previous_d10_source_rows(root)
    entries = []
    for path, (expected_sha, expected_count) in DONORS.items():
        src = root / path
        raw = src.read_bytes()
        if blob_sha(raw) != expected_sha:
            raise ValueError(f"source Git blob changed (fail closed): {path}")
        forms = definitions(raw.decode("utf-8"))
        if len(forms) != expected_count:
            raise ValueError(f"source DEFINE count changed: {path}")
        rows = []
        for name, line in forms:
            domain_matches = surfaces.get(name.lower(), [])
            manifests = harvested.get((path, name), [])
            if domain_matches:
                decision = "RATIFIED_D1_D9_NAME_COLLISION_REVIEW_BEHAVIOR"
            elif manifests:
                decision = "ALREADY_SELECTED_D10_SOURCE_ROW"
            else:
                decision = "UNREVIEWED_NOT_AUTOMATIC_D10_CANDIDATE"
            rows.append({
                "source_name": name, "source_line": line, "decision": decision,
                "d1_d9_surface_matches": domain_matches,
                "d10_prior_selected_harvest": manifests,
                "coordinate": None, "ratified": False,
            })
        entries.append({
            "source_file": path, "source_git_blob_sha": expected_sha,
            "definition_count": len(rows),
            "ratified_name_collisions": sum(bool(row["d1_d9_surface_matches"]) for row in rows),
            "prior_d10_source_selections": sum(
                bool(row["d10_prior_selected_harvest"])
                and not row["d1_d9_surface_matches"] for row in rows
            ),
            "still_unreviewed": sum(row["decision"].startswith("UNREVIEWED") for row in rows),
            "rows": rows,
        })
    return {
        "schema": SCHEMA,
        "status": "RESEARCH_CENSUS_ONLY__NO_SEMANTIC_SELECTION",
        "doctrine": "D10 one bitstream, 0 ratified; D2 alone governs structure",
        "no_new_candidates_admitted": True,
        "summary": {
            "donor_definitions": sum(x["definition_count"] for x in entries),
            "ratified_domain_surface_collisions": sum(x["ratified_name_collisions"] for x in entries),
            "already_selected_d10_source_rows": sum(x["prior_d10_source_selections"] for x in entries),
            "unreviewed_name_rows_not_new_semantics": sum(x["still_unreviewed"] for x in entries),
            "new_d10_meanings": 0,
            "original_executable_physical_migrations": 0,
        },
        "donors": entries,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--summary-only", action="store_true")
    args = ap.parse_args()
    result = audit(args.root.resolve())
    if args.summary_only:
        result = {k: v for k, v in result.items() if k != "donors"}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
