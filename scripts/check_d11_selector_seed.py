#!/usr/bin/env python3
"""Mechanical audit of the D11 selector research seed.

This validates 11-bit candidate derivation and collision guards only.
It never ratifies D11 entries, reserves coordinates, or grants callability.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATHS = {
    "seed": "knowledge/d11-selector-seed.json",
    "d10_seed": "knowledge/d10-selector-seed.json",
    "d10_table": "lib/domains/d10.lisp",
    "d11_table": "lib/domains/d11.lisp",
    "d11_vocabulary": "knowledge/d11-testing-vocabulary-ratified.json",
}
DOMAIN_ROW = re.compile(
    r"^[ \t]*\((?P<bits>[^()\s]+)[ \t]+.*?\(LISP[ \t]+(?P<name>[^()\s]+)\)",
    re.MULTILINE,
)


class AuditError(ValueError):
    """One named, fail-closed inconsistency in the current D11 seed."""

    def __init__(self, test_id: str, detail: str) -> None:
        self.test_id = test_id
        self.detail = detail
        super().__init__(f"test_id={test_id} layer=d11-seed {detail}")


def require(ok: bool, test_id: str, detail: str) -> None:
    if not ok:
        raise AuditError(test_id, detail)


def git_blob_sha1(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


def load_documents(root: Path = ROOT) -> dict[str, Any]:
    """Read only the seed, its D10 parent evidence, and the current D11 test table."""
    documents: dict[str, Any] = {}
    for key in ("seed", "d10_seed", "d11_vocabulary"):
        rel = PATHS[key]
        try:
            documents[key] = json.loads((root / rel).read_bytes().decode("utf-8"))
        except FileNotFoundError as exc:
            raise AuditError("SOURCE_MISSING", f"missing {rel}") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AuditError("SOURCE_INVALID", f"cannot parse {rel}: {exc}") from exc

    for key in ("d10_table", "d11_table"):
        rel = PATHS[key]
        try:
            documents[key] = (root / rel).read_bytes().decode("utf-8")
        except FileNotFoundError as exc:
            raise AuditError("SOURCE_MISSING", f"missing {rel}") from exc
        except UnicodeDecodeError as exc:
            raise AuditError("SOURCE_INVALID", f"cannot decode {rel}: {exc}") from exc
    return documents


def parse_domain_rows(source: str, label: str) -> list[tuple[str, str]]:
    """Extract only one-line domain-table rows with an explicit LISP projection."""
    rows = [(m.group("bits"), m.group("name")) for m in DOMAIN_ROW.finditer(source)]
    require(bool(rows), "TABLE_EMPTY", f"{label} has no parseable domain-table rows")
    return rows


def validate_documents(documents: dict[str, Any]) -> dict[str, Any]:
    seed = documents["seed"]
    d10_seed = documents["d10_seed"]
    vocabulary = documents["d11_vocabulary"]

    require(seed.get("schema") == "sens.d11.selector-seed/v1",
            "SEED_SCHEMA", "expected sens.d11.selector-seed/v1")
    require(seed.get("status") == "RESEARCH_ONLY_NOT_RATIFIED" and
            seed.get("owner_decision") == "PENDING",
            "NOT_RESEARCH_ONLY",
            "candidate seed must remain RESEARCH_ONLY_NOT_RATIFIED with owner_decision=PENDING")
    require(seed.get("domain") == "D11" and seed.get("width") == 11 and
            seed.get("capacity") == 2048,
            "SEED_WIDTH", "D11 candidates require exact width 11 and capacity 2048")

    source = seed.get("source", {})
    require(source.get("parent_domain") == "D10" and
            source.get("ratified_parent_surface") == PATHS["d10_table"],
            "PARENT_SOURCE", "candidate parent must be the current D10 domain table")
    parent_pin = source.get("parent_git_blob")
    require(isinstance(parent_pin, str) and re.fullmatch(r"[0-9a-f]{40}", parent_pin),
            "PARENT_PIN_FORMAT", "historical parent Git blob pin must be a 40-digit SHA-1")
    require(source.get("d11_testing_vocabulary") == PATHS["d11_vocabulary"],
            "TEST_VOCAB_SOURCE", "seed must name the ratified D11 testing vocabulary")

    law = seed.get("law", {})
    require(law.get("candidate_only") is True and
            law.get("non_selector_parents") == "NO_EXTENSION" and
            law.get("coordinate_rule") == "11-bit candidate = 10-bit D10 selector coordinate || one bit",
            "CANDIDATE_LAW", "seed must remain a selector-only, candidate-only extension")
    gate = str(law.get("candidate_gate", ""))
    require(all(token in gate for token in (
        "NO_RATIFICATION", "NO_D11_CALLABILITY", "NO_ZIG_T5_ADMISSION"
    )), "CANDIDATE_GATE", "seed must explicitly deny ratification, callability and T5 admission")

    # Current D10 mapping is the evidence used for derivation. The seed's source
    # pin is historical provenance; drift is reported, not silently treated as
    # semantic failure if every parent is revalidated below.
    d10_rows = parse_domain_rows(documents["d10_table"], "lib/domains/d10.lisp")
    require(len(d10_rows) == 1024, "D10_TABLE_COUNT",
            f"expected 1024 current D10 rows; found {len(d10_rows)}")
    d10_map: dict[str, str] = {}
    d10_names: set[str] = set()
    for bits, name in d10_rows:
        require(re.fullmatch(r"[01]{10}", bits) is not None,
                "D10_WIDTH", f"invalid current D10 coordinate {bits!r}")
        require(bits not in d10_map, "D10_DUP_COORD", f"duplicate current D10 coordinate {bits}")
        require(name.casefold() not in d10_names, "D10_DUP_NAME",
                f"duplicate current D10 LISP name {name}")
        d10_map[bits] = name
        d10_names.add(name.casefold())

    parent_rows = d10_seed.get("rows")
    require(isinstance(parent_rows, list) and len(parent_rows) == 256,
            "PARENT_COUNT", "expected 256 selector parents in the pinned D10 generator seed")
    parents: dict[str, str] = {}
    parent_names: set[str] = set()
    for index, row in enumerate(parent_rows):
        bits, name = row.get("coordinate"), row.get("semantic_name")
        require(isinstance(bits, str) and re.fullmatch(r"[01]{10}", bits) is not None,
                "PARENT_WIDTH", f"parent row {index} must have exactly 10 bits")
        require(isinstance(name, str) and bool(name),
                "PARENT_NAME", f"parent row {index} has no semantic name")
        require(bits not in parents, "PARENT_DUP_COORD", f"duplicate selector parent {bits}")
        require(name.casefold() not in parent_names, "PARENT_DUP_NAME",
                f"duplicate selector parent name {name}")
        require(d10_map.get(bits) == name, "PARENT_NOT_CURRENT_D10",
                f"{bits} names {name} in seed but {d10_map.get(bits)!r} in current D10")
        require(name.endswith("R"), "PARENT_NAME_SHAPE",
                f"selector parent {name} does not end in the expected terminal R")
        parents[bits] = name
        parent_names.add(name.casefold())

    require(seed.get("source", {}).get("parent_git_blob") is not None,
            "PARENT_PIN_MISSING", "seed must retain its historical source pin")
    current_d10_blob = git_blob_sha1(documents["d10_table"].encode("utf-8"))
    parent_pin_matches = current_d10_blob == parent_pin

    # Verify that the canonical D11 table still consists only of the 43
    # owner-ratified testing entries, not the 512 research candidates.
    require(vocabulary.get("schema") == "sens.d11.testing/v1" and
            vocabulary.get("status") == "owner-ratified" and
            vocabulary.get("ratified_by") == "PROJECT_OWNER",
            "TEST_VOCAB_AUTHORITY", "D11 testing vocabulary must remain owner-ratified")
    require(vocabulary.get("width") == 11 and vocabulary.get("capacity") == 2048 and
            vocabulary.get("occupancy") == 43 and
            vocabulary.get("semantic_scope") ==
            "Testing vocabulary for binary SENS semantic tests; not callable Core",
            "TEST_VOCAB_SCOPE", "43-entry D11 table is test vocabulary, not callable Core")

    vocab_rows = vocabulary.get("table")
    require(isinstance(vocab_rows, list) and len(vocab_rows) == 43,
            "TEST_VOCAB_COUNT", "expected exactly 43 ratified D11 testing entries")
    test_map: dict[str, str] = {}
    test_names: set[str] = set()
    for index, row in enumerate(vocab_rows):
        bits, name = row.get("bits"), row.get("lisp")
        require(isinstance(bits, str) and re.fullmatch(r"[01]{11}", bits) is not None,
                "TEST_VOCAB_WIDTH", f"testing row {index} must have exactly 11 bits")
        require(isinstance(name, str) and bool(name),
                "TEST_VOCAB_NAME", f"testing row {index} has no LISP name")
        require(bits not in test_map, "TEST_VOCAB_DUP_COORD", f"duplicate D11 testing coordinate {bits}")
        require(name.casefold() not in test_names, "TEST_VOCAB_DUP_NAME",
                f"duplicate D11 testing name {name}")
        test_map[bits] = name
        test_names.add(name.casefold())

    d11_rows = parse_domain_rows(documents["d11_table"], "lib/domains/d11.lisp")
    require(len(d11_rows) == 43, "D11_TABLE_COUNT",
            f"expected 43 canonical D11 testing rows; found {len(d11_rows)}")
    d11_map: dict[str, str] = {}
    d11_names: set[str] = set()
    for bits, name in d11_rows:
        require(re.fullmatch(r"[01]{11}", bits) is not None,
                "D11_TABLE_WIDTH", f"invalid current D11 testing coordinate {bits!r}")
        require(bits not in d11_map, "D11_TABLE_DUP_COORD", f"duplicate current D11 coordinate {bits}")
        require(name.casefold() not in d11_names, "D11_TABLE_DUP_NAME",
                f"duplicate current D11 name {name}")
        d11_map[bits] = name
        d11_names.add(name.casefold())
    require(d11_map == test_map, "D11_TABLE_DRIFT",
            "lib/domains/d11.lisp differs from the owner-ratified 43-row testing vocabulary")

    candidate_rows = seed.get("rows")
    require(isinstance(candidate_rows, list) and len(candidate_rows) == 512,
            "CANDIDATE_COUNT", "expected 512 D11 selector candidates")
    candidates: dict[str, str] = {}
    candidate_names: set[str] = set()
    for index, row in enumerate(candidate_rows):
        require(isinstance(row, list) and len(row) == 2,
                "CANDIDATE_SHAPE", f"candidate row {index} must be [11-bit coordinate, name]")
        bits, name = row
        require(isinstance(bits, str) and re.fullmatch(r"[01]{11}", bits) is not None,
                "CANDIDATE_WIDTH", f"candidate row {index} must have exactly 11 bits")
        require(isinstance(name, str) and bool(name),
                "CANDIDATE_NAME", f"candidate row {index} has no name")
        require(bits not in candidates, "CANDIDATE_DUP_COORD", f"duplicate candidate coordinate {bits}")
        require(name.casefold() not in candidate_names, "CANDIDATE_DUP_NAME",
                f"duplicate candidate name {name}")
        candidates[bits] = name
        candidate_names.add(name.casefold())

    candidate_coordinates = set(candidates)
    test_coordinates = set(test_map)
    coord_collisions = candidate_coordinates & test_coordinates
    name_collisions = candidate_names & d11_names
    require(not coord_collisions, "D11_TEST_COORD_COLLISION",
            f"candidate coordinates overlap ratified testing rows: {sorted(coord_collisions)[:5]}")
    require(not name_collisions, "D11_TEST_NAME_COLLISION",
            f"candidate names overlap ratified testing rows: {sorted(name_collisions)[:5]}")

    expected_coordinates: set[str] = set()
    parent_extensions: dict[str, set[str]] = {bits: set() for bits in parents}
    for bits, name in candidates.items():
        parent, extension = bits[:10], bits[10]
        require(parent in parents, "CANDIDATE_PARENT",
                f"{bits} does not extend one of the 256 D10 selector parents")
        parent_name = d10_map[parent]
        suffix = "A" if extension == "0" else "D"
        expected_name = parent_name[:-1] + suffix + parent_name[-1]
        require(name == expected_name, "CANDIDATE_NAME_DERIVATION",
                f"{bits}: expected {expected_name} from {parent_name}, found {name}")
        expected_coordinates.add(parent + extension)
        parent_extensions[parent].add(extension)

    require(candidate_coordinates == {
        parent + extension for parent in parents for extension in ("0", "1")
    }, "CANDIDATE_COVERAGE", "each selector parent must have exactly suffixes 0 and 1")
    require(all(extensions == {"0", "1"} for extensions in parent_extensions.values()),
            "CANDIDATE_PAIR", "one or more D10 parents lack a 0/1 child pair")

    actual_accounting = {
        "d10_selector_parents": len(parents),
        "d11_selector_candidates": len(candidates),
        "unique_11bit_coordinates": len(candidate_coordinates),
        "unique_names": len(candidate_names),
        "d11_existing_testing_only": len(test_map),
        "test_coordinate_collisions": len(coord_collisions),
        "test_name_collisions": len(name_collisions),
        "callable": 0,
        "zig_t5_admitted": 0,
        "unallocated_coordinates_after_testing": 2048 - len(test_map),
        "unproposed_coordinates_after_testing_and_selector_research":
            2048 - len(test_map) - len(candidate_coordinates),
        "selector_candidate_coordinates_reserved": 0,
        "selector_candidates_not_callable": len(candidates),
        "new_ratified_residents": 0,
    }
    declared = seed.get("accounting", {})
    for key, actual in actual_accounting.items():
        require(declared.get(key) == actual, "ACCOUNTING",
                f"{key}: declared {declared.get(key)!r}, actual {actual!r}")

    return {
        "test_id": "D11_SELECTOR_SEED_AUDIT",
        "layer": "domain-ladder",
        "status": "MECHANICAL_PASS",
        "semantic_status": "NOT_VERIFIED",
        "domain": "D11",
        "width": 11,
        "capacity": 2048,
        "candidate_status": seed["status"],
        "owner_decision": seed["owner_decision"],
        "selector_parents": len(parents),
        "candidate_count": len(candidates),
        "unique_coordinates": len(candidate_coordinates),
        "unique_names": len(candidate_names),
        "testing_only_rows": len(test_map),
        "candidate_testing_coordinate_collisions": len(coord_collisions),
        "candidate_testing_name_collisions": len(name_collisions),
        "callable_admissions_added": 0,
        "ratified_residents_added": 0,
        "historical_d10_parent_blob": parent_pin,
        "current_d10_parent_blob": current_d10_blob,
        "historical_pin_matches_current": parent_pin_matches,
        "source_pin_note": (
            "MATCHES_CURRENT_D10_TABLE" if parent_pin_matches else
            "HISTORICAL_PIN_DIFFERS; all 256 candidate parents revalidated against current D10 rows"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print a machine-readable report")
    args = parser.parse_args(argv)
    try:
        report = validate_documents(load_documents())
    except AuditError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        print(
            "PASS test_id=D11_SELECTOR_SEED_AUDIT layer=domain-ladder "
            f"candidates={report['candidate_count']} parents={report['selector_parents']} "
            f"width={report['width']} testing_only={report['testing_only_rows']} "
            f"collisions=0 callability_added=0 ratified_residents_added=0 "
            f"semantic_status={report['semantic_status']}"
        )
        if not report["historical_pin_matches_current"]:
            print(f"WARN source_pin={report['source_pin_note']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
