#!/usr/bin/env python3
"""Fail-closed lexical preflight for SENS Lisp migration patches.

Uses existing three-pass parser, never a second Lisp reader or domain table.
A PASS verifies lexical context only, NOT runtime semantic equivalence.
Use --before old.lisp --after new.lisp or --git-base origin/main.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
MODULE = "_sens_migration_context_parser"
spec = importlib.util.spec_from_file_location(MODULE, SCRIPTS / "migrate-three-pass.py")
if spec is None or spec.loader is None:
    raise RuntimeError("SENS three-pass parser unavailable")
parser = importlib.util.module_from_spec(spec)
sys.modules[MODULE] = parser
spec.loader.exec_module(parser)

DEFINITIONS = {"00001001", "0011", "DEFINE", "define", "def"}
LAMBDAS = {"00001000", "0010", "LAMBDA", "lambda"}
QUOTES = {"00000001", "001", "QUOTE", "quote"}
LETS = {"001000", "001001", "LET", "LET*", "let", "let*"}
EXACT_WORD = re.compile(r"[01]{3,9}\Z")


class Blocked(ValueError):
    pass


def _head(x):
    if isinstance(x, parser.ListNode) and x.items and isinstance(x.items[0], parser.Atom):
        return x.items[0].tok.text
    return None


def _bound_names(forms):
    """Conservatively protect names defined or lexically bound in the source."""
    names = set()

    def visit(x):
        if isinstance(x, parser.Quote) or not isinstance(x, parser.ListNode):
            return
        op = _head(x)
        if op in DEFINITIONS and len(x.items) > 1:
            target = x.items[1]
            if isinstance(target, parser.Atom):
                names.add(target.tok.text)
            elif isinstance(target, parser.ListNode) and target.items:
                if isinstance(target.items[0], parser.Atom):
                    names.add(target.items[0].tok.text)
        if op in LAMBDAS and len(x.items) > 1:
            params = x.items[1]
            if isinstance(params, parser.ListNode):
                names.update(y.tok.text for y in params.items if isinstance(y, parser.Atom))
        if op in LETS and len(x.items) > 1:
            bindings = x.items[1]
            if isinstance(bindings, parser.ListNode):
                for b in bindings.items:
                    if isinstance(b, parser.ListNode) and b.items and isinstance(b.items[0], parser.Atom):
                        names.add(b.items[0].tok.text)
        for n, y in enumerate(x.items):
            if n == 1 and op in QUOTES:
                continue
            visit(y)
        if x.tail is not None:
            visit(x.tail)

    for form in forms:
        visit(form)
    return names


def _check(old, new, bindings, quoted=False, head=False):
    if type(old) is not type(new):
        raise Blocked("AST shape changed instead of call-head-only migration")
    if isinstance(old, parser.Atom):
        a, b = old.tok.text, new.tok.text
        if a == b:
            return
        if quoted:
            raise Blocked("quoted/data atom altered: " + a + " -> " + b)
        if not head:
            raise Blocked("non-head atom altered: " + a + " -> " + b)
        if a in bindings:
            raise Blocked("locally bound callable rewritten: " + a + " -> " + b)
        if not EXACT_WORD.fullmatch(b):
            raise Blocked("replacement not exact-domain binary: " + b)
        return
    if isinstance(old, parser.String):
        if old.tok.text != new.tok.text:
            raise Blocked("string payload changed")
        return
    if isinstance(old, parser.Quote):
        _check(old.value, new.value, bindings, quoted=True)
        return
    if isinstance(old, parser.ListNode):
        if len(old.items) != len(new.items) or ((old.tail is None) != (new.tail is None)):
            raise Blocked("list structure or argument count changed")
        op, newer = _head(old), _head(new)
        for i, (x, y) in enumerate(zip(old.items, new.items)):
            is_data = quoted or (i > 0 and (op in QUOTES or newer in QUOTES))
            _check(x, y, bindings, quoted=is_data, head=(i == 0 and not is_data))
        if old.tail is not None:
            _check(old.tail, new.tail, bindings, quoted=quoted)
        return
    raise Blocked("unknown existing parser node")


def audit_edit(before, after):
    old = parser.Parser(parser.tokenize(parser.strip_comments(before))).parse_program()
    new = parser.Parser(parser.tokenize(parser.strip_comments(after))).parse_program()
    if len(old) != len(new):
        raise Blocked("number of top-level forms changed")
    bound = _bound_names(old)
    for x, y in zip(old, new):
        _check(x, y, bound)
    return {"status": "LEXICAL_CONTEXT_ONLY", "forms": len(old),
            "protected_bindings": len(bound), "semantic_parity": "NOT_CHECKED"}


def _git(repo, *args):
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if proc.returncode:
        raise Blocked("git preflight unavailable: " + proc.stderr.decode(errors="replace"))
    return proc.stdout


def audit_git(root, base_ref):
    base = _git(root, "merge-base", base_ref, "HEAD").decode().strip()
    candidates = _git(root, "diff", "--name-only", "--diff-filter=M", "-z",
                      base, "HEAD", "--", "*.lisp")
    rows = []
    for raw in candidates.split(b"\0"):
        if not raw:
            continue
        name = raw.decode("utf-8")
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise Blocked("source missing or outside checkout: " + name)
        before = _git(root, "show", base + ":" + name).decode("utf-8")
        after = path.read_text(encoding="utf-8")
        try:
            rows.append({"path": name, **audit_edit(before, after)})
        except (Blocked, parser.MigrationError) as e:
            rows.append({"path": name, "status": "BLOCKED", "reason": str(e)})
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--before", type=Path)
    p.add_argument("--after", type=Path)
    p.add_argument("--git-base")
    p.add_argument("--repo", type=Path, default=ROOT)
    a = p.parse_args()
    try:
        if a.git_base and a.before is None and a.after is None:
            rows = audit_git(a.repo, a.git_base)
        elif a.git_base is None and a.before and a.after:
            rows = [{"path": str(a.after), **audit_edit(
                a.before.read_text(encoding="utf-8"),
                a.after.read_text(encoding="utf-8"))}]
        else:
            p.error("choose --git-base OR both --before and --after")
    except (Blocked, parser.MigrationError, UnicodeError, OSError) as e:
        rows = [{"status": "BLOCKED", "reason": str(e)}]
    blocked = sum(row["status"] == "BLOCKED" for row in rows)
    print(json.dumps({"status": "BLOCKED" if blocked else "LEXICAL_CONTEXT_ONLY",
                      "checked": len(rows), "blocked": blocked, "rows": rows},
                     ensure_ascii=False, indent=2))
    return int(blocked > 0)


if __name__ == "__main__":
    raise SystemExit(main())
