#!/usr/bin/env python3
"""D10 selected-row growth requires a real recorded proposal; no ratification."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import subprocess
from copy import deepcopy

INVENTORY = "knowledge/d10-v1-semantic-inventory.json"
LEDGER = "knowledge/d10-proposal-ledger.tsv"
FIELDS = (
    "proposal_id", "surface_uk", "surface_ukr", "semantic_name",
    "semantic_law", "width", "donor_provenance", "dedup_check",
    "ownership_test", "blocked_source", "status", "ratified",
)
SHA = re.compile(r"[0-9a-f]{40}\Z")


class GateError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise GateError(message)


def parse_ledger(content: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(content), delimiter="\t")
    require(tuple(reader.fieldnames or ()) == FIELDS, "ledger TSV header drift")
    rows = list(reader)
    require(all(None not in row and all(v is not None for v in row.values())
                for row in rows), "ledger TSV ragged row")
    require(all(row["status"] == "pending-review" and row["ratified"] == "0"
                for row in rows), "ledger cannot ratify selected meanings")
    require(len({row["proposal_id"] for row in rows}) == len(rows),
            "duplicate proposal ID")
    require(len({row["semantic_name"].casefold() for row in rows}) == len(rows),
            "duplicate ledger semantic name")
    return rows


def check(base: dict, current: dict,
          base_ledger_text: str, current_ledger_text: str) -> dict:
    original = base.get("rows")
    selected = current.get("rows")
    require(isinstance(original, list) and isinstance(selected, list),
            "D10 inventory rows unavailable")
    require(base.get("domain") == current.get("domain") == "D10",
            "D10 domain authority changed")
    require(base.get("width") == current.get("width") == 10,
            "D10 width changed")
    require(base.get("capacity") == current.get("capacity") == 1024,
            "D10 capacity changed")
    old_account, new_account = base.get("accounting", {}), current.get("accounting", {})
    require(old_account.get("selected_semantic_candidates") == len(original),
            "base D10 count inconsistent")
    require(new_account.get("selected_semantic_candidates") == len(selected),
            "new D10 count inconsistent")
    for accounting, count in ((old_account, len(original)), (new_account, len(selected))):
        require(accounting.get("remaining_semantic_inventory") == 1024 - count,
                "D10 remaining count inconsistent")
        require(accounting.get("law_forced_coordinates") == 256,
                "proved selector coordinates changed")
        require(accounting.get("unplaced_selected_candidates") ==
                count - accounting.get("law_forced_coordinates"),
                "D10 unplaced accounting inconsistent")
        require(accounting.get("ratified_d10_residents") == 0,
                "D10 ratification not authorized")

    require(len(selected) >= len(original), "D10 selected rows removed")
    require(selected[:len(original)] == original,
            "D10 existing selected rows edited/reordered (not append-only)")

    before = parse_ledger(base_ledger_text)
    after = parse_ledger(current_ledger_text)
    require(len(after) >= len(before) and after[:len(before)] == before,
            "D10 proposal ledger edited, deleted or reordered (not append-only)")

    new_rows = selected[len(original):]
    known = {row["semantic_name"].casefold(): row for row in after}
    old_names = {row["semantic_name"].casefold() for row in original}
    all_names = [row["semantic_name"].casefold() for row in selected]
    all_ids = [row["stable_id"] for row in selected]
    require(len(set(all_names)) == len(all_names),
            "duplicate D10 selected semantic name")
    require(len(set(all_ids)) == len(all_ids),
            "duplicate D10 stable id")

    for row in new_rows:
        name = row["semantic_name"]
        require(name.casefold() not in old_names, "old name reselected")
        require(name.casefold() in known,
                "selected D10 meaning " + name + " has NO proposal-ledger row")
        require(row.get("coordinate") is None and row.get("coordinate_basis") == "UNPLACED",
                "selected D10 meaning was assigned an unproved coordinate")
        require(row.get("ratified_resident") is False and
                row.get("status") == "SELECTED-RESEARCH-CANDIDATE",
                "selected D10 meaning was ratified/incorrectly admitted")
        require(row.get("proposal_status", "pending-owner-review") ==
                "pending-owner-review", "selected row bypasses owner review")
        proposal = known[name.casefold()]
        require(proposal["width"] == "D10" and
                proposal["status"] == "pending-review" and
                proposal["ratified"] == "0",
                "proposal is not an unratified D10 research proposal")

    return {"previous": len(original), "current": len(selected),
            "new_selected": len(new_rows), "ledger_previous": len(before),
            "ledger_current": len(after),
            "new_names": [row["semantic_name"] for row in new_rows]}


def git_show(rev: str, path: str) -> str:
    require(bool(SHA.fullmatch(rev)), "revision must be a full verified git SHA")
    out = subprocess.run(["git", "show", rev + ":" + path],
                         check=False, text=True, capture_output=True)
    require(out.returncode == 0, f"cannot read {rev}:{path}: {out.stderr.strip()}")
    return out.stdout


def fixture():
    header = "\t".join(FIELDS) + "\n"
    ref = "juv4uk/sens@" + "a" * 40 + ":lib/source.lisp:1"
    a = {
        "proposal_id": "D10P-0001", "surface_uk": "тест-закон",
        "surface_ukr": "тестовий-закон", "semantic_name": "NEW-LAW",
        "semantic_law": "observed new law", "width": "D10",
        "donor_provenance": ref,
        "dedup_check": "D1-D9@" + "a"*40 + "=NO-MATCH;D10@" + "b"*40 + "=NO-MATCH",
        "ownership_test": "UNIVERSAL-BORDER: explicit observable behavior",
        "blocked_source": "NO-MIGRATION-BLOCK",
        "status": "pending-review", "ratified": "0",
    }
    row = "\t".join(a[k] for k in FIELDS) + "\n"
    base_rows = [{"stable_id": "old", "semantic_name": "OLD-LAW",
                  "coordinate": "0"*10, "ratified_resident": False}]
    new_row = {"stable_id": "new", "semantic_name": "NEW-LAW",
               "coordinate": None, "coordinate_basis": "UNPLACED",
               "ratified_resident": False, "status": "SELECTED-RESEARCH-CANDIDATE",
               "proposal_status": "pending-owner-review"}
    def inventory(rows):
        n = len(rows)
        return {"domain": "D10", "width": 10, "capacity": 1024, "rows": rows,
                "accounting": {"selected_semantic_candidates": n,
                               "remaining_semantic_inventory": 1024-n,
                               "law_forced_coordinates": 256,
                               "unplaced_selected_candidates": n-256,
                               "ratified_d10_residents": 0}}
    return inventory(base_rows), inventory(base_rows + [new_row]), header, row


def self_test() -> None:
    base, target, header, row = fixture()
    assert check(base, target, header, header + row)["new_selected"] == 1
    # A proposal already submitted in an earlier PR remains valid for later selection.
    assert check(base, target, header + row, header + row)["new_selected"] == 1
    assert check(base, base, header, header)["new_selected"] == 0
    negatives = [
        ("missing proposal", target, header, header),
        ("edited old resident", dict(target, rows=[
            dict(base["rows"][0], semantic_name="ALTERED"), target["rows"][-1]]),
         header, header + row),
        ("deleted ledger", target, header + row, header),
        ("forged ratification", dict(target, rows=[base["rows"][0],
            dict(target["rows"][-1], ratified_resident=True)]), header, header + row),
        ("invented coordinate", dict(target, rows=[base["rows"][0],
            dict(target["rows"][-1], coordinate="0"*10)]), header, header + row),
        ("duplicate selected name", dict(target, rows=[base["rows"][0],
            dict(target["rows"][-1], semantic_name="OLD-LAW")]), header, header + row),
        ("wrong ledger status", target, header,
         header + row.replace("pending-review", "selected")),
        ("fake reader authority", dict(target,
            accounting=dict(target["accounting"], ratified_d10_residents=1)),
         header, header + row),
    ]
    for label, candidate, prev, cur in negatives:
        try:
            check(base, candidate, prev, cur)
        except GateError:
            continue
        raise AssertionError("negative control escaped: " + label)
    print("D10-LEDGER-GROWTH: PASS 8/8 negative controls")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base")
    parser.add_argument("--head", default=None)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
        if not args.base:
            require(args.self_test, "missing --base full SHA")
            return 0
        require(args.head, "missing --head full SHA")
        result = check(json.loads(git_show(args.base, INVENTORY)),
                       json.loads(git_show(args.head, INVENTORY)),
                       git_show(args.base, LEDGER), git_show(args.head, LEDGER))
        print("D10-LEDGER-GROWTH: PASS " + json.dumps(result, ensure_ascii=False))
        return 0
    except (GateError, ValueError, KeyError, AssertionError) as exc:
        print("D10-LEDGER-GROWTH: BLOCK " + str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
