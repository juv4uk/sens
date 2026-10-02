#!/usr/bin/env python3
"""#2360 anti-collapse witness: shared behavior != shared semantic identity.

Research only. This script proves a deliberately narrow distinction:
- two current identities can be observationally equal on a bounded executable
  corpus;
- that evidence is insufficient to merge their semantic identities;
- explicit generation certificates remain a separate, stronger fact.

No production registry or runtime behavior is changed.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "lib" / "surface" / "semantic-registry.lisp"
GENEALOGY = ROOT / "experiments" / "function-genealogy.lisp"

ROW_RE = re.compile(r"^\s*\(([01]{8})\s+(.*)\)\s*$")
EN_RE = re.compile(r"\(en\s+([^\s()]+|\(\))\)")

EXPECTED_IDS = {
    "second": "00101111",
    "fourth": "00110001",
    "caar": "00110011",
    "cadr": "00110100",
    "cadddr": "00110110",
}

# There is intentionally no equivalence authority for these overlap pairs.
SEMANTIC_EQUIVALENCE: set[frozenset[str]] = set()

# Positive control: generation can be admitted without quotienting another
# identity. The merged selector certificate evidence is explicit.
GENERATED_CERTIFICATES = {
    "00110011": "#2345",
    "00110100": "#2345",
    "00110101": "#2345",
    "00110110": "#2345",
}


def registry_by_en() -> dict[str, str]:
    result: dict[str, str] = {}
    for line in REGISTRY.read_text(encoding="utf-8").splitlines():
        match = ROW_RE.match(line)
        if not match:
            continue
        identity, rest = match.groups()
        en = EN_RE.search(rest)
        if en and en.group(1) != "()":
            result[en.group(1)] = identity
    return result


def car(value):
    assert isinstance(value, tuple) and len(value) > 0
    return value[0]


def cdr(value):
    assert isinstance(value, tuple) and len(value) > 0
    return value[1:]


def second(value):
    return car(cdr(value))


def cadr(value):
    return car(cdr(value))


def fourth(value):
    return car(cdr(cdr(cdr(value))))


def cadddr(value):
    return car(cdr(cdr(cdr(value))))


def signature(fn, corpus):
    return tuple(fn(value) for value in corpus)


def may_semantic_merge(left: str, right: str) -> bool:
    if left == right:
        return True
    return frozenset((left, right)) in SEMANTIC_EQUIVALENCE


def may_mark_generated(identity: str) -> bool:
    return identity in GENERATED_CERTIFICATES


def main() -> None:
    registry = registry_by_en()
    for name, expected in EXPECTED_IDS.items():
        actual = registry.get(name)
        assert actual == expected, (name, actual, expected)

    assert registry["second"] != registry["cadr"]
    assert registry["fourth"] != registry["cadddr"]

    genealogy = GENEALOGY.read_text(encoding="utf-8")
    required_evidence = (
        "second and cadr have identical bodies",
        "cadddr is literally defined as the same closure object as fourth",
        "(00100111 00101111 genealogy-observes-like 00110100)",
        "(00100111 00110001 genealogy-observes-like 00110110)",
    )
    for needle in required_evidence:
        assert needle in genealogy, needle

    corpus = (
        ("a", "b", "c", "d", "e"),
        (("x", "y"), ("p", "q"), "r", "s", "t"),
        (0, 1, 2, 3, 4, 5),
        ("left", "middle", "right", "fourth-value"),
    )

    second_sig = signature(second, corpus)
    cadr_sig = signature(cadr, corpus)
    fourth_sig = signature(fourth, corpus)
    cadddr_sig = signature(cadddr, corpus)

    assert second_sig == cadr_sig
    assert fourth_sig == cadddr_sig

    naive_behavior_groups = {
        second_sig: {registry["second"], registry["cadr"]},
        fourth_sig: {registry["fourth"], registry["cadddr"]},
    }
    assert all(len(group) == 2 for group in naive_behavior_groups.values())

    # The critical guard: behavior-equivalence evidence is not semantic-
    # equivalence authority.
    assert not may_semantic_merge(registry["second"], registry["cadr"])
    assert not may_semantic_merge(registry["fourth"], registry["cadddr"])

    # Positive control: an explicit generation certificate is sufficient to
    # mark a specific identity generated without merging it with another ID.
    assert may_mark_generated(registry["caar"])
    assert may_mark_generated(registry["cadr"])
    assert may_mark_generated(registry["cadddr"])

    print("PAIR=second/cadr")
    print(f"IDS={registry['second']},{registry['cadr']}")
    print(f"BEHAVIOR-SIGNATURE-EQUAL={int(second_sig == cadr_sig)}")
    print("SEMANTIC-MERGE-ALLOWED=0")

    print("PAIR=fourth/cadddr")
    print(f"IDS={registry['fourth']},{registry['cadddr']}")
    print(f"BEHAVIOR-SIGNATURE-EQUAL={int(fourth_sig == cadddr_sig)}")
    print("SEMANTIC-MERGE-ALLOWED=0")

    print("POSITIVE-GENERATED-CONTROL=caar,cadr,cadddr")
    print("GENERATION-REQUIRES=EXPLICIT-CERTIFICATE")
    print("RULE=SHARED-BEHAVIOR-DOES-NOT-IMPLY-SHARED-IDENTITY")
    print("STATUS=PASS-BEHAVIOR-VS-IDENTITY-ANTI-COLLAPSE")
    print("AUTHORITY=RESEARCH-ONLY")


if __name__ == "__main__":
    main()
