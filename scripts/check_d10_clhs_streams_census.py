#!/usr/bin/env python3
"""Перевіряє перепис §21.2 як research-only дані, без семантичної ратифікації."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "knowledge/d10-clhs-streams-census-20261009.json"
KIND_COUNTS = {"system-class": 8, "function": 49, "macro": 4,
               "variable": 7, "condition-type": 2}
MAIN_SOURCE = "https://www.cs.cmu.edu/Groups/AI/html/hyperspec/HyperSpec/Body/sec_the_streams_dictionary.html"


class CensusError(ValueError):
    pass


def require(ok: bool, why: str) -> None:
    if not ok:
        raise CensusError(why)


def validate(document: dict) -> dict:
    require(document.get("schema") == "d10-clhs-streams-census/v1", "schema")
    require(document.get("status") == "READ-ONLY-SOURCE-GRADED-CENSUS-NOT-SELECTED",
            "improper selection status")
    require(document.get("primary_url") == MAIN_SOURCE, "wrong source")
    require(document.get("estimated_new_selected") == 0, "invented selected growth")
    require(document.get("ratified_added") == 0 and
            document.get("new_coordinates") == 0, "ratified/coordinate")
    require(document.get("current_d10_selected") == 630,
            "historical snapshot count must remain explicit")
    for key in ("current_d9_blob", "current_d10_blob"):
        require(bool(re.fullmatch(r"[0-9a-f]{40}", str(document.get(key, "")))),
                "missing pinned immutable blob: " + key)
    rows = document.get("rows", [])
    require(isinstance(rows, list) and len(rows) == 70, "not all 70 name/kind entries")
    seen = set()
    counts = {key: 0 for key in KIND_COUNTS}
    d9hits, d10hits = [], []
    for item in rows:
        name, kind = item.get("name"), item.get("kind")
        require(isinstance(name, str) and name.strip(), "empty donor name")
        require(kind in KIND_COUNTS and item.get("group"), "invalid source kind")
        require((name, kind) not in seen, "duplicate name/kind identity")
        seen.add((name, kind))
        counts[kind] += 1
        require(item.get("primary_dictionary") == MAIN_SOURCE, "missing primary source")
        require(item.get("relation_class") == "CENSUS-ONLY-PENDING-BEHAVIORAL-DEDUP",
                "semantic selection disguised as census")
        require(item.get("lower_D1_D8_semantic_dedup") == "PENDING",
                "unproven lower semantic equality")
        require(item.get("selected_in_d10") is False, "unauthorized selection")
        require(item.get("coordinate") is None and item.get("ratified") is False,
                "coordinate or ratification invented")
        if item.get("name_collision_d9"):
            d9hits.append(name)
        if item.get("name_collision_d10"):
            d10hits.append(name)
    require(counts == KIND_COUNTS, "name-kind counts changed")
    tally = document.get("counts", {})
    require(tally.get("total_name_kind_entries") == len(rows), "total mismatch")
    require(tally.get("kind") == counts, "kind tally mismatch")
    require(tally.get("D9_exact_name_collisions") == d9hits, "D9 spelling tally changed")
    require(tally.get("D10_exact_name_collisions") == d10hits, "D10 spelling tally changed")
    roots = document.get("root_reviews", [])
    require(len(roots) == 3 and len({r.get("root_claim") for r in roots}) == 3,
            "root review count")
    for root in roots:
        require(root.get("lead_name") in [i["name"] for i in rows],
                "root lead not in standard dictionary")
        require(root.get("source_url", "").startswith("https://"),
                "source URL not pinned")
        require(len(root.get("positive_witnesses", [])) >= 2 and
                root.get("falsifier"), "insufficient falsifiers/positives")
        require(root.get("decision", "").startswith("HOLD-"), "premature selection")
        require(root.get("oracle_status") == "NOT-RUN", "false oracle claim")
        require(root.get("coordinate") is None and root.get("ratified") is False
                and root.get("selected") is False, "invented coordinate/resident")
    return {"dictionary_name_kind_entries": len(rows),
            "deep_review_hold": len(roots), "new_selected": 0,
            "ratified": 0}


def self_test(doc: dict) -> None:
    require(validate(doc)["dictionary_name_kind_entries"] == 70, "positive case")
    mutations = [
        ("rename source", lambda d: d.update(primary_url="http://fake")),
        ("drop record", lambda d: d["rows"].pop()),
        ("copy one source item", lambda d: d["rows"].append(copy.deepcopy(d["rows"][0]))),
        ("forge resident", lambda d: d["rows"][0].update(selected_in_d10=True)),
        ("forge bit", lambda d: d["rows"][0].update(coordinate="0" * 10)),
        ("forge ratification", lambda d: d.update(ratified_added=1)),
        ("edit tally", lambda d: d["counts"].update(total_name_kind_entries=71)),
        ("claim full lower dedup", lambda d: d["rows"][0].update(lower_D1_D8_semantic_dedup="NO-MATCH")),
        ("erase falsifier", lambda d: d["root_reviews"][0].update(falsifier="")),
        ("fake live oracle", lambda d: d["root_reviews"][1].update(oracle_status="SBCL-PASS")),
    ]
    for label, change in mutations:
        altered = copy.deepcopy(doc)
        change(altered)
        try:
            validate(altered)
        except CensusError:
            continue
        raise CensusError("negative mutation escaped: " + label)
    print("D10-CLHS-STREAMS: PASS 10/10 negative mutation controls")


def main() -> int:
    try:
        doc = json.loads(DATA.read_text(encoding="utf-8"))
        self_test(doc)
        print("D10-CLHS-STREAMS: PASS " + json.dumps(validate(doc), ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("D10-CLHS-STREAMS: BLOCK " + str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
