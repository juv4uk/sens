#!/usr/bin/env python3
"""Research-only 1977 finite categorical version-space oracle. No D10 opcode admission."""
from __future__ import annotations

from itertools import product
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
NAME = "CANONICAL-VERSION-SPACE-BOUNDARIES"
BOTTOM = None  # a hypothesis that covers no observation; distinct from empty list/data
WILDCARD = "*"
MAX_INSTANCES = 64
MAX_HYPOTHESES = 4096


def canon_domains(domains):
    if not isinstance(domains, (list, tuple)) or not 1 <= len(domains) <= 4:
        raise ValueError("1..4 finite attribute domains required")
    out = []
    for column in domains:
        if not isinstance(column, (list, tuple)) or not column:
            raise ValueError("empty or malformed attribute domain")
        if any(type(x) is not str or not x or x in (WILDCARD, "⊥") for x in column):
            raise ValueError("reserved/invalid categorical value")
        if len(set(column)) != len(column):
            raise ValueError("duplicate category")
        out.append(tuple(sorted(column)))
    sizes = 1
    hyps = 1
    for row in out:
        sizes *= len(row)
        hyps *= 1 + len(row)
    if sizes > MAX_INSTANCES or hyps + 1 > MAX_HYPOTHESES:
        raise ValueError("bounded finite oracle only")
    return tuple(out)


def hyp_set(domains):
    return (BOTTOM,) + tuple(product(*(col + (WILDCARD,) for col in domains)))


def all_instances(domains):
    return tuple(product(*domains))


def covers(h, x):
    return h is not BOTTOM and len(h) == len(x) and all(v == WILDCARD or v == datum for v, datum in zip(h, x))


def ext(h, instances):
    return frozenset(x for x in instances if covers(h, x))


def key(h):
    return (0, ()) if h is BOTTOM else (1, h)


def admit_examples(domains, examples):
    instances = set(all_instances(domains))
    got = []
    seen = {}
    contradictory = False
    for row in examples:
        if not isinstance(row, (list, tuple)) or len(row) != 2:
            raise ValueError("each example must be (instance, D1-boolean)")
        x, flag = row
        if not isinstance(x, (list, tuple)) or type(flag) is not bool:
            raise ValueError("instance or label not well typed")
        t = tuple(x)
        if t not in instances:
            raise ValueError("example outside declared domain")
        if t in seen and seen[t] != flag:
            contradictory = True
        seen[t] = flag
        got.append((t, flag))
    return tuple(got), contradictory


def version_space(domains, examples):
    """Bounded explicit exact semantics, not the efficient streaming Mitchell algorithm."""
    dom = canon_domains(domains)
    ex, contradictory = admit_examples(dom, examples)
    all_i = all_instances(dom)
    good = tuple(h for h in hyp_set(dom) if all(covers(h, x) == label for x, label in ex))
    if not good:
        status = "CONTRADICTORY-OBSERVATIONS" if contradictory else "NO-CONSISTENT-CONJUNCTION"
        return {"status": status, "S": (), "G": (), "version_space": ()}
    extensions = {h: ext(h, all_i) for h in good}
    # S: no strictly more specific consistent hypothesis. G: no strictly more general one.
    specific = tuple(sorted((h for h in good if not any(extensions[k] < extensions[h] for k in good)), key=key))
    general = tuple(sorted((h for h in good if not any(extensions[k] > extensions[h] for k in good)), key=key))
    return {"status": "OK", "S": specific, "G": general, "version_space": good}


def reconstructed_from_boundaries(domains, S, G):
    dom = canon_domains(domains)
    all_i = all_instances(dom)
    Sx = tuple(ext(h, all_i) for h in S)
    Gx = tuple(ext(h, all_i) for h in G)
    return tuple(h for h in hyp_set(dom) if any(s <= ext(h, all_i) <= g for s in Sx for g in Gx))


def encoded_hyp(h):
    return {"bottom": True} if h is BOTTOM else {"conjunction": list(h)}


def verify_registry(root: Path = ROOT):
    dossier = json.loads((root / "knowledge/d10-mitchell-version-space-research-v1.json").read_text())
    assert dossier["status"] == "HOLD-CORE-VS-LIBRARY-UNRATIFIED"
    assert dossier["coordinate"] is None and dossier["ratified_resident"] is False
    assert dossier["selected_in_canonical_inventory"] is False
    assert dossier["physical_t5_authorized"] is False
    assert dossier["semantic_name"] == NAME
    inv = json.loads((root / "knowledge/d10-v1-semantic-inventory.json").read_text())
    fd = json.loads((root / "knowledge/d1-d9-foundation.json").read_text())
    existing = {r["semantic_name"].upper() for r in inv["rows"]}
    lower = {str(v).upper() for d in fd["domains"].values() for v in d["residents"].values()}
    assert NAME not in existing and NAME not in lower, "exact-name collision"
    assert len(inv["rows"]) == inv["accounting"]["selected_semantic_candidates"]
    assert inv["accounting"]["ratified_d10_residents"] == 0
    assert dossier["primary_source_url"].startswith("https://www.ijcai.org/")
    assert len(dossier["falsifiers"]) >= 4
    return len(inv["rows"])


def main():
    if "--self-test" in sys.argv:
        import unittest
        suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_d10_mitchell_version_space.py")
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        return 0 if result.wasSuccessful() else 1
    count = verify_registry()
    d = canon_domains([["dry", "wet"], ["bright", "dim"]])
    out = version_space(d, [(("dry", "bright"), True), (("dry", "dim"), False)])
    assert out["status"] == "OK"
    assert set(out["version_space"]) == set(reconstructed_from_boundaries(d, out["S"], out["G"]))
    print(f"D10 MITCHELL RESEARCH PASS selected={count} status=HOLD ratified=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
