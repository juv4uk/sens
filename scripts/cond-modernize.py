#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fail-closed AST inventory and opt-in migration for Contract 11.8 D3 COND.

Pass 1: parse executable Lisp forms, excluding quotation/comments/strings;
classify exact-domain D3:110 vs historical SID8 COND, predicate carrier, and
YES/NO polarity. Legacy, NO, and unknown cases are HOLD, never rewritten.

Pass 2: for explicitly approved exact D3:110 + exact D3:010/101 + YES ONLY,
remove the obsolete expected field using AST byte spans. Reparse and verify
that ONLY those fields changed. No implicit truthiness, domain coercion, or
changes to historical source/provenance are permitted.

Default: READ-ONLY. Applying requires --apply and a DIFFERENT --out directory.
Mixed files with even one HOLD are refused as a whole. Output is NOT ratified,
runtime-proven, or merge-ready until independent witnesses and Hosted CI pass.

Example:
    python3 scripts/cond-modernize.py --scan lib --json
    python3 scripts/cond-modernize.py lib/file.lisp
    python3 scripts/cond-modernize.py lib/file.lisp --apply --out /tmp/review
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys


class Blocked(ValueError):
    pass


@dataclass(frozen=True)
class Tok:
    kind: str
    value: str
    start: int
    end: int
    line: int


@dataclass(frozen=True)
class Form:
    start: int
    end: int
    line: int
    atom: str | None = None
    children: tuple["Form", ...] = ()
    opaque: bool = False


def lex(source: str) -> list[Tok]:
    out = []
    i, line, n = 0, 1, len(source)
    while i < n:
        c = source[i]
        if c.isspace():
            if c == "\n":
                line += 1
            i += 1
            continue
        if c == ";":
            while i < n and source[i] != "\n":
                i += 1
            continue
        if source.startswith("#|", i):
            depth, at = 1, line
            i += 2
            while i < n and depth:
                if source.startswith("#|", i):
                    depth += 1
                    i += 2
                elif source.startswith("|#", i):
                    depth -= 1
                    i += 2
                else:
                    if source[i] == "\n":
                        line += 1
                    i += 1
            if depth:
                raise Blocked(f"unclosed block comment at {at}")
            continue
        at, start = line, i
        if source.startswith("#;", i):
            i += 2
            out.append(Tok("discard", "#;", start, i, at))
        elif source.startswith("#'", i):
            i += 2
            out.append(Tok("quote", "#'", start, i, at))
        elif c == "'":
            i += 1
            out.append(Tok("quote", "'", start, i, at))
        elif c in "()":
            i += 1
            out.append(Tok(c, c, start, i, at))
        elif source.startswith("#\\", i):
            i += 2
            if i < n:
                i += 1
            while i < n and not source[i].isspace() and source[i] not in "();":
                i += 1
            out.append(Tok("atom", source[start:i], start, i, at))
        elif c in ('"', '|'):
            delim = c
            i += 1
            closed = False
            while i < n:
                if source[i] == "\\":
                    i += 2
                    continue
                if source[i] == "\n":
                    line += 1
                if source[i] == delim:
                    i += 1
                    closed = True
                    break
                i += 1
            if not closed:
                raise Blocked(f"unclosed quoted token at {at}")
            out.append(Tok("atom", source[start:i], start, i, at))
        else:
            while i < n and not source[i].isspace() and source[i] not in "();":
                i += 1
            if i == start:
                raise Blocked(f"unsupported reader character at {at}")
            out.append(Tok("atom", source[start:i], start, i, at))
    return out


def parse(source: str) -> tuple[Form, ...]:
    tokens = lex(source)
    i = 0

    def read() -> Form:
        nonlocal i
        if i >= len(tokens):
            raise Blocked("unexpected end of S-expression")
        tok = tokens[i]
        i += 1
        if tok.kind == ")":
            raise Blocked(f"unexpected ')' at line {tok.line}")
        if tok.kind in ("quote", "discard"):
            inner = read()
            return Form(tok.start, inner.end, tok.line, opaque=True)
        if tok.kind != "(":
            return Form(tok.start, tok.end, tok.line, atom=tok.value)
        children: list[Form] = []
        while True:
            if i >= len(tokens):
                raise Blocked(f"unclosed '(' at line {tok.line}")
            if tokens[i].kind == ")":
                closing = tokens[i]
                i += 1
                return Form(tok.start, closing.end, tok.line,
                            children=tuple(children))
            children.append(read())

    result = []
    while i < len(tokens):
        result.append(read())
    return tuple(result)


QUOTE_HEADS = frozenset(("001", "00000001", "quote", "QUOTE"))
CURRENT_COND = "110"      # exact D3 bīja3 identity, not 8-bit SID8
LEGACY_COND = frozenset(("00000111", "cond", "COND"))
EXACT_D1_PRODUCERS = frozenset(("010", "101"))  # D3 ATOM and EQ
# Eight-bit 00100010 EQUAL is a known D1-result mechanism in some profiles,
# but it is not an exact three-bit D3 call and thus not auto-certified here.


@dataclass(frozen=True)
class Finding:
    line: int
    status: str
    reason: str
    cond: str
    producer: str
    expected: str
    start: int = 0
    end: int = 0


def head(form: Form) -> str:
    if form.opaque or not form.children:
        return ""
    return form.children[0].atom or ""


