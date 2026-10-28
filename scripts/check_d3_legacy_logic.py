#!/usr/bin/env python3
"""Read-only, fail-closed inventory of obsolete D3 COND/ATOM/EQ logic.

Scans tracked active Lisp source, not historical research or surface tables.
Does not inspect or define Rust evaluator semantics. This is only a
legacy-source migration inventory, never a SENS language-law oracle.

    python3 scripts/check_d3_legacy_logic.py --json
    python3 scripts/check_d3_legacy_logic.py --strict

Exit status: 0 no findings; 1 obsolete calls in --strict mode;
2 incomplete scan, parsing error, absent authority or inaccessible source.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import subprocess
import sys

OLD = {"00000010": "ATOM", "00000011": "EQ", "00000111": "COND"}
QUOTE = {"001", "00000001", "QUOTE", "quote", "як-є"}
CANONICAL = {"010": ("ATOM", 1), "101": ("EQ", 2)}
COND = {"110", "за-умовою"}
NON_D1 = {"T", "NIL", "t", "nil", "#t", "#f", "true", "false"}
SCHEMA = "sens-d3-legacy-logic-inventory/v1"


class Unscannable(ValueError):
    pass


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    line: int


@dataclass(frozen=True)
class Node:
    line: int
    atom: str | None = None
    children: tuple["Node", ...] = ()
    opaque: bool = False


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    operation: str
    rule: str
    detail: str


def tokenize(source: str) -> list[Token]:
    result: list[Token] = []
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
            depth, start = 1, line
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
                raise Unscannable(f"unclosed block comment at {start}")
            continue
        at = line
        if source.startswith("#;", i):
            result.append(Token("quote", "#;", at))
            i += 2
        elif source.startswith(("#'", ",@"), i):
            result.append(Token("quote", source[i:i + 2], at))
            i += 2
        elif c in "'`,":
            result.append(Token("quote", c, at))
            i += 1
        elif c in "()":
            result.append(Token(c, c, at))
            i += 1
        elif c == '"':
            i += 1
            while i < n:
                if source[i] == "\\":
                    i += 2
                elif source[i] == '"':
                    i += 1
                    break
                else:
                    if source[i] == "\n":
                        line += 1
                    i += 1
            else:
                raise Unscannable(f"unclosed string at {at}")
            result.append(Token("atom", "<string>", at))
        elif source.startswith("#\\", i):
            i += 2
            if i < n:
                i += 1
            while i < n and not source[i].isspace() and source[i] not in "();":
                i += 1
            result.append(Token("atom", "<character>", at))
        else:
            start = i
            while i < n and not source[i].isspace() and source[i] not in "();`\",": 
                i += 1
            if i == start:
                raise Unscannable(f"unsupported reader token at {at}")
            result.append(Token("atom", source[start:i], at))
    return result


def parse(source: str) -> tuple[Node, ...]:
    tokens = tokenize(source)
    i = 0

    def read(depth: int = 0) -> Node:
        nonlocal i
        if depth > 1024:
            raise Unscannable("S-expression nesting too deep")
        if i >= len(tokens):
            raise Unscannable("unexpected end of S-expression")
        tok = tokens[i]
        i += 1
        if tok.kind == ")":
            raise Unscannable(f"unexpected ')' at {tok.line}")
        if tok.kind == "quote":
            sub = read(depth + 1)
            return Node(tok.line, opaque=True, children=(sub,))
        if tok.kind == "atom":
            return Node(tok.line, atom=tok.value)
        children = []
        while True:
            if i >= len(tokens):
                raise Unscannable(f"unclosed '(' at {tok.line}")
            if tokens[i].kind == ")":
                i += 1
                return Node(tok.line, children=tuple(children))
            children.append(read(depth + 1))

    nodes = []
    while i < len(tokens):
        nodes.append(read())
    return tuple(nodes)


def scan_lisp(source: str, path: str) -> list[Finding]:
    findings = []
    stack = list(reversed(parse(source)))
    while stack:
        node = stack.pop()
        if node.opaque or not node.children:
            continue
        head = node.children[0].atom
        if head in QUOTE:
            continue  # quoted form is data, not a call
        args = node.children[1:]
        if head in OLD and args:
            findings.append(Finding(path, node.line, OLD[head], "LEGACY_W8_CALL",
                                    f"historical {head} in call-head position; review metadata context"))
        if head in CANONICAL:
            name, arity = CANONICAL[head]
            if len(args) != arity:
                findings.append(Finding(path, node.line, name, "D3_WRONG_ARITY",
                                        f"exact {head}: expected {arity}, found {len(args)}"))
        if head in COND:
            for clause in args:
                if clause.atom is not None or len(clause.children) != 2 or clause.opaque:
                    findings.append(Finding(path, clause.line, "COND", "COND_NOT_TWO_FIELDS",
                                            "exact D3 clause must be (test expression)"))
                elif clause.children[0].atom in NON_D1:
                    findings.append(Finding(path, clause.line, "COND", "COND_HOST_TRUTH",
                                            "literal host T/NIL/boolean is not exact D1 PredicateBit"))
        stack.extend(reversed(node.children))
    return findings


def is_live(path: str) -> bool:
    if not path.endswith(".lisp"):
        return False
    if path.startswith("lib/"):
        return not path.startswith(("lib/domains/", "lib/generated/", "lib/surface/"))
    if path.startswith("scripts/"):
        return not path.startswith(("scripts/research-", "scripts/archive/"))
    return path.startswith("crates/") and "/src/" in path


def tracked_paths(root: Path) -> list[str]:
    proc = subprocess.run(["git", "-C", str(root), "ls-files", "-z"],
                          capture_output=True, check=False)
    if proc.returncode:
        raise Unscannable("git ls-files failed: repository must be checked out (" +
                          proc.stderr.decode("utf-8", errors="replace").strip() + ")")
    return sorted(p.decode("utf-8") for p in proc.stdout.split(b"\0") if p)


def audit(root: Path) -> dict:
    paths = tracked_paths(root)
    active = [p for p in paths if is_live(p)]
    findings: list[Finding] = []
    errors = []
    for relative in active:
        path = root / relative
        try:
            if path.is_symlink() or not path.is_file():
                raise Unscannable("symlink or missing tracked file")
            findings.extend(scan_lisp(path.read_text(encoding="utf-8"), relative))
        except (Unscannable, UnicodeError, OSError, RecursionError) as exc:
            errors.append(f"{relative}: {exc}")
    if not active:
        errors.append("no tracked active Lisp source files; refusing false green")
    findings.sort(key=lambda f: (f.path, f.line, f.operation, f.rule))
    return {"schema": SCHEMA, "tracked_files": len(paths),
            "active_lisp_files_scanned": len(active) - sum(1 for e in errors if e.split(":", 1)[0] in active),
            "historical_and_metadata_not_semantically_scanned": sum(1 for p in paths if p.endswith(".lisp") and not is_live(p)),
            "runtime_mechanism_checked": False,
            "findings": [asdict(f) for f in findings], "errors": errors}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args(argv)
    try:
        report = audit(args.root.resolve())
    except (Unscannable, OSError, UnicodeError) as exc:
        print(f"INCOMPLETE: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for f in report["findings"]:
            print(f"{f['path']}:{f['line']}: {f['operation']} {f['rule']}: {f['detail']}")
        for e in report["errors"]:
            print(f"INCOMPLETE: {e}", file=sys.stderr)
        print(f"D3: checked {report['active_lisp_files_scanned']} live Lisp files; "
              f"{len(report['findings'])} finding(s); {len(report['errors'])} scan error(s); "
              f"{report['historical_and_metadata_not_semantically_scanned']} metadata/history files excluded")
    if report["errors"]:
        return 2
    return 1 if args.strict and report["findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
