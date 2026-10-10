#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fail-closed review staging of legacy eight-bit CALL HEADS to D3-D6 words.

Issue #5029. This is NOT a semantic-admission publisher and never emits .sens.
The only successor authority is the existing owner-ratified three-pass
migration resolver. No second parser or 8-bit name/meaning table is created:
reuse cond-modernize.py's quotation-aware AST with source offsets.

Pass 1: replace proved executable old call heads; HOLD unknown, ambiguous or
historical COND (its clause semantics need separate Contract 11.8 proof).
Pass 2: reconstruct only the original AST-approved spans, and prove that every
other character (including quoted data, binders, strings and comments) is
identical. Output is a staged .lisp for REVIEW, not execution certification.

--scan lib/                read-only, per-file inventory
lib/file.lisp              read-only verdict; no output
lib/file.lisp --apply --out /tmp/review
--verify-only STAGED.lisp --original ORIGINAL.lisp
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SID = re.compile(r"[01]{8}$")
# The old expected-result field of COND is not equivalent to strict two-field
# D3. Operator replacement alone would silently change the program.
LEGACY_COND = "00000111"
QUOTE_HEADS = {"00000001", "001", "quote", "QUOTE"}
LAMBDA_HEADS = {"00001000", "0010", "lambda", "LAMBDA"}
DEFINE_HEADS = {"00001001", "0011", "define", "DEFINE"}


class Blocked(ValueError):
    pass


