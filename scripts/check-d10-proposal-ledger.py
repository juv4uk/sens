#!/usr/bin/env python3
"""Перевірка форми D10-пропозицій; НЕ семантична ратифікація."""
from __future__ import annotations

import argparse
import csv
import io
import json
import hashlib
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = ROOT / "knowledge" / "d10-proposal-ledger.tsv"
FIELDS = (
    "proposal_id", "surface_uk", "surface_ukr", "semantic_name",
    "semantic_law", "width", "donor_provenance", "dedup_check",
    "ownership_test", "blocked_source", "status", "ratified",
)
REF = r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{7,40}:[^:\t\n]+:[1-9][0-9]*(?:-[1-9][0-9]*)?"
DEDUP = re.compile(
    r"D1-D9@[0-9a-f]{7,40}=NO-MATCH;D10@[0-9a-f]{7,40}=NO-MATCH\Z"
)
PROVENANCE = re.compile(REF + r"\Z")
ID = re.compile(r"D10P-[0-9]{4,}\Z")


def validate(content: str) -> list[str]:
    errors: list[str] = []
    reader = csv.DictReader(io.StringIO(content), delimiter="\t")
    if tuple(reader.fieldnames or ()) != FIELDS:
        return ["Заголовок TSV не збігається з канонічним FIELDS"]
    ids: set[str] = set()
    names: set[str] = set()
    surfaces: set[tuple[str, str]] = set()
    for lineno, row in enumerate(reader, start=2):
        if None in row or any(value is None for value in row.values()):
            errors.append(f"{lineno}: зайві або відсутні поля TSV")
            continue
        missing = [f for f in FIELDS if not row[f].strip()]
        if missing:
            errors.append(f"{lineno}: порожні поля: {', '.join(missing)}")
            continue
        pid = row["proposal_id"]
        if not ID.fullmatch(pid) or pid in ids:
            errors.append(f"{lineno}: недопустимий або дубльований proposal_id")
        ids.add(pid)
        name = row["semantic_name"].casefold().strip()
        if name in names:
            errors.append(f"{lineno}: дубль semantic_name в реєстрі")
        names.add(name)
        pair = (row["surface_uk"].casefold(), row["surface_ukr"].casefold())
        if pair in surfaces:
            errors.append(f"{lineno}: дубль українських поверхонь")
        surfaces.add(pair)
        for surface in pair:
            if not any("\u0400" <= ch <= "\u04ff" for ch in surface):
                errors.append(f"{lineno}: surface_uk/ukr має містити кирилицю")
        if row["width"] != "D10":
            errors.append(f"{lineno}: дозволено тільки width=D10")
        if not PROVENANCE.fullmatch(row["donor_provenance"]):
            errors.append(f"{lineno}: donor_provenance потребує owner/repo@COMMIT:path:line")
        if row["blocked_source"] != "NOT-A-MIGRATION-BLOCK" and not PROVENANCE.fullmatch(row["blocked_source"]):
            errors.append(f"{lineno}: blocked_source потребує owner/repo@COMMIT:path:line або точний маркер NOT-A-MIGRATION-BLOCK")
        if not DEDUP.fullmatch(row["dedup_check"]):
            errors.append(f"{lineno}: dedup_check потребує окремих D1-D9 та D10 SHA")
        if not row["ownership_test"].startswith("UNIVERSAL-BORDER: ") or len(row["ownership_test"]) < 32:
            errors.append(f"{lineno}: потрібен аргументований UNIVERSAL-BORDER")
        if row["status"] != "pending-review" or row["ratified"] != "0":
            errors.append(f"{lineno}: тільки pending-review та ratified=0")
        for key in FIELDS:
            if "\n" in row[key] or "\r" in row[key]:
                errors.append(f"{lineno}: переноси рядка всередині поля заборонені")
    return errors




