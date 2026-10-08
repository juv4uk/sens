#!/usr/bin/env python3
"""Audit RAW D10 donor symbols without awarding semantic residency.

The 39 independently SELECTED D10 language laws are in
knowledge/d10-library-harvest-v1.json. This NEW 102-entry evidence-only source
harvest must never overwrite those laws, allocate a D10 coordinate or add 102
to the authoritative selected count.

Only exact Git blob bytes, definition locations and status/provenance are
certified here; executable behavior and D1-D9 semantic dedup are NOT.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "knowledge/d10-library-source-symbols-v1.json"
SELECTED_LIBRARY = ROOT / "knowledge/d10-library-harvest-v1.json"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"
STATE = ROOT / "knowledge/d10-fill-v1-state.json"


def git_blob_sha1(content: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()


def validate(raw: dict, library: dict, inventory: dict, state: dict,
             root: Path = ROOT) -> dict:
    if (raw.get("schema") != "d10-library-harvest/v1"
            or raw.get("authority") != "#4013"
            or raw.get("status") != "RESEARCH-UNRATIFIED"
            or raw.get("law") !=
            "source-grounded candidate meanings only; NO D10 positions invented (positions are owner generator authority)"):
        raise ValueError("invalid raw source-symbol authority or D10 selection claim")
    if (library.get("schema") != "d10-library-harvest-v1/v1"
            or library.get("authority") != "#4026"
            or library.get("status") != "RESEARCH-UNRATIFIED"
            or len(library.get("rows", [])) != 39
            or library.get("accounting", {}).get("selected_d10_candidates") != 39):
        raise ValueError("original 39 independently selected meanings must not be overwritten")
    if (inventory.get("status") != "RESEARCH-UNRATIFIED-PARTIAL"
            or inventory.get("domain") != "D10"
            or inventory.get("width") != 10
            or inventory.get("capacity") != 1024):
        raise ValueError("unknown D10 semantic inventory authority")
    if (state.get("status") != "RESEARCH-UNRATIFIED"
            or state.get("target", {}).get("ratified_residents") != 0):
        raise ValueError("D10 has no ratified executable residents")
    official = state["target"]["selected_semantic_candidates"]
    if (len(inventory.get("rows", [])) != official
            or state["target"]["remaining_semantic_candidates"] != 1024 - official):
        raise ValueError("raw symbols must never alter selected/remaining semantic accounting")
    by_id = {r["stable_id"]: r for r in inventory["rows"]}
    if len(by_id) != official:
        raise ValueError("duplicate selected D10 stable ID")
    for old in library["rows"]:
        selected = by_id.get(old["stable_id"])
        if not selected or selected["semantic_name"] != old["semantic_name"]:
            raise ValueError("restored 39 selected meanings conflict with D10 semantic inventory")

    sources = raw.get("sources")
    rows = raw.get("candidates")
    if (not isinstance(sources, list) or len(sources) != 4
            or not isinstance(rows, list) or len(rows) != 102
            or raw.get("count") != len(rows)):
        raise ValueError("102 raw definitions and four immutable source donors required")

    file_lines: dict[str, list[str]] = {}
    for src in sources:
        if not isinstance(src, dict) or set(src) != {"path", "blob_sha"}:
            raise ValueError("untrusted source evidence row")
        path, pinned = src["path"], src["blob_sha"]
        if (not isinstance(path, str) or
                not path.startswith("lib/") or not path.endswith(".lisp") or
                "\\" in path or ".." in path.split("/") or
                not isinstance(pinned, str) or not re.fullmatch(r"[0-9a-f]{40}", pinned)
                or path in file_lines):
            raise ValueError("unsafe/duplicate D10 donor path or blob pin")
        disk = root / path
        if disk.is_symlink() or not disk.is_file():
            raise ValueError(f"D10 source missing/unsafe: {path}")
        content = disk.read_bytes()
        if git_blob_sha1(content) != pinned:
            raise ValueError(f"source Git blob drift: {path}")
        file_lines[path] = content.decode("utf-8").splitlines()

    counts = {path: 0 for path in file_lines}
    coordinates = set()
    selected_names = {r["semantic_name"].casefold() for r in inventory["rows"]}
    exact_duplicates = []
    constant_like = []
    for row in rows:
        if (not isinstance(row, dict) or
                set(row) != {"source", "blob_sha", "line", "name", "kind", "status"}
                or row["kind"] != "library-defined"
                or row["status"] != "research-unratified"):
            raise ValueError("raw harvest attempted coordinate, ratification or unknown schema")
        path = row["source"]
        name = row["name"]
        line = row["line"]
        if (path not in file_lines or
                row["blob_sha"] != next(s["blob_sha"] for s in sources if s["path"] == path)
                or not isinstance(name, str) or not name or
                not isinstance(line, int) or isinstance(line, bool) or
                line < 1 or line > len(file_lines[path]) or
                (path, line) in coordinates):
            raise ValueError(f"raw source identity, line or SHA mismatch: {path}:{line}")
        # A textual symbol definition is evidence, not a callable meaning.
        observed = file_lines[path][line - 1]
        if not re.match(r"^\s*\(00001001\s+" + re.escape(name) + r"(?=\s|\)|$)", observed):
            raise ValueError(f"no pinned Lisp source definition at {path}:{line} for {name}")
        counts[path] += 1
        coordinates.add((path, line))
        if name.casefold() in selected_names:
            exact_duplicates.append(name)
        if name.startswith("*") and name.endswith("*"):
            constant_like.append(name)

    if counts != {
        "lib/quantity.lisp": 42, "lib/translation.lisp": 31,
        "lib/si.lisp": 29, "lib/reason.lisp": 0,
    }:
        raise ValueError("donor harvest shape drift; reason requires separate source-form reader")
    return {
        "schema": "d10-raw-symbol-source-evidence-audit/v1",
        "status": "RAW_NOT_SEMANTICALLY_SELECTED",
        "raw_definitions_checked": len(rows),
        "source_counts": counts,
        "exact_name_duplicates_with_selected": len(exact_duplicates),
        "duplicate_names": sorted(exact_duplicates),
        "data_constant_like_names": sorted(constant_like),
        "selected_authority_unchanged": official,
        "ratified_residents": 0,
        "newly_selected_from_raw_harvest": 0,
        "next_gate": "behavior_oracle + D1-D9/D10 dedup + source ownership + human ratification",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, help="optional evidence-only result JSON")
    args = parser.parse_args()
    read = lambda p: json.loads(p.read_text(encoding="utf-8"))
    result = validate(read(RAW), read(SELECTED_LIBRARY), read(INVENTORY),
                      read(STATE))
    serialized = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
