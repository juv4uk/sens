#!/usr/bin/env python3
"""L1–L7 migration preflight: reuse the *existing* three-pass AST reader.

Owner authority: https://github.com/juv4uk/sens/issues/5140
This is a read-only, fail-closed preflight, NOT an alternative parser, emitter
or semantic oracle. It never rewrites the source or stages physical .sens.

Positive normalization in this first slice: executable D3:110 COND (t expr)
to (1 expr), only after the rest of its two-part clauses have admitted exact
D1-producing syntax. Any other interpretation remains BLOCK.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
READER_PATH = ROOT / "scripts/migrate-three-pass.py"
# run_name != __main__: importing the AST code never starts a migration.
M = runpy.run_path(str(READER_PATH), run_name="l1_l7_reader")
Atom, ListNode, Quote = M["Atom"], M["ListNode"], M["Quote"]
MigrationError = M["MigrationError"]

QUOTE_HEADS = frozenset({"001", "00000001", "quote", "QUOTE"})
EXACT_COND = "110"
LEGACY_COND = frozenset({"COND", "cond", "00000111"})
RETIRED_HEADS = frozenset({"structural-kind", "identity-relation"})
LEGACY_HELPERS = frozenset({"equal?", "null"})
EXACT_D1 = frozenset({"0", "1"})


def call_head(node):
    if not isinstance(node, ListNode) or not node.items:
        return None
    head = node.items[0]
    return head.tok.text if isinstance(head, Atom) else None


def analyze(source: str) -> dict:
    """Classify source with no writes, while leaving QUOTE/data untouched."""
    raw_sha = hashlib.sha256(source.encode("utf-8")).hexdigest()
    try:
        stripped = M["strip_comments"](source)
        forms = M["Parser"](M["tokenize"](stripped)).parse_program()
    except (MigrationError, RecursionError, ValueError) as exc:
        return {"source_sha256": raw_sha, "status": "BLOCK",
                "findings": [{"law": "L7", "status": "OWNER_REVIEW",
                              "reason": str(exc)}],
                "normalized": None}

    findings = []
    replacements = []

    def note(law, status, node, reason):
        tok = node.tok if hasattr(node, "tok") else None
        loc = M["line_col"](stripped, tok.offset) if tok else (None, None)
        findings.append({"law": law, "status": status,
                         "line": loc[0], "column": loc[1],
                         "reason": reason})

    def d1_producer(node):
        if isinstance(node, Atom):
            return node.tok.text in EXACT_D1
        # ATOM (D3:010) is a total D1 predicate. EQ (D3:101) is partial;
        # do not claim EQ has an exact D1 result without an oracle/type proof.
        return (isinstance(node, ListNode) and node.tail is None
                and len(node.items) == 2 and call_head(node) == "010")

    def visit(node):
        if isinstance(node, Quote):
            return  # quoted source is data, not executable
        if not isinstance(node, ListNode):
            return
        if not node.items:
            return
        head = call_head(node)
        if head in QUOTE_HEADS:
            return
        if head in RETIRED_HEADS:
            note("L5", "BLOCK", node, "retired active semantics: archaeology review")
        if head in LEGACY_HELPERS:
            note("L4", "BLOCK", node, "needs proved D8 resident or generated D3 derivation")
        if head == EXACT_COND or head in LEGACY_COND:
            if node.tail is not None:
                note("L1", "BLOCK", node, "dotted COND has no admitted migration")
            for clause in node.items[1:]:
                if (not isinstance(clause, ListNode) or clause.tail is not None
                        or len(clause.items) != 2):
                    note("L1", "BLOCK", clause,
                         "not a two-part clause; historical comparison requires proof")
                    visit(clause)
                    continue
                query, body = clause.items
                if isinstance(query, Atom) and query.tok.text == "t":
                    if head != EXACT_COND:
                        note("L2", "BLOCK", query,
                             "legacy COND head must resolve to exact D3 before fallback rewrite")
                    else:
                        # AST token offset refers to comment-stripped source.
                        replacements.append((query.tok.offset, "t", "1"))
                        note("L2", "STAGE_ONLY", query,
                             "explicit exact D1:1 fallback; require independent oracle")
                elif not d1_producer(query):
                    note("L1", "BLOCK", query,
                         "test not statically proved to return only exact D1 1/0")
                visit(query)
                visit(body)
            return
        # Existing migrator resolves executable heads, source-era and bindings.
        # Never fabricate an L3 coordinate from spelling.
        for child in node.items:
            visit(child)
        if node.tail is not None:
            visit(node.tail)

    for form in forms:
        visit(form)

    normalized = stripped
    for offset, expected, replacement in sorted(replacements, reverse=True):
        if normalized[offset:offset + len(expected)] != expected:
            raise AssertionError("AST span drift: refusing a speculative rewrite")
        normalized = (normalized[:offset] + replacement
                      + normalized[offset + len(expected):])
    try:
        # Structural reparse with the same reader is mandatory.
        M["Parser"](M["tokenize"](normalized)).parse_program()
    except (MigrationError, RecursionError, ValueError) as exc:
        note("L7", "BLOCK", forms[0] if forms else None,
             f"normalized source does not reparse: {exc}")

    has_block = any(row["status"] == "BLOCK" for row in findings)
    return {"source_sha256": raw_sha,
            "status": "BLOCK" if has_block else "STAGE_ONLY",
            "findings": findings,
            "normalized_sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
            "normalized": normalized if not has_block else None,
            "oracle_status": "UNVERIFIED",
            "exact_domain_status": "NOT_EMITTED"}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", type=Path, help="one .lisp file; never rewritten")
    args = ap.parse_args(argv)
    if args.path.suffix != ".lisp" or not args.path.is_file():
        ap.error("input must be an existing .lisp file")
    try:
        content = args.path.read_text(encoding="utf-8")
        result = analyze(content)
    except UnicodeError as exc:
        result = {"status": "BLOCK",
                  "findings": [{"law": "L7", "status": "OWNER_REVIEW",
                                "reason": str(exc)}], "normalized": None}
    result["path"] = str(args.path)
    # Report only metadata, never suggest the normalized staging source is
    # production code or leak a partial candidate into the repo.
    result.pop("normalized", None)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 4 if result["status"] == "BLOCK" else 0


if __name__ == "__main__":
    sys.exit(main())