def import_tool(filename: str, module_name: str):
    path = SCRIPTS / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise Blocked("canonical tool unavailable: " + filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_parser():
    return import_tool("cond-modernize.py", "sens_cond_migration_ast")


def load_bridge(root: Path = ROOT) -> dict[str, str]:
    """Use current proved historical -> domain successors, never old Rust regex."""
    migration = import_tool("migrate-three-pass.py", "sens_canonical_three_pass")
    data = migration.load_foundation(root / "knowledge/d1-d9-foundation.json")
    legacy, _, _ = migration.build_three_pass_maps(
        data,
        root / "crates/sens/src/domain_surface_registry_generated.rs",
        root / "crates/sens/src/semantic_registry_generated.rs",
        root / "crates/sens/src/semantic_registry.rs",
        root / "crates/sens/src/eval/necessary_forms_generated.rs",
        root / "contracts/core1-historical-sid-map.lisp",
        root / "knowledge/sens8-current-coverage-v1.json",
    )
    result: dict[str, str] = {}
    for sid, identity in legacy.items():
        if identity is None:
            continue
        bits, domain = identity[:2]
        descriptor = data["domains"].get(domain)
        if domain not in {"D3", "D4", "D5", "D6"} or not descriptor:
            continue
        if len(bits) != int(descriptor["width"]) or bits not in descriptor["residents"]:
            raise Blocked("out-of-ratification successor for " + sid)
        result[sid] = bits
    if not result:
        raise Blocked("no current owner-proved successor map; refuse a false OK")
    return result


def approved_head_patches(source: str, bridge: dict[str, str]):
    parser = canonical_parser()
    try:
        forms = parser.parse(source)
    except parser.Blocked as exc:
        raise Blocked("canonical AST parse: " + str(exc)) from exc
    patches = []
    blockers = []

    def visit(form, executable: bool = True):
        if form.opaque or not form.children:
            return
        first = form.children[0]
        head = first.atom or ""
        if not executable:
            return
        if SID.fullmatch(head):
            if head == LEGACY_COND:
                blockers.append(f"line {form.line}: historical COND needs approved polarity/oracle")
            elif head not in bridge:
                blockers.append(f"line {form.line}: no proved successor for {head}")
            else:
                patches.append((first.start, first.end, head, bridge[head]))
        # Do not traverse quoted forms, even when the QUOTE head itself migrates.
        if head in QUOTE_HEADS:
            return
        # Binder and definition-name positions are DATA, not executable calls.
        # Only the lambda body or definition value can contain executable heads.
        if head in LAMBDA_HEADS or (SID.fullmatch(head) and bridge.get(head) == "0010"):
            children = form.children[2:]
        elif head in DEFINE_HEADS or (SID.fullmatch(head) and bridge.get(head) == "0011"):
            children = form.children[2:]
        else:
            children = form.children[1:] if first.atom else form.children
        for child in children:
            visit(child)
    for form in forms:
        visit(form)
    return patches, blockers


def stage(source: str, bridge: dict[str, str]):
    """Verify all edits against the original source and reparse candidate."""
    patches, blockers = approved_head_patches(source, bridge)
    if blockers:
        raise Blocked("; ".join(blockers[:6]) + (f"; +{len(blockers)-6} more" if len(blockers)>6 else ""))
    if not patches:
        raise Blocked("no proved legacy executable head to migrate")
    new = source
    for start, end, before, after in sorted(patches, key=lambda p: p[0], reverse=True):
        if source[start:end] != before:
            raise Blocked("AST span drift")
        new = new[:start] + after + new[end:]
    # Reconstruct EVERY non-edited character, not just token counts; collisions
    # in the successor map cannot falsify this exact projection check.
    pos = 0
    sections = []
    for start, end, before, after in sorted(patches):
        sections.append(source[pos:start])
        sections.append(after)
        pos = end
    sections.append(source[pos:])
    if new != "".join(sections):
        raise Blocked("pass 2: non-executable bytes changed")
    parser = canonical_parser()
    try:
        parser.parse(new)
    except parser.Blocked as exc:
        raise Blocked("pass 2: candidate AST invalid: " + str(exc)) from exc
    again, remaining = approved_head_patches(new, bridge)
    if remaining or again:
        raise Blocked("pass 2: old or unmapped executable call remains")
    return new, patches


def review(path: Path, bridge: dict[str, str]) -> dict:
    source = path.read_text(encoding="utf-8")
    changes, blockers = approved_head_patches(source, bridge)
    return {
        "path": str(path), "mapped_heads": len(changes),
        "blocked": len(blockers), "reasons": blockers[:12],
        "status": "BLOCK" if blockers else "READY_FOR_REVIEW" if changes else "NO_CHANGES",
        "semantic_parity": "NOT_VERIFIED", "physical_T5": "NOT_PUBLISHED",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("target", nargs="?", default="lib")
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--original", type=Path)
    args = ap.parse_args(argv)
    if args.scan and (args.apply or args.verify_only):
        ap.error("--scan is inventory only")
    if args.apply and (args.out is None or args.verify_only):
        ap.error("--apply requires --out DIR and cannot combine with --verify-only")
    if args.verify_only and (args.original is None or args.apply or args.out):
        ap.error("--verify-only needs --original ORIGINAL.lisp; a lone output proves nothing")
    if args.out and not args.apply:
        ap.error("--out is only permitted with --apply")

    try:
        bridge = load_bridge(ROOT)
        target = Path(args.target)
        if args.verify_only:
            original = args.original.read_text(encoding="utf-8")
            expected, _ = stage(original, bridge)
            actual = target.read_text(encoding="utf-8")
            if actual != expected:
                raise Blocked("review output differs from the exact approved head-only patch")
            print("SOURCE_DELTA_EXACT; runtime/oracle NOT_VERIFIED")
            return 0
        if args.scan:
            target = target if target.is_dir() else target.parent
            paths = sorted(target.rglob("*.lisp"))
        else:
            if not target.is_file():
                raise Blocked("single .lisp path required")
            paths = [target]
        rows = [review(path, bridge) for path in paths]
        for row in rows:
            print(json.dumps(row, ensure_ascii=False, sort_keys=True))
        if args.apply:
            row = rows[0]
            if row["status"] != "READY_FOR_REVIEW":
                raise Blocked("nothing safe to stage: " + row["status"])
            candidate, _ = stage(paths[0].read_text(encoding="utf-8"), bridge)
            output = args.out / paths[0].name
            if output.resolve() == paths[0].resolve():
                raise Blocked("refuse overwrite original")
            output.parent.mkdir(parents=True, exist_ok=True)
            # Atomic no-overwrite create. No in-place source edits and no .sens.
            with output.open("x", encoding="utf-8") as stream:
                stream.write(candidate)
            print("STAGED_FOR_REVIEW " + str(output))
        return 2 if any(row["status"] == "BLOCK" for row in rows) else 0
    except (Blocked, ValueError, OSError, UnicodeError) as exc:
        print("BLOCK: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
