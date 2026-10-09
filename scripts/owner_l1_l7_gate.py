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
        mapped_helper = name in HELPERS
        if mapped_helper:
            domain, label = HELPERS[name]
            code = resident_code(foundation, domain, label)
            if code is None:
                mark("L4", "BLOCK", "no unique resident; D3 expansion needs independent law/oracle", head)
                return
            changes.append((head.tok.offset, head.tok.offset + len(name), code))
            mark("L4", "STAGED", f"ratified {domain} resident {code} for {label}", head)
            name = code
        if name in COND:
            if name == "00000111":
                mark("L1", "BLOCK", "historical SID8 COND needs separately proven source-era mapping", head)
                return
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
        if len(name) == 8 and source_era == "auto" and not mapped_helper:
            mark("L3", "BLOCK", "eight-bit head ambiguous between SID8 and current D8", head)
            return
        if len(name) == 8 and source_era == "legacy" and not mapped_helper:
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
            # Existing three-pass exact-domain emitter and physical T5 codec.
            # No second source reader/encoder or host-truthiness adaptation.
            data = foundation
            legacy, my, upper = engine.build_three_pass_maps(
                data,
                ROOT / "crates/sens/src/domain_surface_registry_generated.rs",
                ROOT / "crates/sens/src/semantic_registry_generated.rs",
                ROOT / "crates/sens/src/semantic_registry.rs",
                ROOT / "crates/sens/src/eval/necessary_forms_generated.rs",
                ROOT / "contracts/core1-historical-sid-map.lisp",
                ROOT / "knowledge/sens8-current-coverage-v1.json",
            )
            text7 = engine.build_text7(
                data, ROOT / "crates/sens/src/text7_projection_generated.rs"
            )
            # An explicitly mapped EQUAL? D8 resident has exact current-domain
            # evidence; unrecognised raw W8 heads still fail during inspect().
            alias_d8 = any(f.law == "L4" and " D8 " in f.reason for f in findings)
            effective_era = "current" if alias_d8 else args.source_era
            resolver = engine.Resolver(
                legacy, my, upper, effective_era,
                data["domains"].get("D8", {}).get("residents", {}),
            )
            projection = engine.migrate_file(staged, resolver, text7)
            words = engine.parse_words(projection)
            payload = engine.encode_projection(projection)
            if engine.decode_bytes(payload) != words:
                raise ValueError("L1-L7: physical T5 roundtrip failed")
            typed_sha = engine.typed_sha256(words)
            physical_sha = hashlib.sha256(payload).hexdigest()
            report.update({
                "status": "STAGED-REVIEW",
                "reason": "independent oracle digests required; NOT semantic parity",
                "staged_source_sha256": hashlib.sha256(staged.encode()).hexdigest(),
                "exact_domain_projection": projection,
                "typed_word_sha256": typed_sha,
                "physical_sha256": physical_sha,
                "source_era_effective": effective_era,
            })
            oracle_pair = (args.oracle_typed_sha256, args.oracle_physical_sha256)
            if all(oracle_pair):
                if oracle_pair != (typed_sha, physical_sha):
                    report["status"] = "BLOCK"
                    report["reason"] = "independent oracle typed/physical digest mismatch"
                else:
                    report["status"] = "STAGED-ORACLE-MATCH"
                    report["reason"] = (
                        "digest equality confirmed; independent semantic oracle "
                        "provenance still required by admit-t5-migration.py"
                    )
                    if args.out:
                        # This preview gate must NOT publish physical binaries:
                        # only the existing transactional admission tool can do that.
                        report["status"] = "BLOCK"
                        report["reason"] = (
                            "no binary publication from preview gate: "
                            "use admit-t5-migration.py with independent witnesses"
                        )
            elif any(oracle_pair):
                report["status"] = "BLOCK"
                report["reason"] = "both independent oracle digests are required"
            if args.out and report["status"] == "STAGED-REVIEW":
                report["status"] = "BLOCK"
                report["reason"] = (
                    "unverified binary publication prohibited; "
                    "use admit-t5-migration.py"
                )
    except (UnicodeError, OSError, ValueError, engine.MigrationError) as exc:
        report["reason"] = f"L7 input/validation BLOCK: {exc}"
        report.setdefault("findings", []).append(vars(Finding("L7", "BLOCK", str(exc), 0)))
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "STAGED-ORACLE-MATCH" else 4


if __name__ == "__main__":
    raise SystemExit(main())