def expectation(form: Form) -> str:
    if form.atom in ("0", "1"):
        return "NO" if form.atom == "0" else "YES"
    children = form.children
    if len(children) == 1 and children[0].atom in ("0", "1"):
        return "NO" if children[0].atom == "0" else "YES"
    return "OTHER"


def inspect(source: str) -> tuple[list[Finding], tuple[Form, ...]]:
    roots = parse(source)
    result = []
    stack = list(reversed(roots))
    while stack:
        form = stack.pop()
        if form.opaque or head(form) in QUOTE_HEADS:
            continue
        children = form.children
        op = head(form)
        if op == CURRENT_COND or op in LEGACY_COND:
            for clause in children[1:]:
                parts = clause.children
                if not parts or len(parts) != 3:
                    continue
                query, expected, _branch = parts
                producer = head(query) or query.atom or "<computed>"
                polarity = expectation(expected)
                if op != CURRENT_COND:
                    status, reason = "HOLD", "legacy COND identity; requires an admitted bridge"
                elif producer not in EXACT_D1_PRODUCERS:
                    status, reason = "HOLD", "exact D1 producer not statically established"
                elif polarity == "NO":
                    status, reason = "HOLD", "negative branch requires proved D1 inversion"
                elif polarity != "YES":
                    status, reason = "HOLD", "expected result is not an explicit YES"
                else:
                    status, reason = "AUTO_YES", "exact D3 predicate and affirmative branch"
                result.append(Finding(clause.line, status, reason, op, producer,
                                      polarity, query.end, expected.end))
        stack.extend(reversed(children))
    return result, roots


def stage(source: str) -> tuple[str, list[Finding]]:
    findings, original = inspect(source)
    holds = [f for f in findings if f.status == "HOLD"]
    if holds:
        raise Blocked(f"{len(holds)} HOLD clause(s): no output; first is line "
                      f"{holds[0].line}: {holds[0].reason}")
    selected = [f for f in findings if f.status == "AUTO_YES"]
    if not selected:
        raise Blocked("no proven exact-D3 YES clauses; no output")
    patches = []
    for item in selected:
        between = source[item.start:item.end]
        if not between.isspace() and between.strip() not in ("0", "1", "(0)", "(1)"):
            raise Blocked(f"line {item.line}: comments or unexpected reader content in removal")
        patches.append((item.start, item.end, " "))
    result = source
    for start, end, replacement in sorted(patches, reverse=True):
        result = result[:start] + replacement + result[end:]
    rewritten, _ = inspect(result)
    if any(f.status == "AUTO_YES" for f in rewritten):
        raise Blocked("pass 2: eligible legacy clauses remained after rewrite")
    if any(f.status == "HOLD" for f in rewritten):
        raise Blocked("pass 2: HOLD clause appeared after rewrite")
    # All modifications are exact AST-identified intervals; every other byte
    # remains untouched. Round-trip parsing is required and runs in inspect().
    if len(parse(result)) != len(original):
        raise Blocked("pass 2: top-level form count changed")
    return result, selected


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("target", nargs="?", default=".")
    ap.add_argument("--scan", action="store_true", help="inventory only; never write")
    ap.add_argument("--json", action="store_true", help="machine-readable inventory")
    ap.add_argument("--apply", action="store_true", help="opt-in safe staging")
    ap.add_argument("--out", type=Path, help="distinct output directory, mandatory for --apply")
    args = ap.parse_args(argv)
    if args.apply and (args.scan or args.out is None):
        ap.error("--apply requires --out DIR and cannot be combined with --scan")
    if args.out and not args.apply:
        ap.error("--out is only allowed with --apply")
    target = Path(args.target)
    if not target.exists():
        ap.error(f"not found: {target}")
    if args.apply and not target.is_file():
        ap.error("--apply takes exactly one Lisp file")
    paths = sorted(target.rglob("*.lisp")) if target.is_dir() else [target]
    rows = []
    failures = []
    for p in paths:
        try:
            source = p.read_text(encoding="utf-8")
            findings, _ = inspect(source)
            for f in findings:
                rows.append({"path": str(p), "line": f.line, "status": f.status,
                             "reason": f.reason, "cond": f.cond,
                             "producer": f.producer, "expected": f.expected})
            if args.apply:
                result, selected = stage(source)
                output = args.out / p.name
                if output.resolve() == p.resolve():
                    raise Blocked("output must be different from source")
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(result, encoding="utf-8")
                print(f"STAGED {len(selected)} proven YES clauses → {output}",
                      file=sys.stderr)
        except (OSError, UnicodeError, Blocked, RecursionError) as exc:
            failures.append(f"{p}: {exc}")
    if args.json:
        print(json.dumps({"findings": rows, "errors": failures},
                         ensure_ascii=False, indent=2))
    else:
        for r in rows:
            print(f"{r['path']}:{r['line']}: {r['status']} "
                  f"{r['cond']}/{r['producer']} {r['expected']}: {r['reason']}")
        print(f"Inventory: {len(rows)} clauses; "
              f"{sum(r['status'] == 'HOLD' for r in rows)} HOLD; "
              f"{sum(r['status'] == 'AUTO_YES' for r in rows)} auto YES")
        for failure in failures:
            print(f"BLOCKED: {failure}", file=sys.stderr)
    return 2 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
