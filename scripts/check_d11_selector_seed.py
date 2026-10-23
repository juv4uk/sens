#!/usr/bin/env python3
"""Mechanical audit of the D11 selector research seed.

This validates universal 11-bit selector derivation and coordinate uniqueness.
Definitions follow CAR/CDR algebra; this does not implement a direct D11 opcode.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
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


def validate_d11_table_projections(source: str) -> None:
    """Звірити всі шість поверхонь Д11 з композицією CAR/CDR.

    Використовує той самий S-expression reader, що й відкриття доменних
    функцій. Неправильний порядок або зайві колонки не можуть бути пропущені.
    """
    parser_path = ROOT / "scripts" / "discover_domain_function_candidates.py"
    spec = importlib.util.spec_from_file_location("sens_d11_row_parser", parser_path)
    require(spec is not None and spec.loader is not None, "D11_TABLE_PARSER",
            f"cannot load exact domain-table parser {parser_path}")
    parser = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = parser
    spec.loader.exec_module(parser)

    checked = 0
    for line_no, line in enumerate(source.splitlines(), 1):
        if not re.match(r"^\s*\([01]{11}\s+", line):
            continue
        try:
            row = parser.parse_domain_row(line, 11, line_no)
        except parser.AuditError as exc:
            raise AuditError("D11_TABLE_PROJECTION",
                             f"line {line_no}: malformed six-column D11 row: {exc}") from exc
        require(row is not None, "D11_TABLE_PROJECTION",
                f"line {line_no}: row cannot be parsed")
        name = row["LISP"]
        require(re.fullmatch(r"C[AD]{9}R", name) is not None,
                "D11_TABLE_PROJECTION",
                f"line {line_no} code={row['bits']}: invalid selector name {name!r}")
        require(not row["LISP_quoted"], "D11_TABLE_PROJECTION",
                f"line {line_no} code={row['bits']}: LISP name must not be quoted")
        steps = name[1:-1]
        ukrainian = "-від-".join("перше" if ch == "A" else "решта" for ch in steps)
        sanskrit = "-".join("ādi" if ch == "A" else "śeṣa" for ch in steps)
        expected = {
            "ук": ukrainian,
            "укр": ukrainian,
            "san": sanskrit,
            "en": name.lower(),
            "sym": "()",
        }
        for column, value in expected.items():
            require(row[column] == value and not row[column + "_quoted"],
                    "D11_TABLE_PROJECTION",
                    f"line {line_no} code={row['bits']} column={column}"
                    f" expected={value!r} actual={row[column]!r}"
                    f" quoted={row[column + '_quoted']}")
        checked += 1
    require(checked == 512, "D11_TABLE_PROJECTION",
            f"expected 512 complete D11 projections, found {checked}")


def validate_documents(documents: dict[str, Any]) -> dict[str, Any]:
    seed = documents["seed"]
    d10_seed = documents["d10_seed"]
    vocabulary = documents["d11_vocabulary"]

    require(seed.get("schema") == "sens.d11.selector-seed/v1",
            "SEED_SCHEMA", "expected sens.d11.selector-seed/v1")
    require(seed.get("status") == "MATHEMATICALLY_DERIVED_SELECTOR_FUNCTIONS" and
            seed.get("owner_decision") == "MATHEMATICAL_DERIVATION_CONFIRMED_NOT_NEW_PRIMITIVE",
            "NOT_MATHEMATICAL_DERIVATION",
            "selector definitions must follow ratified CAR/CDR composition, not a new primitive admission")
    require(seed.get("domain") == "D11" and seed.get("width") == 11 and
            seed.get("capacity") == 2048,
            "SEED_WIDTH", "D11 deriveds require exact width 11 and capacity 2048")

    source = seed.get("source", {})
    require(source.get("parent_domain") == "D10" and
            source.get("ratified_parent_surface") == PATHS["d10_table"],
            "PARENT_SOURCE", "derived parent must be the current D10 domain table")
    parent_pin = source.get("parent_git_blob")
    require(isinstance(parent_pin, str) and re.fullmatch(r"[0-9a-f]{40}", parent_pin),
            "PARENT_PIN_FORMAT", "historical parent Git blob pin must be a 40-digit SHA-1")
    require(source.get("d11_testing_vocabulary") == PATHS["d11_vocabulary"],
            "TEST_VOCAB_SOURCE", "seed must identify the legacy unratified D11 test fixture")

    law = seed.get("law", {})
    require(law.get("derived_by_law") is True and
            law.get("non_selector_parents") == "NO_EXTENSION" and
            law.get("coordinate_rule") == "11-bit derived selector = 10-bit D10 parent selector coordinate || one bit",
            "DERIVED_LAW", "seed must remain a selector-only, derived-only extension")
    gate = str(law.get("opcode_admission", ""))
    require(all(token in gate for token in (
        "NO_NEW_PRIMITIVE", "NO_ZIG_T5_DIRECT_OPCODE_ADMISSION"
    )), "OPCODE_ADMISSION", "mathematical derivation is distinct from direct opcode and Zig T5 admission")

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

    # The 43 historical test fixtures remain unratified and archived;
    # the current D11 table is checked against all 512 derived selectors below.
    require(vocabulary.get("schema") == "sens.d11.testing/v1" and
            vocabulary.get("status") == "UNRATIFIED_REVIEW" and
            vocabulary.get("ratified") is False and
            vocabulary.get("ratified_by") is None,
            "TEST_VOCAB_AUTHORITY", "D11 legacy testing fixtures must remain explicitly unratified")
    require(vocabulary.get("width") == 11 and vocabulary.get("capacity") == 2048 and
            vocabulary.get("occupancy") == 43 and
            vocabulary.get("semantic_scope") ==
            "Testing vocabulary for binary SENS semantic tests; not callable Core",
            "TEST_VOCAB_SCOPE", "43-entry D11 table is test vocabulary, not callable Core")

    vocab_rows = vocabulary.get("table")
    require(isinstance(vocab_rows, list) and len(vocab_rows) == 43,
            "TEST_VOCAB_COUNT", "expected exactly 43 unratified historical D11 test fixtures")
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
    # D11 — РОБОЧИЙ домен розширення: наповнений похідними за законом (512), а не
    # відхиленими 22.10.2026 тестовими 43 (ті перенесено в lib/domains/archive/).
    require(len(d11_rows) == 512, "D11_TABLE_COUNT",
            f"expected 512 derived D11 rows (law selector-suffix-extension); found {len(d11_rows)}")
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
    # Звірку з похідними (deriveds) робимо нижче, після їх побудови.
    validate_d11_table_projections(documents["d11_table"])

    derived_rows = seed.get("rows")
    require(isinstance(derived_rows, list) and len(derived_rows) == 512,
            "DERIVED_COUNT", "expected 512 D11 selector deriveds")
    deriveds: dict[str, str] = {}
    derived_names: set[str] = set()
    for index, row in enumerate(derived_rows):
        require(isinstance(row, list) and len(row) == 2,
                "DERIVED_SHAPE", f"derived row {index} must be [11-bit coordinate, name]")
        bits, name = row
        require(isinstance(bits, str) and re.fullmatch(r"[01]{11}", bits) is not None,
                "DERIVED_WIDTH", f"derived row {index} must have exactly 11 bits")
        require(isinstance(name, str) and bool(name),
                "DERIVED_NAME", f"derived row {index} has no name")
        require(bits not in deriveds, "DERIVED_DUP_COORD", f"duplicate derived coordinate {bits}")
        require(name.casefold() not in derived_names, "DERIVED_DUP_NAME",
                f"duplicate derived name {name}")
        deriveds[bits] = name
        derived_names.add(name.casefold())

    derived_coordinates = set(deriveds)
    test_coordinates = set(test_map)
    coord_collisions = derived_coordinates & test_coordinates
    name_collisions = derived_names & test_names
    # Збіг із легасі-фікстурою більше не заборонено: ті 43 перенесено в архів
    # (lib/domains/archive/d11-rejected-43.lisp), і саме похідні за законом
    # тепер наповнюють lib/domains/d11.lisp. Звірку d11_map == deriveds зроблено вище.

    expected_coordinates: set[str] = set()
    parent_extensions: dict[str, set[str]] = {bits: set() for bits in parents}
    for bits, name in deriveds.items():
        parent, extension = bits[:10], bits[10]
        require(parent in parents, "DERIVED_PARENT",
                f"{bits} does not extend one of the 256 D10 selector parents")
        parent_name = d10_map[parent]
        suffix = "A" if extension == "0" else "D"
        expected_name = parent_name[:-1] + suffix + parent_name[-1]
        require(name == expected_name, "DERIVED_NAME_DERIVATION",
                f"{bits}: expected {expected_name} from {parent_name}, found {name}")
        expected_coordinates.add(parent + extension)
        parent_extensions[parent].add(extension)

    require(derived_coordinates == {
        parent + extension for parent in parents for extension in ("0", "1")
    }, "DERIVED_COVERAGE", "each selector parent must have exactly suffixes 0 and 1")
    require(all(extensions == {"0", "1"} for extensions in parent_extensions.values()),
            "DERIVED_PAIR", "one or more D10 parents lack a 0/1 child pair")

    # The current D11 table must match the mathematically derived seed, not
    # merely contain 512 distinct well-formed coordinates.
    for bits, expected_name in deriveds.items():
        actual_name = d11_map.get(bits)
        require(actual_name == expected_name, "D11_TABLE_DERIVATION",
                f"input=D11:{bits} expected={expected_name!r} actual={actual_name!r} "
                "reproduce=python3 scripts/check_d11_selector_seed.py --json")

    actual_accounting = {
        "d10_selector_parents": len(parents),
        "d11_mathematically_defined_selectors": len(deriveds),
        "unique_11bit_coordinates": len(derived_coordinates),
        "unique_names": len(derived_names),
        "d11_existing_testing_only": len(test_map),
        "test_coordinate_collisions": len(coord_collisions),
        "test_name_collisions": len(name_collisions),
        "callable": 0,
        "zig_t5_admitted": 0,
        "coordinates_outside_testing_vocabulary": 2048 - len(test_map),
        "coordinates_outside_testing_and_derived_selectors":
            2048 - len(test_coordinates | derived_coordinates),
        "selector_derived_coordinates": len(deriveds),
        "derived_selectors_without_direct_opcode_admission": len(deriveds),
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
        "semantic_status": "DERIVED_BY_COMPOSITION",
        "domain": "D11",
        "width": 11,
        "capacity": 2048,
        "derived_status": seed["status"],
        "owner_decision": seed["owner_decision"],
        "selector_parents": len(parents),
        "derived_count": len(deriveds),
        "unique_coordinates": len(derived_coordinates),
        "unique_names": len(derived_names),
        "testing_only_rows": len(test_map),
        "derived_testing_coordinate_collisions": len(coord_collisions),
        "derived_testing_name_collisions": len(name_collisions),
        "callable_admissions_added": 0,
        "ratified_residents_added": 0,
        "historical_d10_parent_blob": parent_pin,
        "current_d10_parent_blob": current_d10_blob,
        "historical_pin_matches_current": parent_pin_matches,
        "source_pin_note": (
            "MATCHES_CURRENT_D10_TABLE" if parent_pin_matches else
            "HISTORICAL_PIN_DIFFERS; all 256 derived parents revalidated against current D10 rows"
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
            f"derived={report['derived_count']} parents={report['selector_parents']} "
            f"width={report['width']} testing_only={report['testing_only_rows']} "
            f"collisions={report['derived_testing_coordinate_collisions']} "
            f"name_collisions={report['derived_testing_name_collisions']} "
            f"callability_added=0 ratified_residents_added=0 "
            f"semantic_status={report['semantic_status']}"
        )
        if not report["historical_pin_matches_current"]:
            print(f"WARN source_pin={report['source_pin_note']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
