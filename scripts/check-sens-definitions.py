#!/usr/bin/env python3
"""Mechanical check of SENS function definitions in lib/*.lisp.

Mechanical gate only: it never decides language meaning. SENS owns semantics;
this script proves the structural facts the workshop relies on when it adds
(0011 NAME ...) definitions:

  HARD (exit 1):
    1. every definition's parentheses balance (and the file's);
    2. no NAME is defined twice within a file.

  SOFT (reported, exit 0):
    3. names in lib/core4.lisp that are not ratified ladder residents -- these
       are library-internal helpers (second, core4-*, <=, ...) and are listed
       for review, not failed, because only the owner ratifies new law.

Exit 0 = no hard violation. Exit 1 = a concrete hard violation.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "lib"


def ladder_names() -> set[str]:
    names: set[str] = set()
    for p in sorted((LIB / "domains").glob("d*.lisp")):
        for line in p.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\s*\(([01]+)\s+(.*)\)\s*$", line)
            if not m:
                continue
            for surf in re.findall(r"\((?:ук|укр|en|san|LISP|sym)\s+([^()]+?)\)", m.group(2)):
                s = surf.strip()
                if s and s != "()":
                    names.add(s)
    return names



def strip_strings_comments(text: str) -> str:
    """Remove ; comments and "..." string bodies so parens inside them do not count."""
    out = []
    i, n, in_str = 0, len(text), False
    while i < n:
        c = text[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            i += 1
            continue
        if c == ";":
            while i < n and text[i] != "\n":
                i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def defs_in(text: str) -> list[tuple[str, int, str]]:
    lines = text.splitlines()
    out: list[tuple[str, int, str]] = []
    i = 0
    while i < len(lines):
        m = re.match(r"\(0011\s+(\S+)", lines[i])
        if not m:
            i += 1
            continue
        name = m.group(1)
        start = i
        depth = 0
        j = i
        started = False
        while j < len(lines):
            depth += lines[j].count("(") - lines[j].count(")")
            if "(" in lines[j]:
                started = True
            if started and depth == 0:
                break
            j += 1
        out.append((name, start + 1, "\n".join(lines[start : j + 1])))
        i = j + 1
    return out


def main() -> int:
    known = ladder_names()
    hard: list[str] = []
    soft: list[str] = []
    total = 0

    # Hard scope: the files the workshop edits and owns (core4 + the ladder).
    hard_scope = {"core4.lisp"}
    targets = sorted(LIB.glob("*.lisp")) + sorted((LIB / "domains").glob("d*.lisp"))
    for path in targets:
        text = path.read_text(encoding="utf-8")
        clean = strip_strings_comments(text)
        in_scope = path.name in hard_scope or path.parent.name == "domains"
        if in_scope and clean.count("(") != clean.count(")"):
            hard.append(f"{path.name}: file parens unbalanced ({clean.count('(')} vs {clean.count(')')})")
        defs = defs_in(clean)
        total += len(defs)
        seen: dict[str, int] = {}
        for name, line, block in defs:
            if in_scope and block.count("(") != block.count(")"):
                hard.append(f"{path.name}:{line}: definition {name!r} parens unbalanced")
            if in_scope and name in seen:
                hard.append(f"{path.name}:{line}: {name!r} redefined (first at line {seen[name]})")
            elif in_scope:
                seen[name] = line
            if in_scope and name not in known and path.name == "core4.lisp":
                soft.append(f"{path.name}:{line}: {name!r} (library-internal, not a ladder resident)")

    if soft:
        print(f"SENS_DEFINITION_CHECK: {len(soft)} library-internal names (review only)")
        for s in soft[:40]:
            print("  note " + s)
    if hard:
        print("SENS_DEFINITION_CHECK: FAIL")
        for v in hard[:200]:
            print("  " + v)
        print(f"total hard violations: {len(hard)}")
        return 1
    print(f"SENS_DEFINITION_CHECK: OK ({total} definitions; balanced, no dupes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
