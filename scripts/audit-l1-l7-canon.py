#!/usr/bin/env python3
"""Fail-closed L1–L7 migration preflight, never a replacement for the oracle.

Reuses the existing three-pass migrator's source parser, resolver, exact-domain
encoder, and T5 codec; does not maintain a second ad-hoc Lisp grammar.
Read-only: source and physical .sens files are never created or overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MIGRATOR = ROOT / "scripts" / "migrate-three-pass.py"


def load_migrator():
    spec = importlib.util.spec_from_file_location("_sens_l1_l7_migrator", MIGRATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("existing three-pass migrator is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # required for dataclasses in imported module
    spec.loader.exec_module(module)
    return module


def parse(m: Any, source: str):
    return m.Parser(m.tokenize(m.strip_comments(source))).parse_program()


def render(m: Any, node: Any) -> str:
    """Syntax projection to feed the EXISTING encoder, not an output file."""
    if isinstance(node, m.Atom):
        return node.tok.text
    if isinstance(node, m.String):
        return node.tok.text
    if isinstance(node, m.Quote):
        return "'" + render(m, node.value)
    if isinstance(node, m.ListNode):
        items = " ".join(render(m, item) for item in node.items)
        if node.tail is not None:
            return "(" + items + " . " + render(m, node.tail) + ")"
        return "(" + items + ")"
    raise TypeError(type(node).__name__)


def inspect(m: Any, forms: list[Any]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Apply only owner L1–L7 rules for which transformation is unambiguous.

    Every unproved predicate type, legacy helper expansion, or retired meaning
    is a blocker. No implicit truthiness and no guessed D10 coordinate.
    """
    blockers: list[dict[str, str]] = []
    rewrites: list[dict[str, str]] = []
    predicates = {"atom", "eq", "not", "010", "101", "0100"}

    def block(rule: str, reason: str, node: Any):
        tok = getattr(node, "tok", None)
        blockers.append({
            "rule": rule,
            "reason": reason,
            "token": tok.text if tok is not None else "",
        })

    def walk(node: Any, quoted: bool = False):
        if quoted or isinstance(node, (m.Atom, m.String, m.Quote)):
            return
        if not isinstance(node, m.ListNode):
            raise TypeError(type(node).__name__)
        if not node.items:
            return
        head = node.items[0]
        if not isinstance(head, m.Atom):
            block("L3", "computed executable head needs an admitted call law", node)
            return
        name = head.tok.text
        lower = name.lower()

        if lower in {"structural-kind", "identity-relation"}:
            block("L5", "retired executable semantics: archive and remove from ACTIVE corpus by a reviewed change", head)
            return
        if name in {"equal?", "null", "null?"}:
            block("L4", "requires proved D8 role mapping or law-derived D3 expansion; spelling is not evidence", head)
            return
        if lower == "quote" or name == "001":
            # Both a shorthand quote and this special form are data.
            return
        if lower == "lambda" or name == "0010":
            # Parameter declarations are not executable calls.
            for body in node.items[2:]:
                walk(body)
            return
        if lower in {"define", "def"} or name == "0011":
            # DEFINE target is a binding, not a call head.
            for value in node.items[2:]:
                walk(value)
            return
        if lower == "cond" or name == "110":
            for clause in node.items[1:]:
                if not isinstance(clause, m.ListNode) or clause.tail is not None or len(clause.items) != 2:
                    block("L1", "COND requires a proper two-element (query result) clause", clause)
                    continue
                test, result = clause.items
                if isinstance(test, m.Atom) and test.tok.text == "t":
                    clause.items[0] = m.Atom(m.Tok("ATOM", "1", test.tok.offset))
                    rewrites.append({"rule": "L2", "before": "t", "after": "1"})
                elif isinstance(test, m.Atom) and test.tok.text in {"0", "1"}:
                    pass  # exact D1 predicate in query position
                elif (isinstance(test, m.ListNode) and test.items and
                      isinstance(test.items[0], m.Atom) and
                      test.items[0].tok.text.lower() in predicates):
                    walk(test)  # these ratified roles return an exact D1 predicate
                else:
                    block("L1", "COND query is not statically proved to produce exact D1 1/0", test)
                walk(result)
            return

        for argument in node.items[1:]:
            walk(argument)
        if node.tail is not None:
            walk(node.tail, quoted=True)

    for form in forms:
        walk(form)
    return blockers, rewrites


