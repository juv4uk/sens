#!/usr/bin/env python3
"""#1664 — executable checker for the Core1–4 universal foundation contract.

This is a *structural* checker: it validates that the contract states the
the sections and witness metadata of a Lisp-owned language contract.
It never compares language outcomes to Python-maintained truth tables; only
native SENS execution can establish the semantics.

Named structural failures, fail-closed: any missing section, malformed
corpus row, or uncovered governing issue is reported by name and the process
exits non-zero.

Usage:
    python3 scripts/check-core-universal-contract.py [--quiet]
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import sys

CONTRACT = "contracts/core-universal-contract.lisp"
CORPUS_DIR = "tests/fixtures/semantic"

# (law section key, governing issue) — the corpus must carry each one.
GOVERNING = [
    ("predicate-answer", "#1699"),
    ("010", "#1704"),
    ("101", "#1705"),
    ("110", "#1713"),
    ("reader", "#1709"),
]

REQUIRED_SECTIONS = [
    "scope", "predicate-answer", "010", "101", "110", "reader",
    "shared-identities", "negative-laws", "profile-coverage",
]

ROW_FIELDS = ["expect", "expr", "expected", "active", "name", "semantic-id", "governs", "note"]
ASSERTION_KINDS = {"expect-value", "expect-error", "expect-rejected"}
# Лише статичний захист метаданих. Семантичний вердикт дає SENS.
LEGACY_HEAD = re.compile(r"\(\s*(?:(?:sid8|sens8):)?[01]{8}(?=[\s()])", re.I)
EXACT_ID = re.compile(r"D([1-9]|10|11):([01]+)\Z")


# --------------------------------------------------------------------------
# minimal S-expression reader (comments, strings, lists, dotted pairs)
# --------------------------------------------------------------------------
class Sym(str):
    pass


class Dot:
    def __init__(self, a, b):
        self.a, self.b = a, b


def tokenize(text):
    toks, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c == ";":
            while i < n and text[i] != "\n":
                i += 1
        elif c in " \t\r\n":
            i += 1
        elif c in "()":
            toks.append(c); i += 1
        elif c == '"':
            i += 1
            buf = []
            while i < n and text[i] != '"':
                if text[i] == "\\" and i + 1 < n:
                    buf.append(text[i + 1]); i += 2
                else:
                    buf.append(text[i]); i += 1
            i += 1
            toks.append(("str", "".join(buf)))
        else:
            j = i
            while j < n and text[j] not in " \t\r\n();":
                j += 1
            toks.append(text[i:j]); i = j
    return toks


def parse(text):
    toks, pos = tokenize(text), 0

    def form():
        nonlocal pos
        t = toks[pos]; pos += 1
        if t == "(":
            items = []
            while toks[pos] != ")":
                items.append(form())
            pos += 1
            if len(items) == 3 and isinstance(items[1], Sym) and items[1] == ".":
                return Dot(items[0], items[2])
            return items
        if t == ")":
            raise ValueError("unexpected )")
        if isinstance(t, tuple) and t[0] == "str":
            return t[1]
        try:
            return int(t)
        except ValueError:
            return Sym(t)

    forms = []
    while pos < len(toks):
        forms.append(form())
    return forms


def alist(node):
    """Turn a list of dotted pairs into a dict keyed by symbol name."""
    out = {}
    for item in node:
        if isinstance(item, Dot):
            out[str(item.a)] = item.b
    return out


def as_str(v):
    return v if isinstance(v, str) else str(v)


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------
def check_contract(fail):
    if not os.path.isfile(CONTRACT):
        fail(f"contract missing: {CONTRACT}")
        return {}
    forms = parse(open(CONTRACT, encoding="utf-8").read())
    if not forms or not isinstance(forms[0], list):
        fail(f"{CONTRACT}: not a sectioned contract")
        return {}
    head = forms[0][0]
    if str(head) != "core-universal-contract-1":
        fail(f"{CONTRACT}: unexpected head {head!r} (want core-universal-contract-1)")

    sections = {}
    for node in forms[0][1:]:
        d = alist(node)
        if not d:
            fail(f"{CONTRACT}: empty section")
            continue
        key = next(iter(d))
        sections[key] = d

    for key in REQUIRED_SECTIONS:
        if key not in sections:
            fail(f"{CONTRACT}: missing section `{key}`")

    for key, issue in GOVERNING:
        sec = sections.get(key)
        if sec is None:
            continue
        if as_str(sec.get("governs")) != issue:
            fail(f"{CONTRACT}: `{key}` governs={sec.get('governs')!r}, want {issue}")

    return sections


def check_corpus(fail):
    files = sorted(glob.glob(os.path.join(CORPUS_DIR, "*-v1.lisp")))
    if not files:
        fail(f"corpus missing: no *-v1.lisp under {CORPUS_DIR}")
        return [], {}

    rows, by_issue = [], {}
    for path in files:
        for node in parse(open(path, encoding="utf-8").read()):
            if not isinstance(node, list):
                fail(f"{path}: row is not an alist")
                continue
            row = alist(node)
            where = f"{path}:{row.get('name', '<unnamed>')}"
            for field in ROW_FIELDS:
                if field not in row:
                    fail(f"{where}: missing `{field}`")
            kind = as_str(row.get("expect", ""))
            if kind not in ASSERTION_KINDS:
                fail(f"{where}: unknown assertion kind {kind!r}")
            governs = as_str(row.get("governs", ""))
            if not governs.startswith("#"):
                fail(f"{where}: unanchored governs {governs!r}")
            expr = row.get("expr")
            if not isinstance(expr, str) or isinstance(expr, Sym):
                fail(f"{where}: expr must contain a source string")
            elif LEGACY_HEAD.search(expr):
                fail(f"{where}: legacy SID8/Sens8 executable head in expr")
            semantic_id = row.get("semantic-id")
            identity = EXACT_ID.fullmatch(semantic_id) if isinstance(semantic_id, str) else None
            if semantic_id != "reader" and (identity is None or
                    len(identity.group(2)) != int(identity.group(1))):
                fail(f"{where}: semantic-id must be current exact domain coordinate")
            if not as_str(row.get("note", "")).strip():
                fail(f"{where}: empty note")
            rows.append(row)
            if row.get("active") is True or as_str(row.get("active")) == "t":
                by_issue.setdefault(governs, []).append(where)

    if len(rows) < 10:
        fail(f"corpus is too small to be a corpus: {len(rows)} rows")

    for key, issue in GOVERNING:
        if not by_issue.get(issue):
            fail(f"corpus covers no active row governed by {issue} (contract section `{key}`)")
    return rows, by_issue


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    failures = []
    fail = failures.append

    check_contract(fail)
    rows, by_issue = check_corpus(fail)

    if failures:
        print("core-universal-contract-violation")
        for f in failures:
            print(f"  - {f}")
        return 1

    # Structural inventory only; no Python verdict for SENS language laws.
    verdict = (f"(core-universal-contract-inventory "
               f"(sections {len(REQUIRED_SECTIONS)}) "
               f"(governs {len(GOVERNING)}) "
               f"(corpus-rows {len(rows)}))")
    print(verdict)
    return 0


if __name__ == "__main__":
    sys.exit(main())
