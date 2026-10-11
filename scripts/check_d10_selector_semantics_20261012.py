#!/usr/bin/env python3
"""D10 selector-family constructive proof, separate from F1/F2/T5 runtime admission.

Checks pinned D9 ratified parents, the D10 law-derived seed, the full gauge
and current live D10 inventory. Proves extensional distinction *inside* the
256-member selector cohort on a complete depth-eight binary-pair witness.
Does not attest donor provenance, independent machine oracle or physical SENS.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "d9": ("knowledge/d9-ratified.json", "c615ee5026ecb61d5c6620ce4f8cb3e3367f1c48"),
    "seed": ("knowledge/d10-selector-seed.json", "ce1cfbaf2812010e1e4d0b5dfc9c36cbd9278a0c"),
    "gauge": ("knowledge/d10-v17-complete-research-gauge-20261012.json", "d923c115fae39fc2b63c9d8d9d06f2b0c39065ed"),
}
POINTER = "knowledge/d10-current-inventory.json"
OWNER = "knowledge/d10-owner-whole-domain-ratification-20261012.json"
BITS = re.compile(r"[01]{10}\Z")
SELECTOR = re.compile(r"C[AD]{8}R\Z")


def demand(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("D10_SELECTOR_PROOF_BLOCK:" + message)


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def pinned(root: Path, path: str, sha: str) -> dict:
    base = root.resolve()
    target = (base / path).resolve()
    demand(target.is_relative_to(base) and target.is_file(), "unsafe or missing " + path)
    raw = target.read_bytes()
    demand(git_blob(raw) == sha, "git SHA drift " + path)
    return json.loads(raw)


def pairs(depth: int, address: str = ""):
    """Total binary-pair witness: every depth-eight leaf carries its address."""
    if depth == 0:
        return address
    return (pairs(depth - 1, address + "A"),
            pairs(depth - 1, address + "D"))


def car(pair):
    demand(isinstance(pair, tuple) and len(pair) == 2, "CAR on non-pair")
    return pair[0]


def cdr(pair):
    demand(isinstance(pair, tuple) and len(pair) == 2, "CDR on non-pair")
    return pair[1]


def composed_selector(name: str, value):
    """D3 CAR/CDR composition: innermost selector is the rightmost letter."""
    demand(bool(re.fullmatch(r"C[AD]+R", name)), "malformed selector")
    for symbol in reversed(name[1:-1]):
        value = car(value) if symbol == "A" else cdr(value)
    return value


def verify(d9: dict, seed: dict, gauge: dict, live: dict,
           pointer: dict, owner: dict) -> dict:
    demand(d9.get("status") == "owner-ratified" and len(d9["rows"]) == 512,
           "D9 parent authority")
    demand(seed.get("schema") == "d10-selector-seed/v1" and
           seed.get("law", {}).get("name") == "selector-suffix-extension" and
           len(seed["rows"]) == 256, "selector seed/law")
    demand(owner.get("ratified") is True and
           owner.get("ratification_mode") == "ATOMIC_WHOLE_DOMAIN_NOT_PER_RESIDENT",
           "owner D10 whole-domain decision")
    demand(pointer["canonical_current"]["git_blob"] ==
           owner["inventory"]["git_blob"] and
           pointer["canonical_current"]["path"] == owner["inventory"]["path"],
           "owner and current inventory pin disagree")
    demand(len(gauge["rows"]) == len(live["rows"]) == 1024,
           "1024 inventory rows")

    by_d9 = {r["coordinate"]: r for r in d9["rows"]}
    by_gauge = {r["coordinate"]: r for r in gauge["rows"]}
    by_live = {r["coordinate"]: r for r in live["rows"]}
    demand(len(by_d9) == 512 and len(by_gauge) == len(by_live) == 1024,
           "repeated domain coordinates")

    # An independent address oracle does not call car/cdr or traverse pairs.
    address_oracle = {format(i, "08b").replace("0", "A").replace("1", "D"):
                      format(i, "08b").replace("0", "A").replace("1", "D")
                      for i in range(256)}
    witness = pairs(8)
    seen_ids: set[str] = set()
    seen_names: set[str] = set()
    seen_addresses: set[str] = set()
    children: dict[str, set[str]] = {}
    for row in seed["rows"]:
        code, name, sid = (row[k] for k in
                           ("coordinate", "semantic_name", "stable_id"))
        demand(bool(BITS.fullmatch(code)) and bool(SELECTOR.fullmatch(name)),
               "invalid 10-bit selector/name")
        demand(sid not in seen_ids and name not in seen_names,
               "duplicate selector ID/name")
        seen_ids.add(sid)
        seen_names.add(name)
        parent_code = row["parent_coordinate"]
        parent = by_d9.get(parent_code)
        demand(parent is not None and parent.get("status") == "OWNER-RATIFIED" and
               parent["resident"] == row["parent_semantic_name"] and
               parent["stable_id"] == row["parent_stable_id"],
               "wrong ratified D9 parent")
        suffix = row["generator_suffix_bit"]
        demand(suffix in ("0", "1") and
               row["generator_suffix_role"] == ("CAR/A" if suffix == "0" else "CDR/D"),
               "invalid generator bit/role")
        demand(code == parent_code + suffix and
               name == parent["resident"][:-1] + ("A" if suffix == "0" else "D") + "R",
               "D9→D10 generator law violated")
        children.setdefault(parent_code, set()).add(suffix)
        demand(row["coordinate_basis"] == "PROVED-SELECTOR-GENERATOR" and
               row["relation_class"] == "SEMANTIC-GENERATOR",
               "selector generator evidence changed")
        for candidate, kind in ((by_gauge.get(code), "gauge"),
                                (by_live.get(code), "live")):
            demand(candidate is not None and
                   candidate["stable_id"] == sid and
                   candidate["semantic_name"] == name,
                   kind + " coordinate identity drift")
        # Full eight-step composition and an independent direct-address oracle.
        address = name[1:-1][::-1]
        demand(address in address_oracle, "invalid selector address")
        actual = composed_selector(name, witness)
        demand(actual == address_oracle[address], "composition/address disagreement")
        outer = car(witness) if suffix == "0" else cdr(witness)
        demand(actual == composed_selector(parent["resident"], outer),
               "D9 parent/suffix composition disagreement")
        demand(actual not in seen_addresses, "two selectors alias on witness")
        seen_addresses.add(actual)
    demand(len(children) == 128 and all(bits == {"0", "1"}
                                        for bits in children.values()),
           "missing parent child or one-sided generator")
    demand(len(seen_addresses) == 256 and
           seen_addresses == set(address_oracle),
           "witness not separating all 256 functions")
    return {
        "schema": "d10-selector-constructive-proof/v1",
        "D9_ratified_parent_selectors": 128,
        "D10_selector_children_checked": 256,
        "D10_distinct_depth8_outputs": 256,
        "generator_errors": 0,
        "within_cohort_extensional_collisions": 0,
        "scope": "pair-tree-algebra-only",
        "donor_F1_independently_attested": False,
        "native_oracle_F2_verified": False,
        "global_D1_D10_F3_distinctness_verified": False,
        "physical_runtime_T5_admitted": False,
    }


def run(root: Path = ROOT, self_test: bool = False) -> dict:
    root = root.resolve()
    d9 = pinned(root, *FILES["d9"])
    seed = pinned(root, *FILES["seed"])
    gauge = pinned(root, *FILES["gauge"])
    pointer = json.loads((root / POINTER).read_text(encoding="utf-8"))
    owner = json.loads((root / OWNER).read_text(encoding="utf-8"))
    live = pinned(root, owner["inventory"]["path"],
                  owner["inventory"]["git_blob"])
    result = verify(d9, seed, gauge, live, pointer, owner)
    if self_test:
        mutations = [
            ("wrong generator suffix", "seed", lambda d:
                d["rows"][0].update(generator_suffix_bit="1")),
            ("wrong D9 parent", "seed", lambda d:
                d["rows"][0].update(parent_semantic_name="NOT-THE-PARENT")),
            ("incorrect coordinate", "seed", lambda d:
                d["rows"][0].update(coordinate="0000000000")),
            ("wrong semantic law", "seed", lambda d:
                d["rows"][0].update(semantic_name="CDDDDDDDDR")),
            ("forged gauge identity", "gauge", lambda d:
                d["rows"][271].update(semantic_name="FORGED")),
            ("forged live identity", "live", lambda d:
                next(r for r in d["rows"] if r["coordinate"] == "0110000000").update(
                    semantic_name="FORGED")),
        ]
        sources = dict(d9=d9, seed=seed, gauge=gauge, live=live,
                       pointer=pointer, owner=owner)
        for label, key, change in mutations:
            alternate = dict(sources)
            alternate[key] = copy.deepcopy(sources[key])
            change(alternate[key])
            try:
                verify(**alternate)
            except ValueError:
                pass
            else:
                raise ValueError("D10_SELECTOR_PROOF_BLOCK:mutation passed " + label)
        result["negative_controls_rejected"] = len(mutations)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(self_test=args.self_test), sort_keys=True, ensure_ascii=False))
