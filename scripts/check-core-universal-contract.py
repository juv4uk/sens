#!/usr/bin/env python3
"""#1664 — executable checker for the Core1–4 universal foundation contract.

This is a *structural* checker: it validates that the contract states the
universal predicate/control law and that the shared corpus (#1709, living in
`tests/fixtures/semantic/`) actually carries that law. It decides no meaning of
its own — the law is Lisp-owned data and the corpus is Lisp-owned data; this
script only refuses to let either drift silently.

Named failures, fail-closed: any missing section, wrong law value, malformed
corpus row, or uncovered governing issue is reported by name and the process
exits non-zero.

Usage:
    python3 scripts/check-core-universal-contract.py [--quiet]
"""

from __future__ import annotations

import argparse
import glob
import os
import sys

CONTRACT = "contracts/core-universal-contract.lisp"
CORPUS_DIR = "tests/fixtures/semantic"

# (law section key, governing issue) — the corpus must carry each one.
GOVERNING = [
    ("predicate-answer", "#1699"),
    ("010", "#1704"),
    ("111", "#1705"),
    ("011", "#1713"),
    ("reader", "#1709"),
]

REQUIRED_SECTIONS = [
    "scope", "predicate-answer", "010", "111", "011", "reader",
    "shared-identities", "negative-laws", "profile-coverage",
]

EXPECTED_LAW = {
    "predicate-answer": {
        "predicate-answer": "one-bit", "yes": 1, "no": 0,
        "graded-answers": "forbidden",
        "partial-predicate-no-witness": [],
        "empty-no-witness-equals-no": "forbidden",
        "host-boolean-defines-semantics": "forbidden",
    },
    "010": {"compat-function8": "00000010", "empty-structure": 1,
            "non-pair": 1, "pair-structure": 0},
    "111": {"compat-function8": "00000011", "same-admitted-atom": 1,
            "distinct-admitted-atom": 0, "pair-operand": "named-error"},
    "011": {"compat-function8": "00000111", "clause-shape": "two-part",
            "test-1": "select", "test-0": "skip",
            "test-empty": "skip-no-witness", "zero-equals-empty": "forbidden",
            "other-test-value": "named-type-error",
            "unselected-expression": "not-evaluated",
            "exhaustion": [], "three-part-clause": "rejected"},
    "reader": {"malformed-source": "rejected-not-repaired"},
}

SHARED_IDENTITIES = ["00000001", "00000010", "00000011", "00000100",
                     "00000101", "00000110", "00000111"]

NEGATIVE_LAWS = ["graded-predicate-answer", "empty-equals-predicate-no",
                 "untyped-empty-as-truth", "structural-kind-substitution",
                 "host-truth-substitution"]

PROFILE_COVERAGE = {"native": "proven", "core3": "proven", "core2": "measured-blocked",
                    "core1": "not-yet-exercisable", "core4": "not-yet-exercisable"}

ROW_FIELDS = ["expect", "expr", "expected", "active", "name", "semantic-id", "governs", "note"]
ASSERTION_KINDS = {"expect-value", "expect-error", "expect-rejected"}


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
    if str(head) != "core-universal-contract/1":
        fail(f"{CONTRACT}: unexpected head {head!r} (want core-universal-contract/1)")

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

    for key, expected in EXPECTED_LAW.items():
        sec = sections.get(key)
        if sec is None:
            continue
        # Law sections nest their law table: ((key . ((field . value) ...))).
        # Exact-width D3 keys are quoted bit strings so leading zeroes survive.
        # A section whose own value is scalar keeps that scalar as a field.
        fields = {k: v for k, v in sec.items()}
        if isinstance(sec.get(key), list):
            fields.update(alist(sec[key]))
        for field, want in expected.items():
            got = fields.get(field)
            if isinstance(want, list):
                if not (isinstance(got, list) and len(got) == 0):
                    fail(f"{CONTRACT}: `{key}.{field}` = {got!r}, want empty list")
            elif got != want:
                fail(f"{CONTRACT}: `{key}.{field}` = {got!r}, want {want!r}")

    ids = sections.get("shared-identities", {}).get("shared-identities")
    if [as_str(x) for x in ids] != SHARED_IDENTITIES if isinstance(ids, list) else True:
        fail(f"{CONTRACT}: shared-identities = {ids!r}, want {SHARED_IDENTITIES}")

    neg = sections.get("negative-laws", {}).get("negative-laws")
    if not (isinstance(neg, list) and [str(x) for x in neg] == NEGATIVE_LAWS):
        fail(f"{CONTRACT}: negative-laws = {neg!r}, want {NEGATIVE_LAWS}")

    cov = sections.get("profile-coverage", {}).get("profile-coverage")
    cov_map = alist(cov) if isinstance(cov, list) else {}
    for prof, want in PROFILE_COVERAGE.items():
        if as_str(cov_map.get(prof)) != want:
            fail(f"{CONTRACT}: profile-coverage.{prof} = {cov_map.get(prof)!r}, want {want!r}")

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
            if not as_str(row.get("semantic-id", "")).strip():
                fail(f"{where}: empty semantic-id")
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

    verdict = ("(core-universal-contract-ok "
               f"(laws {len(EXPECTED_LAW)}) (governs {len(GOVERNING)}) "
               f"(corpus-rows {len(rows)}) "
               f"(profiles proven 2 measured-blocked 1 not-yet-exercisable 2))")
    print(verdict)
    return 0


if __name__ == "__main__":
    sys.exit(main())
