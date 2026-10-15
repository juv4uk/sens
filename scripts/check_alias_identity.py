#!/usr/bin/env python3
"""Guard: every human alias resolves to EXACTLY ONE identity (#5609, migration-empty-to-solution step 1).

Design note `migration-empty-to-solution.md` localized the non-identity-preserving
migration to the **alias -> admitted-surface resolution**: a Ukrainian alias can
resolve to an SID that is not the intended operation. This guard makes that class
of bug impossible to land:

A1  each spelling in the human slots (ук / укр / sa / sym) belongs to at most ONE
    identity -- two identities claiming the same alias is ambiguity and fails closed;
A2  an alias shared between identities must not silently pick one;
A3  the `en` slot of every identity is itself unique (no two identities share an
    English name) -- otherwise `en` is not a usable key either.

This is a structural check on the single surface registry; it decides no semantics.
Exit 0 = ALIAS_IDENTITY_OK; exit 1 = ALIAS_AMBIGUOUS.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

REGISTRY = "lib/surface/semantic-registry.lisp"
ENTRY = re.compile(r"^\s*\(([01]{8})\s+(.*)\)\s*$")
SLOT = re.compile(r'\((en|ук|укр|sa|sym)\s+(\(\)|"(?:\\.|[^"])*"|[^\s()]+)\)')
HUMAN = ("ук", "укр", "sa", "sym")


def decode(raw: str) -> str | None:
    if raw == "()":
        return None
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]
    return raw


def parse(text: str) -> list[tuple[str, dict[str, str | None]]]:
    out = []
    for line in text.splitlines():
        m = ENTRY.match(line)
        if not m:
            continue
        bits = m.group(1)
        slots = {k: decode(v) for k, v in SLOT.findall(m.group(2))}
        out.append((bits, slots))
    return out


def check(root: Path) -> list[str]:
    path = root / REGISTRY
    if not path.is_file():
        return [f"missing {REGISTRY}"]
    entries = parse(path.read_text(encoding="utf-8"))
    if not entries:
        return [f"no entries parsed from {REGISTRY}"]
    problems: list[str] = []

    # A1/A2 -- an alias must belong to at most one identity.
    owners: dict[tuple[str, str], list[str]] = defaultdict(list)
    for bits, slots in entries:
        for slot in HUMAN:
            v = slots.get(slot)
            if v:
                owners[(slot, v)].append(bits)
    for (slot, name), bits in sorted(owners.items()):
        if len(bits) > 1:
            problems.append(f"A1/A2: alias ({slot} {name}) claimed by {len(bits)} identities: "
                            f"{', '.join(sorted(bits))}")

    # A3 -- en names unique.
    en: dict[str, list[str]] = defaultdict(list)
    for bits, slots in entries:
        v = slots.get("en")
        if v:
            en[v].append(bits)
    for name, bits in sorted(en.items()):
        if len(bits) > 1:
            problems.append(f"A3: en name {name!r} shared by {len(bits)} identities: "
                            f"{', '.join(sorted(bits))}")

    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parents[1]))
    ns = ap.parse_args()
    root = Path(ns.root).resolve()
    try:
        problems = check(root)
    except OSError as exc:
        print(f"ALIAS_AMBIGUOUS: {exc}"); return 1
    if problems:
        print(f"ALIAS_AMBIGUOUS {len(problems)} problem(s):", flush=True)
        for p in problems:
            print(" -", p, flush=True)
        return 1
    print("ALIAS_IDENTITY_OK every human alias resolves to exactly one identity", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
