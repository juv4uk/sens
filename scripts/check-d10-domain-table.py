#!/usr/bin/env python3
"""D10 1024-row human surface proof against the immutable owner-ratified catalogue.

Checks all ten domain files for human surface collisions; does not admit runtime
instructions, revise D10 semantics or reinterpret D1–D9 contracts.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
import re
from pathlib import Path

from domain_tables import CURRENT_HUMAN_TABLES, D10_TABLE, read_domain_table

ROOT = Path(__file__).resolve().parents[1]
POINTER = ROOT / "knowledge/d10-current-inventory.json"
OWNER = ROOT / "knowledge/d10-owner-whole-domain-ratification-20261012.json"
CODE = re.compile(r"[01]{10}\Z")


def need(condition: bool, reason: str):
    if not condition:
        raise ValueError("D10_HUMAN_TABLE_BLOCK:" + reason)


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def source():
    pointer = json.loads(POINTER.read_text(encoding="utf-8"))
    owner = json.loads(OWNER.read_text(encoding="utf-8"))
    need(owner.get("ratified") is True and
         owner.get("ratification_mode") == "ATOMIC_WHOLE_DOMAIN_NOT_PER_RESIDENT",
         "owner domain ratification")
    need(pointer["canonical_current"]["path"] == owner["inventory"]["path"] and
         pointer["canonical_current"]["git_blob"] == owner["inventory"]["git_blob"],
         "current source pin")
    path = (ROOT / owner["inventory"]["path"]).resolve()
    need(path.is_relative_to(ROOT) and path.is_file(), "source path")
    raw = path.read_bytes()
    need(git_blob(raw) == owner["inventory"]["git_blob"], "source blob SHA")
    inventory = json.loads(raw)
    need(inventory["width"] == 10 and inventory["capacity"] == 1024 and
         len(inventory["rows"]) == 1024, "inventory extent")
    return inventory, owner


def check(d10, inventory, lower):
    expected = {row["coordinate"]: row for row in inventory["rows"]}
    need(len(expected) == 1024 and all(CODE.fullmatch(key) for key in expected),
         "source contains repeated or invalid 10-bit codes")
    need(len(d10) == 1024, "not 1024 Lisp domain rows")
    need([x.bits for x in d10] == [f"{i:010b}" for i in range(1024)],
         "missing, duplicated or unordered 10-bit coordinates")
    need(len(lower) == 1020, "D1–D9 lower-domain residents changed")

    distinct = {"uk": {}, "ukr": {}, "san": {}}
    for row in lower + d10:
        for column in distinct:
            value = getattr(row, column)
            if value is None:
                if row.domain == "D10":
                    need(False, "D10 missing " + column + " " + row.bits)
                continue
            before = distinct[column].get(value)
            need(before is None, "human surface collision " +
                 column + " " + value + ": " + str(before) + " and " +
                 row.domain + ":" + row.bits)
            distinct[column][value] = row.domain + ":" + row.bits

    for row in d10:
        original = expected[row.bits]
        name = original["semantic_name"]
        need(row.domain == "D10" and row.width == 10, "D10 width")
        need(row.lisp == name and row.en == name.lower(),
             "donor/English projection drift " + row.bits)
        need(bool(row.uk) and bool(row.ukr) and bool(row.san),
             "incomplete surface " + row.bits)
        need(len(row.uk) <= len(row.ukr), "compact Ukrainian longer than expanded")
        need(row.sym is None, "symbolic coordinate borrowed without authority")
        if name.endswith("?"):
            need(row.uk.endswith("?") and row.ukr.endswith("?") and
                 not row.san.endswith("?"), "predicate question marker " + row.bits)
        if name.endswith("!"):
            need(row.uk.endswith("!") and row.ukr.endswith("!") and
                 not row.san.endswith("!"), "mutation marker " + row.bits)
        if re.fullmatch(r"C[AD]{8}R", name):
            path = name[1:-1]
            need(row.uk == "-".join("п" if x == "A" else "р" for x in path) and
                 row.ukr == "-від-".join("перше" if x == "A" else "решта"
                                        for x in path) and
                 row.san == "-".join("ādi" if x == "A" else "śeṣa" for x in path),
                 "selector path translation changed " + row.bits)
    return {"D10": 1024, "D1_D9": 1020, "all_domains": 2044,
            "missing_uk": 0, "missing_ukr": 0, "missing_san": 0,
            "cross_domain_surface_collisions": 0, "word_width": 10,
            "owner_ratified_domain": True, "runtime_admitted_by_check": False}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--self-test", action="store_true")
    args = cli.parse_args()
    inventory, _ = source()
    others = []
    for table in CURRENT_HUMAN_TABLES:
        if table == D10_TABLE:
            continue
        others.extend(read_domain_table(table))
    d10 = read_domain_table(D10_TABLE)
    result = check(d10, inventory, others)

    if args.self_test:
        mutants = [
            ("wrong code", lambda xs: xs.__setitem__(
                1, replace(xs[1], bits=xs[0].bits))),
            ("wrong resident", lambda xs: xs.__setitem__(
                0, replace(xs[0], lisp="FORGED"))),
            ("missing Ukrainian", lambda xs: xs.__setitem__(
                0, replace(xs[0], uk=None))),
            ("colliding Sanskrit", lambda xs: xs.__setitem__(
                1, replace(xs[1], san=xs[0].san))),
            ("wrong selector path", lambda xs: xs.__setitem__(
                next(i for i, row in enumerate(xs)
                     if re.fullmatch(r"C[AD]{8}R", row.lisp or "")),
                replace(next(row for row in xs if re.fullmatch(
                    r"C[AD]{8}R", row.lisp or "")), uk="WRONG"))),
        ]
        for label, modify in mutants:
            fake = list(d10)
            modify(fake)
            try:
                check(fake, inventory, others)
            except ValueError:
                continue
            raise ValueError("D10_HUMAN_TABLE_BLOCK:accepted mutant " + label)
        result["negative_controls_rejected"] = len(mutants)
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
