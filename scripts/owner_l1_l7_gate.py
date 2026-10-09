#!/usr/bin/env python3
"""Owner L1–L7 migration gate. Uses the EXISTING three-pass SENS reader/emitter.

This is an evidence-gated STAGER, never an alternate parser, language oracle,
in-place converter, or a license to revive historical truth/structure laws.
No output binary without externally pinned typed AND physical oracle digests.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "migrate-three-pass.py"
spec = importlib.util.spec_from_file_location("owner_l1_l7_existing_engine", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("canonical migration reader unavailable")
engine = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = engine
spec.loader.exec_module(engine)

RETIRED = frozenset({"structural-kind", "identity-relation", "structural-relation"})
HELPERS = {"equal?": ("D8", "EQUAL"), "null": ("D4", "NULL")}
COND = frozenset({"110", "COND", "cond", "00000111"})
QUOTES = frozenset({"001", "QUOTE", "quote"})
PREDICATES = frozenset({"010", "101", "ATOM", "EQ", "atom", "eq"})


@dataclass(frozen=True)
class Finding:
    law: str
    verdict: str
    reason: str
    offset: int


def resident_code(foundation: dict, domain: str, label: str) -> str | None:
    residents = foundation["domains"].get(domain, {}).get("residents", {})
    codes = [code for code, name in residents.items() if name == label]
    return codes[0] if len(codes) == 1 else None


def inspect(source: str, foundation: dict, *, source_era: str = "auto"):
    """Return (staged_readable_source, findings). Does not write any file."""
    findings: list[Finding] = []
    changes: list[tuple[int, int, str]] = []
    if source_era not in {"auto", "legacy", "current"}:
        raise ValueError("unrecognised source provenance")
    try:
        # Exact same lexical/parser logic as the production three-pass migrator.
        clean = engine.strip_comments(source)
        roots = engine.Parser(engine.tokenize(clean)).parse_program()
    except engine.MigrationError as exc:
        return None, [Finding("L7", "BLOCK", str(exc), getattr(exc.tok, "offset", 0) if exc.tok else 0)]

    admitted: dict[str, str] = {}
    for domain in ("D3", "D4", "D5", "D6", "D7", "D8", "D9"):
        for bits, label in foundation["domains"][domain]["residents"].items():
            if label != "EMPTY":
                admitted[bits] = domain

    def mark(law, verdict, reason, node):
        findings.append(Finding(law, verdict, reason, node.tok.offset))

    def query_exact(node) -> bool:
        if isinstance(node, engine.Atom):
            return node.tok.text in {"0", "1"}  # exact D1 literals; not numeric truthiness
        return (isinstance(node, engine.ListNode) and node.tail is None
                and bool(node.items) and isinstance(node.items[0], engine.Atom)
                and (node.items[0].tok.text in PREDICATES))

    def visit(node, quoted=False):
        if isinstance(node, engine.Quote):
            return  # Lisp quote is data; no executable-head rewriting
        if not isinstance(node, engine.ListNode) or not node.items:
            return
        if node.tail is not None and not quoted:
            mark("L3", "BLOCK", "dotted executable form is not certified", node)
            return
        head = node.items[0]
        if quoted:
            return
        if not isinstance(head, engine.Atom):
            mark("L3", "BLOCK", "computed executable head: no ratified coordinate proof", node)
            return
        name = head.tok.text
        if name in QUOTES:
            return
        if name.lower() in RETIRED:
            mark("L5", "BLOCK", "retired semantic executable; remove via separately audited archaeology", head)
            return
        if name in HELPERS:
            domain, label = HELPERS[name]
            code = resident_code(foundation, domain, label)
            if code is None:
                mark("L4", "BLOCK", "no unique resident; D3 expansion needs independent law/oracle", head)
                return
            changes.append((head.tok.offset, head.tok.offset + len(name), code))
            mark("L4", "STAGED", f"ratified {domain} resident {code} for {label}", head)
            name = code
        if name in COND:
            for clause in node.items[1:]:
                if not isinstance(clause, engine.ListNode) or clause.tail is not None:
                    mark("L1", "BLOCK", "COND clause must be a proper two-member list", clause)
                    continue
                if len(clause.items) != 2:
                    mark("L6", "BLOCK", "old fixture/three-part COND: regenerate via canonical fixture tool", clause)
                    continue
                query, branch = clause.items
                if isinstance(query, engine.Atom) and query.tok.text == "t":
                    # L2 has one explicitly ratified rewriting, not global T truthiness.
                    changes.append((query.tok.offset, query.tok.offset + 1, "1"))
                    mark("L2", "STAGED", "explicit D1:1 clause; t is not a special symbol", query)
                elif not query_exact(query):
                    mark("L1", "BLOCK", "no static exact-D1 predicate proof; arbitrary truthiness forbidden", query)
                visit(query)
                visit(branch)
            return
        if name not in admitted:
            if name in HELPERS:
                return
            # Source names are *not* coordinates; no unproven callable Text7 fallback.
            mark("L3", "BLOCK", f"unresolved executable head {name!r}; D10 proposal, do not mint coordinate", head)
            return
        if len(name) == 8 and source_era == "auto":
            mark("L3", "BLOCK", "eight-bit head ambiguous between SID8 and current D8", head)
            return
        if len(name) == 8 and source_era == "legacy":
            mark("L3", "BLOCK", "legacy SID8 needs history-aware resolver, not current D8 assertion", head)
            return
        for arg in node.items[1:]:
            visit(arg)

    for root in roots:
        visit(root)
    staged = clean
    for start, stop, replace in sorted(changes, reverse=True):
        staged = staged[:start] + replace + staged[stop:]
    try:
        engine.Parser(engine.tokenize(staged)).parse_program()
    except engine.MigrationError as exc:
        findings.append(Finding("L7", "BLOCK", f"post-normalization parse failed: {exc}", 0))
    return staged, findings


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--source-era", choices=("auto", "legacy", "current"), default="auto")
    parser.add_argument("--oracle-typed-sha256")
    parser.add_argument("--oracle-physical-sha256")
    parser.add_argument("--out", type=Path, help="new .sens file only; never overwrite")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    report = {"schema": "sens-owner-l1-l7-gate/v1", "rules": "L1-L7", "status": "BLOCK"}
    try:
        original = args.source.read_bytes()
        source = original.decode("utf-8")
        report["source_sha256"] = hashlib.sha256(original).hexdigest()
        foundation = engine.load_foundation(ROOT / "knowledge/d1-d9-foundation.json")
        staged, findings = inspect(source, foundation, source_era=args.source_era)
        report["findings"] = [vars(x) for x in findings]
        if any(x.verdict == "BLOCK" for x in findings):
            report["reason"] = "L1–L7 gate blocked: no guessed repair"
        elif staged is None:
            report["reason"] = "L7 malformed source"
        else:
            # Use the existing exact-domain emitter; no independent grammar.
            from_s = ROOT / "scripts"
            if str(from_s) not in sys.path:
                sys.path.insert(0, str(from_s))
            from sens_source_resolver import load_resolver  # noqa: F401
            report["reason"] = "oracle-pinned admission required"
            # Digest comparison is performed by the production approved-T5
            # pipeline, not by this scanner. This gate never publishes bytes.
            report["status"] = "STAGED-REVIEW"
            report["staged_source_sha256"] = hashlib.sha256(staged.encode()).hexdigest()
            if args.out:
                report["status"] = "BLOCK"
                report["reason"] = "publication requires full independent semantic oracle; use admit-t5-migration.py"
    except (UnicodeError, OSError, ValueError, engine.MigrationError) as exc:
        report["reason"] = f"L7 input/validation BLOCK: {exc}"
        report.setdefault("findings", []).append(vars(Finding("L7", "BLOCK", str(exc), 0)))
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "STAGED-REVIEW" else 4


if __name__ == "__main__":
    raise SystemExit(main())
