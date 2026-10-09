#!/usr/bin/env python3
"""Fail-closed owner L1-L7 source normalizer (#5144).

Reuses the existing COND AST reader, three-pass exact-domain emitter and T5
codec; it cannot publish .sens or establish semantic correctness by hashing.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
SCHEMA = "sens-owner-l1-l7-normalization/v1"
RETIRED = frozenset(("structural-kind", "identity-relation"))
HELPERS = frozenset(("equal?", "null"))
D3_PREDICATES = frozenset(("010", "101"))
BINARY_W8 = re.compile(r"[01]{8}\Z")


def load_existing(filename, name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    if spec is None or spec.loader is None:
        raise ValueError("missing canonical implementation: " + filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


reader = load_existing("cond-modernize.py", "l1_l7_owner_reader")


def d8_helpers():
    """Resolve D8 executable helper IDs from the real ratified domain table."""
    foundation = json.loads((ROOT / "knowledge/d1-d9-foundation.json").read_text())
    if foundation.get("status") != "owner-ratified":
        raise ValueError("L4: foundation lacks owner ratification")
    residents = foundation["domains"]["D8"]["residents"]
    roots = reader.parse((ROOT / "lib/domains/d8.lisp").read_text())
    out = {}
    for root in roots:
        # The file is (domain-table/1 (BITS ...fields) ...).
        for row in root.children[1:]:
            cells = row.children
            if not cells:
                continue
            bits = cells[0].atom
            if not isinstance(bits, str) or not BINARY_W8.fullmatch(bits):
                continue
            if bits not in residents:
                continue
            for field in cells[1:]:
                pair = field.children
                if len(pair) != 2 or pair[0].atom != "en":
                    continue
                name = pair[1].atom
                if name in HELPERS:
                    if name in out and out[name] != bits:
                        raise ValueError("L4: multiple admitted D8 coordinates")
                    out[name] = bits
    return out


def analyze(source, path, admitted_d8=None):
    """Pure syntax pass. Any uncertain rule blocks ALL edits to the file."""
    evidence, patches = [], []
    try:
        forms = reader.parse(source)
    except reader.Blocked as exc:
        return source, [{"rule": "L7", "status": "BLOCK", "reason": str(exc)}]

    def block(rule, form, reason):
        evidence.append({"rule": rule, "status": "BLOCK",
                         "line": form.line, "reason": reason})

    def visit(form):
        if form.opaque:
            return
        op = reader.head(form)
        if op in reader.QUOTE_HEADS:
            return
        if op in RETIRED:
            block("L5", form, "retired executable semantics; preserve archaeology")
        if op in HELPERS:
            bits = (admitted_d8 or {}).get(op)
            if bits is None or not BINARY_W8.fullmatch(bits):
                block("L4", form, "requires admitted D8 resident or generated D3-law proof")
            else:
                a = form.children[0]
                patches.append((a.start, a.end, bits))
                evidence.append({"rule": "L4", "status": "PATCH", "line": form.line,
                                 "resident": "D8:" + bits})
        if op in reader.LEGACY_COND:
            block("L1", form, "historical truthiness is not exact PredicateBit")
        if op == reader.CURRENT_COND:
            for clause in form.children[1:]:
                parts = clause.children
                if len(parts) != 2 or clause.atom is not None:
                    block("L1", clause, "COND needs proven two-part canonical clause")
                    continue
                q = parts[0]
                if q.atom == "t":
                    patches.append((q.start, q.end, "1"))
                    evidence.append({"rule": "L2", "status": "PATCH", "line": clause.line})
                elif q.atom in ("0", "1") or reader.head(q) in D3_PREDICATES:
                    evidence.append({"rule": "L1", "status": "TYPED-SYNTAX", "line": clause.line,
                                     "reason": "runtime PredicateBit proof still required"})
                else:
                    block("L1", clause, "COND test has no admitted exact PredicateBit proof")
        if form.children and isinstance(form.children[0].atom, str):
            if BINARY_W8.fullmatch(form.children[0].atom):
                block("L3", form, "source-era W8 executable head requires proof")
        for child in form.children:
            visit(child)

    for form in forms:
        visit(form)
    if patches and "fixtures" in Path(path).parts:
        evidence.append({"rule": "L6", "status": "BLOCK",
                         "reason": "regenerate old fixture with current canonical tool"})
    if any(x["status"] == "BLOCK" for x in evidence):
        return source, evidence
    normalized = source
    for start, end, value in sorted(patches, key=lambda e: e[0], reverse=True):
        normalized = normalized[:start] + value + normalized[end:]
    try:
        reader.parse(normalized)
    except reader.Blocked as exc:
        return source, evidence + [{"rule": "L7", "status": "BLOCK",
                                    "reason": "normalized source failed reparse: " + str(exc)}]
    return normalized, evidence


def pinned_source(relative):
    if relative.is_absolute() or ".." in relative.parts or relative.suffix != ".lisp":
        raise ValueError("L7: expected repository-relative .lisp path")
    path = ROOT / relative
    if not path.is_file() or path.is_symlink() or path.resolve() != path:
        raise ValueError("L7: missing/symlinked source")
    payload = path.read_bytes()
    blob = hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
    record = subprocess.run(["git", "ls-tree", "HEAD", "--", relative.as_posix()],
                            cwd=ROOT, capture_output=True, text=True, check=True).stdout
    if record.strip() != "100644 blob " + blob + "\t" + relative.as_posix():
        raise ValueError("L7: Git HEAD source blob differs from file; no rewrite")
    return payload.decode("utf-8"), blob


def project(normalized):
    mig = load_existing("migrate-three-pass.py", "l1_l7_existing_emitter")
    from sens_t5_codec import parse_words, encode_projection, decode_bytes, typed_sha256
    foundation = mig.load_foundation(ROOT / "knowledge/d1-d9-foundation.json")
    legacy, current, historical = mig.build_three_pass_maps(
        foundation,
        ROOT / "crates/sens/src/domain_surface_registry_generated.rs",
        ROOT / "crates/sens/src/semantic_registry_generated.rs",
        ROOT / "crates/sens/src/semantic_registry.rs",
        ROOT / "crates/sens/src/eval/necessary_forms_generated.rs",
        ROOT / "contracts/core1-historical-sid-map.lisp",
        ROOT / "knowledge/sens8-current-coverage-v1.json")
    resolver = mig.Resolver(legacy, current, historical, "current",
                            foundation["domains"]["D8"]["residents"])
    text7 = mig.build_text7(foundation, ROOT / "crates/sens/src/text7_projection_generated.rs")
    projection = mig.migrate_file(normalized, resolver, text7)
    if resolver.counts["passthrough-head"]:
        raise ValueError("L3: unresolved executable name -> BLOCK + D10 proposal")
    words = parse_words(projection)
    physical = encode_projection(projection)
    if decode_bytes(physical) != words:
        raise ValueError("L3: canonical exact word identity changed")
    return projection, typed_sha256(words), hashlib.sha256(physical).hexdigest()


def main(argv=None):
    arg = argparse.ArgumentParser(description=__doc__)
    arg.add_argument("source", type=Path)
    arg.add_argument("--oracle-typed-sha256")
    arg.add_argument("--oracle-reference")
    arg.add_argument("--stage", type=Path, help="external .words projection, never physical .sens")
    args = arg.parse_args(argv)
    report = {"schema": SCHEMA, "source": args.source.as_posix(),
              "status": "BLOCK", "published_sens": False, "evidence": []}
    try:
        source, blob = pinned_source(args.source)
        report["source_git_blob_sha"] = blob
        normalized, evidence = analyze(source, args.source.as_posix(), d8_helpers())
        report["evidence"] = evidence
        if any(x["status"] == "BLOCK" for x in evidence):
            raise ValueError("L1-L7: unproven case; no output")
        projection, typed, physical = project(normalized)
        report["typed_sha256"] = typed
        report["physical_preview_sha256"] = physical
        report["normalized_source_sha256"] = hashlib.sha256(normalized.encode()).hexdigest()
        if not args.oracle_typed_sha256 or not args.oracle_reference:
            raise ValueError("oracle: independent typed digest + witness reference mandatory")
        if not re.fullmatch(r"[0-9a-f]{64}", args.oracle_typed_sha256):
            raise ValueError("oracle: SHA256 must be 64 lowercase hex characters")
        if args.oracle_typed_sha256 != typed:
            raise ValueError("oracle: typed digest mismatch")
        report["oracle_reference"] = args.oracle_reference
        report["status"] = "DIGEST-MATCH-NOT-SEMANTIC-ADMISSION"
        if args.stage:
            out = args.stage.resolve()
            if out.is_relative_to(ROOT) or out.suffix != ".words":
                raise ValueError("stage: external .words only; physical .sens forbidden")
            with out.open("x", encoding="utf-8") as f:
                f.write(projection)
            report["staged"] = str(out)
    except Exception as exc:
        report["status"] = "BLOCK"
        report["reason"] = str(exc)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == "DIGEST-MATCH-NOT-SEMANTIC-ADMISSION" else 4


if __name__ == "__main__":
    raise SystemExit(main())