def selection_trace_errors(content: str, inventory: dict, baseline: dict, history: dict) -> list[str]:
    """Кожен append після історичного 625 має бути в журналі та в SHA-ланцюгу."""
    errors: list[str] = []
    rows = inventory.get("rows", [])
    initial = baseline.get("frozen_count")
    if initial != 625 or len(rows) < initial or len(baseline.get("rows", [])) != initial:
        return ["некоректна або неповна історична 625-основа"]
    protected = baseline.get("protected_fields", [])
    for index in range(initial):
        for field in protected:
            if rows[index].get(field) != baseline["rows"][index].get(field):
                errors.append(f"історична ідентичність змінена: {index}:{field}")
                break

    ledger = list(csv.DictReader(io.StringIO(content), delimiter="\t"))
    ledger_by_name = {r["semantic_name"].strip().upper(): r for r in ledger}
    if len(ledger_by_name) != len(ledger):
        errors.append("неунікальні імена в журналі")
    transitions = history.get("transitions", [])
    prior = initial
    expected_previous_sha = baseline.get("origin_inventory_git_blob")
    selected_now: set[str] = set()
    for t in transitions:
        if t.get("previous_inventory_blob_sha") != expected_previous_sha:
            errors.append("SHA-ланцюг: попередня подія не збігається з історичним результатом")
        next_sha = t.get("resulting_inventory_blob_sha")
        if not isinstance(next_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", next_sha):
            errors.append("SHA-ланцюг: недопустимий resulting_inventory_blob_sha")
        next_count = t.get("resulting_selected", -1)
        if t.get("previous_selected") != prior or not isinstance(next_count, int) or next_count <= prior or next_count > len(rows):
            errors.append("перерваний або недопустимий ланцюг append D10")
            return errors
        added = rows[prior:next_count]
        if [r.get("stable_id") for r in added] != t.get("added_stable_ids"):
            errors.append("новий зріз інвентарю не збігається з append-ID транзакції")
        if t.get("delta_selected") != len(added) or t.get("coordinates_added") != 0 or t.get("ratified_added") != 0:
            errors.append("неявний ріст, координата або ратифікація у research-переході")
        for row in added:
            name = row.get("semantic_name", "").upper()
            selected_now.add(name)
            ent = ledger_by_name.get(name)
            if not ent:
                errors.append(f"{name}: SELECTED без запису в proposal-ledger")
                continue
            if ent.get("status") != "pending-review" or ent.get("ratified") != "0":
                errors.append(f"{name}: журнал не може ратифікувати запис")
            if ent.get("blocked_source") != "NOT-A-MIGRATION-BLOCK":
                # Якщо цей відбір походить від реального BLOCK, збережіть
                # його source pointer, а не вигадуйте міграційний блок.
                if not PROVENANCE.fullmatch(ent.get("blocked_source", "")):
                    errors.append(f"{name}: invalid migration BLOCK source")
            if ent.get("surface_uk") != row.get("surface_uk") or ent.get("surface_ukr") != row.get("surface_ukr"):
                errors.append(f"{name}: українські поверхні не збігаються з відбором")
            prior_d10 = t.get("previous_inventory_blob_sha")
            match = DEDUP.fullmatch(ent.get("dedup_check", ""))
            if not match or f"D10@{prior_d10}=NO-MATCH" not in ent.get("dedup_check", ""):
                errors.append(f"{name}: D10 dedup має посилатися на стан ПЕРЕД цим append")
            if row.get("coordinate") is not None or row.get("ratified_resident") is not False:
                errors.append(f"{name}: proposal не надає координат або ратифікації")
            if row.get("status") != "SELECTED-RESEARCH-CANDIDATE":
                errors.append(f"{name}: D10 append має research-only статус")
        prior = next_count
        expected_previous_sha = next_sha
    if prior != len(rows):
        errors.append(f"виявлено {len(rows)-prior} неврахованих selection-рядків у D10")
    for ent in ledger:
        name = ent["semantic_name"].strip().upper()
        if name not in selected_now:
            # PROPOSE precedes SELECT. A documented, source-pinned research
            # donor needs NO invented migration BLOCK; remain pending and
            # never auto-admit a new semantic identity.
            if ent["blocked_source"] == "NOT-A-MIGRATION-BLOCK":
                if not PROVENANCE.fullmatch(ent.get("donor_provenance", "")):
                    errors.append(f"{name}: unselected donor lacks pinned source")
                if ent.get("status") != "pending-review" or ent.get("ratified") != "0":
                    errors.append(f"{name}: unselected donor cannot ratify itself")
            elif not PROVENANCE.fullmatch(ent.get("blocked_source", "")):
                errors.append(f"{name}: missing real migration BLOCK provenance")
    return errors



def inventory_projection_errors(inventory: dict, document: str) -> list[str]:
    """Keep Archipelago's human counts in sync with machine D10 authority."""
    accounting = inventory.get("accounting")
    capacity = inventory.get("capacity")
    if not isinstance(accounting, dict) or not isinstance(capacity, int):
        return ["machine D10 inventory lacks accounting/capacity"]

    expected = {
        "D10 selected": (
            re.compile(r"(?m)^D10 selected\s+(\d+)/(\d+)\s*$"),
            (accounting.get("selected_semantic_candidates"), capacity),
        ),
        "law-forced": (
            re.compile(r"(?m)^law-forced\s+(\d+)\s*$"),
            (accounting.get("law_forced_coordinates"),),
        ),
        "unplaced": (
            re.compile(r"(?m)^unplaced\s+(\d+)\s*$"),
            (accounting.get("unplaced_selected_candidates"),),
        ),
        "remaining": (
            re.compile(r"(?m)^remaining\s+(\d+)\s*$"),
            (accounting.get("remaining_semantic_inventory"),),
        ),
        "ratified": (
            re.compile(r"(?m)^ratified\s+(\d+)\s*$"),
            (accounting.get("ratified_d10_residents"),),
        ),
    }
    errors: list[str] = []
    for label, (pattern, wanted) in expected.items():
        matches = pattern.findall(document)
        if len(matches) != 1:
            errors.append(f"Archipelago projection must contain exactly one {label!r} count")
            continue
        found = matches[0]
        observed = tuple(int(value) for value in found) if isinstance(found, tuple) else (int(found),)
        if any(value is None for value in wanted):
            errors.append(f"machine D10 inventory misses the {label!r} accounting value")
            continue
        target = tuple(int(value) for value in wanted)
        if observed != target:
            errors.append(f"Archipelago {label}={observed} disagrees with machine inventory={target}")
    return errors


def self_test() -> None:
    sha = "a" * 40
    reference = f"juv4uk/sens@{sha}:lib/core1.lisp:42"
    valid = [
        "D10P-0001", "виклик", "викликати", "TEST-BORDER",
        "Дослідний тест закону на межі", "D10", reference,
        f"D1-D9@{sha}=NO-MATCH;D10@{sha}=NO-MATCH",
        "UNIVERSAL-BORDER: незалежне від носія правило межі",
        reference, "pending-review", "0",
    ]
    header = "\t".join(FIELDS) + "\n"
    row = "\t".join(valid) + "\n"
    assert not validate(header), "порожній канонічний журнал має бути чинним"
    assert not validate(header + row), "правильний синтетичний запис має пройти"
    research = valid.copy()
    research[9] = "NOT-A-MIGRATION-BLOCK"
    assert not validate(header + "\t".join(research) + "\n"), "source research marker requires later selection trace"

    tests = (
        (11, "1"),
        (10, "admitted"),
        (5, "D8"),
        (6, "source missing"),
        (7, "not-checked"),
        (1, "ascii-only"),
    )
    for index, bad in tests:
        mutant = valid.copy()
        mutant[index] = bad
        assert validate(header + "\t".join(mutant) + "\n"), (index, bad)
    assert validate(header + row + row), "подвійний запис не допускається"
    assert validate("wrong\n"), "зміна схеми має бути відхилена"
    projection_inventory = {
        "capacity": 1024,
        "accounting": {
            "selected_semantic_candidates": 625,
            "law_forced_coordinates": 256,
            "unplaced_selected_candidates": 369,
            "remaining_semantic_inventory": 399,
            "ratified_d10_residents": 0,
        },
    }
    projection = """D10 selected              625/1024
law-forced                256
unplaced                  369
remaining                 399
ratified                    0
"""
    assert not inventory_projection_errors(projection_inventory, projection), "matching projection must pass"
    stale = projection.replace("625/1024", "434/1024")
    assert inventory_projection_errors(projection_inventory, stale), "stale copied counts must fail closed"
    print("D10-PROPOSAL-LEDGER self-test: PASS (schema + negative controls + inventory drift)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    if not args.ledger.is_file():
        print(f"D10-PROPOSAL-LEDGER: BLOCK missing {args.ledger}")
        return 1
    errors = validate(args.ledger.read_text(encoding="utf-8"))
    if errors:
        for error in errors:
            print(f"D10-PROPOSAL-LEDGER: BLOCK {error}")
        return 1
    inventory_path = ROOT / "knowledge" / "d10-v1-semantic-inventory.json"
    architecture_path = ROOT / "docs" / "architecture" / "ARCHIPELAGO-V1.uk.md"
    try:
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        projection = architecture_path.read_text(encoding="utf-8")
    except (OSError, ValueError) as exc:
        print(f"D10-PROPOSAL-LEDGER: BLOCK cannot read D10 machine inventory/projection: {exc}")
        return 1
    try:
        baseline = json.loads((ROOT / "knowledge/d10-growth-baseline-v1.json").read_text(encoding="utf-8"))
        history = json.loads((ROOT / "knowledge/d10-selection-transition-history.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"D10-PROPOSAL-LEDGER: BLOCK missing immutable growth history: {exc}")
        return 1
    trace_errors = selection_trace_errors(args.ledger.read_text(encoding="utf-8"), inventory, baseline, history)
    inventory_bytes = inventory_path.read_bytes()
    actual_blob = hashlib.sha1(b"blob " + str(len(inventory_bytes)).encode("ascii") + b"\0" + inventory_bytes).hexdigest()
    expected_blob = history["transitions"][-1]["resulting_inventory_blob_sha"] if history["transitions"] else baseline["origin_inventory_git_blob"]
    if actual_blob != expected_blob:
        trace_errors.append("SHA-ланцюг: реальний Git blob canonical inventory не дорівнює останньому підтвердженому результату")
    if trace_errors:
        for error in trace_errors:
            print(f"D10-PROPOSAL-LEDGER: BLOCK {error}")
        return 1
    projection_errors = inventory_projection_errors(inventory, projection)
    if projection_errors:
        for error in projection_errors:
            print(f"D10-PROPOSAL-LEDGER: BLOCK {error}")
        return 1

    count = max(0, len(args.ledger.read_text(encoding="utf-8").splitlines()) - 1)
    print(f"D10-PROPOSAL-LEDGER: PASS rows={count}; inventory projection synced; no semantic admission implied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