def strict_resolver_type(m: Any):
    class StrictResolver(m.Resolver):
        """No L3 unknown-head passthrough; retain original lexical binding routing."""

        def head(self, tok):
            words, status = super().head(tok)
            if status == "passthrough-head":
                raise m.MigrationError(
                    f"L3_UNMAPPED: {tok.text!r} has no proved executable domain coordinate",
                    tok,
                )
            return words, status

    return StrictResolver


def triage_source(m: Any, text: str, path: str, foundation: dict, maps: tuple, text7,
                  oracle: dict[str, Any] | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"path": path, "source_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}
    try:
        forms = parse(m, text)
    except m.MigrationError as exc:
        row.update(status="UNPARSEABLE_L7", rule="L7", reason=exc.message)
        return row

    blockers, rewrites = inspect(m, forms)
    row["normalizations"] = rewrites
    if path.startswith("tests/fixtures/") and rewrites:
        row.update(status="REGENERATE_L6", reason="fixture must be regenerated by canonical tooling, never hand edited")
        return row
    if blockers:
        row.update(status="BLOCK", blockers=blockers)
        if any(b["rule"] == "L5" for b in blockers):
            row["archaeology_required"] = True
        return row

    normalized = "\n".join(render(m, node) for node in forms) + ("\n" if forms else "")
    legacy, my, upper = maps
    resolver = strict_resolver_type(m)(legacy, my, upper, source_era="auto",
                          admitted_d8=foundation["domains"].get("D8", {}).get("residents", {}))
    try:
        projection = m.migrate_file(normalized, resolver, text7)
        # L3: the legacy migrator allows passthrough, this gate does not.
        if resolver.counts["passthrough-head"]:
            row.update(status="BLOCK", blockers=[{
                "rule": "L3",
                "reason": "unmapped executable head: require D1–D10 resident or owner D10 proposal, never passthrough",
                "count": resolver.counts["passthrough-head"],
            }])
            return row
        words = m.parse_words(projection)
        payload = m.encode_projection(projection)
        if m.decode_bytes(payload) != words:
            raise m.SensT5Error("codec failed exact-word roundtrip")
    except (m.MigrationError, m.SensT5Error, ValueError) as exc:
        token = getattr(getattr(exc, "tok", None), "text", "")
        row.update(status="BLOCK", blockers=[{
            "rule": "L3",
            "reason": str(exc),
            "token": token,
        }])
        if str(exc).startswith("L3_UNMAPPED:") and token:
            row["d10_proposal"] = {
                "source_head": token,
                "status": "OWNER_REVIEW_UNPLACED",
                "coordinate": None,
                "admission": "BLOCK",
            }
        return row

    row["physical_sha256"] = hashlib.sha256(payload).hexdigest()
    row["typed_word_sha256"] = m.typed_sha256(words)
    row["semantic_words"] = len(words)
    row["resolver_passes"] = resolver.counts
    row["status"] = "NEEDS_INDEPENDENT_ORACLE"
    if (path.startswith("tests/fixtures/") and
            any(resolver.counts.get(key, 0) for key in (
                "pass1-sens8", "pass2-my-lisp", "pass3-lisp15", "pass4-text7-global",
            ))):
        row.update(status="REGENERATE_L6", reason="regenerate migrated fixtures via canonical generator")
        return row
    if oracle is not None:
        # Digest agreement by itself does NOT certify observable semantic parity.
        if oracle.get("source_sha256") != row["source_sha256"]:
            row.update(status="BLOCK", blockers=[{"rule": "ORACLE", "reason": "source provenance mismatch"}])
        elif (oracle.get("physical_sha256") == row["physical_sha256"] and
              oracle.get("typed_word_sha256") == row["typed_word_sha256"]):
            row["status"] = "DIGEST_MATCH_ONLY"
        else:
            row.update(status="BLOCK", blockers=[{"rule": "ORACLE", "reason": "physical or typed digest mismatch"}])
    return row


def self_test(m: Any):
    ok = parse(m, "(cond ((atom (quote x)) (quote yes)) (t (quote ())))")
    blockers, changed = inspect(m, ok)
    assert not blockers and len(changed) == 1, (blockers, changed)
    assert "(1 (quote ()))" in render(m, ok[0])
    data = parse(m, "'(structural-kind x) (quote (equal? x))")
    assert not inspect(m, data)[0]
    assert inspect(m, parse(m, "(cond ((car x) yes))"))[0][0]["rule"] == "L1"
    assert inspect(m, parse(m, "(null x)"))[0][0]["rule"] == "L4"
    assert inspect(m, parse(m, "(identity-relation x)"))[0][0]["rule"] == "L5"
    try:
        parse(m, "(cond (t a)")
    except m.MigrationError:
        pass
    else:
        raise AssertionError("L7 parse failure was not detected")
    assert not inspect(m, parse(m, "(quote t)"))[1]
    print("L1-L7-PREFLIGHT-SELF-TEST: PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", nargs="?", type=Path, help="one .lisp file or directory")
    ap.add_argument("--report", type=Path, help="write a JSON-only report; no source or binary edits")
    ap.add_argument("--oracle-manifest", type=Path, help="optional JSON mapping source paths to independently pinned digests")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    m = load_migrator()
    if args.self_test:
        self_test(m)
        return 0
    if args.source is None:
        ap.error("source required unless --self-test")

    foundation = m.load_foundation(ROOT / "knowledge/d1-d9-foundation.json")
    maps = m.build_three_pass_maps(
        foundation,
        ROOT / "crates/sens/src/domain_surface_registry_generated.rs",
        ROOT / "crates/sens/src/semantic_registry_generated.rs",
        ROOT / "crates/sens/src/semantic_registry.rs",
        ROOT / "crates/sens/src/eval/necessary_forms_generated.rs",
        ROOT / "contracts/core1-historical-sid-map.lisp",
        ROOT / "knowledge/sens8-current-coverage-v1.json",
    )
    text7 = m.build_text7(foundation, ROOT / "crates/sens/src/text7_projection_generated.rs")
    oracle = json.loads(args.oracle_manifest.read_text(encoding="utf-8")) if args.oracle_manifest else {}

    base = args.source.resolve()
    if base.is_file():
        if base.suffix != ".lisp":
            ap.error("only .lisp source files are accepted")
        paths = [base]
        parent = base.parent
    elif base.is_dir():
        paths = sorted(m.source_files(base))
        parent = base
    else:
        ap.error(f"source not found: {base}")

    rows = []
    for p in paths:
        rel = p.relative_to(parent).as_posix()
        try:
            rows.append(triage_source(
                m, p.read_text(encoding="utf-8"), rel, foundation, maps, text7,
                oracle.get(rel),
            ))
        except UnicodeError as exc:
            rows.append({"path": rel, "status": "UNPARSEABLE_L7", "rule": "L7", "reason": str(exc)})

    summary = {"files_seen": len(rows)}
    for row in rows:
        key = row["status"]
        summary[key] = summary.get(key, 0) + 1
    report = {
        "schema": "sens-l1-l7-preflight/v1",
        "mode": "read-only-no-publication",
        "authority": "owner L1-L7; D1-D9 current foundation; D10 unknown => BLOCK",
        "reader": "existing migrate-three-pass Parser (Rust reader parity still required)",
        "semantic_proof": "independent execution oracle required before any admission",
        "summary": summary,
        "files": rows,
        "owner_review_unparseable": [r["path"] for r in rows if r["status"] == "UNPARSEABLE_L7"],
        "owner_review_blocked": [r["path"] for r in rows if r["status"] == "BLOCK"],
    }
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(serialized, encoding="utf-8")
    else:
        sys.stdout.write(serialized)
    return 0 if not any(r["status"] in {"BLOCK", "UNPARSEABLE_L7", "REGENERATE_L6"} for r in rows) else 2


if __name__ == "__main__":
    raise SystemExit(main())
