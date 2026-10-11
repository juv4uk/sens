#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit-only SID8/SENS8 -> exact-domain projection from SENS authority tables.

Reads the 256 historical dispositions in knowledge/sens8-current-coverage-v1.json,
validates every eligible *single* target against the owner-ratified
knowledge/d1-d9-foundation.json and converts historical call heads only.

Output is an annotated .domain-view, NOT executable Lisp or physical .sens.
Use scripts/migrate.py for admitted .sens files after oracle/provenance checks.
Never modifies input. Fail-closed for W8 of unknown era, non-head W8,
compound/unproved legacy successors, malformed Lisp, and output collisions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
BIT8 = re.compile(r"[01]{8}\Z")
TARGET = re.compile(r"(D[1-9]):([01]+) ([^\s+|]+)")
ELIGIBLE = {"DIRECT-CURRENT-IDENTITY", "CURRENT-PROJECTION-DERIVED"}
SKIP_DIRS = {".git", "target", "node_modules", "vendor", "dist", "build", ".venv", "__pycache__"}


class Blocked(ValueError):
    pass


@dataclass(frozen=True)
class Token:
    kind: str
    word: str
    start: int
    end: int


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def load_authorities(root: Path):
    foundation_path = root / "knowledge/d1-d9-foundation.json"
    coverage_path = root / "knowledge/sens8-current-coverage-v1.json"
    fb, cb = foundation_path.read_bytes(), coverage_path.read_bytes()
    foundation, coverage = json.loads(fb), json.loads(cb)
    if foundation.get("status") != "owner-ratified" or coverage.get("status") != "AUDIT-COMPLETE":
        raise Blocked("missing owner-ratified foundation or audited historical dispositions")
    domains = foundation["domains"]
    rows = coverage.get("rows")
    if not isinstance(rows, list) or len(rows) != 256:
        raise Blocked("expected exactly 256 historical SID8 dispositions")
    all_rows = {}
    mapping = {}
    for row in rows:
        sid = row.get("legacy_code")
        if not isinstance(sid, str) or not BIT8.fullmatch(sid) or sid in all_rows:
            raise Blocked("invalid or duplicate legacy code in audited disposition table")
        all_rows[sid] = row
        classification = row.get("classification")
        if classification not in ELIGIBLE:
            continue
        target = row.get("current_target") or ""
        matches = TARGET.findall(target)
        if not matches or " + " in target or " | ".join(f"{d}:{b} {l}" for d, b, l in matches) != target:
            # Complex derived expressions are not a single word.
            continue
        if len(set(matches)) != 1:
            # Different Dn identities (even with the same human name) are ambiguous.
            continue
        domain, bits, label = matches[0]
        desc = domains.get(domain)
        if not desc or int(desc.get("width", -1)) != len(bits):
            raise Blocked(f"invalid target domain/width for {sid}: {target}")
        if desc.get("residents", {}).get(bits) != label:
            raise Blocked(f"legacy {sid} targets nonratified/different resident: {target}")
        if domain in {"D1", "D2", "D7"}:
            # Predicate outcomes, structural controls and phonemes are not call heads.
            continue
        mapping[sid] = f"{domain}:{bits}"
    if set(all_rows) != {f"{i:08b}" for i in range(256)}:
        raise Blocked("historical registry not a complete 256-code inventory")
    return mapping, all_rows, {"foundation": digest(fb), "legacy_coverage": digest(cb)}


def tokenize(source: str) -> list[Token]:
    """Lex without altering byte positions; comments and strings are inert."""
    out = []
    i, n = 0, len(source)
    while i < n:
        ch = source[i]
        if ch.isspace():
            i += 1
        elif ch == ";":
            at = source.find("\n", i)
            i = n if at < 0 else at + 1
        elif source.startswith("#|", i):
            start = i
            i += 2
            depth = 1
            while i < n and depth:
                if source.startswith("#|", i):
                    depth += 1; i += 2
                elif source.startswith("|#", i):
                    depth -= 1; i += 2
                else:
                    i += 1
            if depth:
                raise Blocked(f"unterminated block comment at offset {start}")
        elif ch == '"':
            start = i
            i += 1
            while i < n:
                if source[i] == "\\":
                    if i + 1 >= n:
                        raise Blocked(f"unterminated string escape at offset {start}")
                    i += 2
                elif source[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
            else:
                raise Blocked(f"unterminated string at offset {start}")
            out.append(Token("STRING", source[start:i], start, i))
        elif source.startswith(",@", i):
            out.append(Token("UNQUOTE", ",@", i, i + 2)); i += 2
        elif ch in "()'`,":
            kind = {"(": "LP", ")": "RP", "'": "QUOTE", "`": "BACKQUOTE", ",": "UNQUOTE"}[ch]
            out.append(Token(kind, ch, i, i + 1)); i += 1
        elif source.startswith("#'", i) or source.startswith("#(", i) or source.startswith("#\\", i):
            raise Blocked(f"unsupported reader syntax at offset {i}")
        else:
            start = i
            while i < n and not source[i].isspace() and source[i] not in "();'`\",":
                if source.startswith("#|", i):
                    break
                i += 1
            if start == i:
                raise Blocked(f"unknown reader token at offset {i}")
            out.append(Token("ATOM", source[start:i], start, i))
    return out


def project(source: str, mapping: dict[str, str], all_rows: dict, era: str):
    toks = tokenize(source)
    edits = []
    blocked = []
    observations = {"replaced": 0, "already_typed": 0, "nonhead_w8": 0, "unmapped_w8": 0}

    def visit(pos: int, quoted=False, head=False) -> int:
        if pos >= len(toks):
            raise Blocked("unexpected end of Lisp source")
        tok = toks[pos]
        if tok.kind in ("QUOTE", "BACKQUOTE", "UNQUOTE"):
            if tok.kind != "QUOTE":
                raise Blocked(f"reader syntax {tok.word} requires explicit semantic review at {tok.start}")
            return visit(pos + 1, quoted=True)
        if tok.kind == "RP":
            raise Blocked(f"unexpected ')' at offset {tok.start}")
        if tok.kind == "LP":
            i = pos + 1
            first = True
            quote_form = False
            while i < len(toks) and toks[i].kind != "RP":
                if first and toks[i].kind == "ATOM":
                    # QUOTE arguments are data; do not turn their words into calls.
                    quote_form = toks[i].word.upper() in {"QUOTE", "D3:001", "00000001"}
                i = visit(i, quoted=quoted or (quote_form and not first), head=first and not quoted)
                first = False
            if i >= len(toks):
                raise Blocked(f"unterminated list at offset {tok.start}")
            return i + 1
        if tok.kind == "STRING":
            return pos + 1
        if tok.kind == "ATOM":
            if BIT8.fullmatch(tok.word):
                if not head or quoted:
                    observations["nonhead_w8"] += 1
                    blocked.append((tok.start, tok.word, "UNPROVEN_W8_DATA_OR_VALUE"))
                elif era != "legacy":
                    blocked.append((tok.start, tok.word, "AMBIGUOUS_W8_SOURCE_ERA"))
                elif tok.word not in mapping:
                    observations["unmapped_w8"] += 1
                    row = all_rows[tok.word]
                    blocked.append((tok.start, tok.word, f"NO_SINGLE_RATIFIED_SUCCESSOR:{row['classification']}"))
                else:
                    edits.append((tok.start, tok.end, mapping[tok.word]))
            elif head and re.fullmatch(r"D[1-9]:[01]+", tok.word):
                observations["already_typed"] += 1
            return pos + 1
        raise Blocked(f"unexpected token {tok.word!r} at {tok.start}")

    i = 0
    while i < len(toks):
        i = visit(i)
    if blocked:
        return None, observations, [{"offset": o, "token": w, "reason": why} for o, w, why in blocked]
    output = source
    for start, end, replacement in reversed(edits):
        output = output[:start] + replacement + output[end:]
    observations["replaced"] = len(edits)
    # Independent lexical check: idempotent projection, with no remaining W8.
    if edits:
        output2, _, problems = project(output, mapping, all_rows, "auto")
        if problems or output2 != output:
            raise Blocked("post-projection verification failed")
    return output, observations, []


def files_at(path: Path):
    if path.is_symlink():
        raise Blocked("symlink inputs are not admitted")
    if path.is_file():
        if path.suffix != ".lisp":
            raise Blocked("input must be a .lisp file")
        return [path], path.parent
    if not path.is_dir():
        raise Blocked(f"missing input: {path}")
    return sorted(p for p in path.rglob("*.lisp")
                  if not p.is_symlink() and not (set(p.relative_to(path).parts) & SKIP_DIRS)), path


def run(args) -> int:
    mapping, all_rows, sha = load_authorities(args.root.resolve())
    if args.list_map:
        print("sid8\tlegacy_name\tclassification\ttarget")
        for sid, row in sorted(all_rows.items()):
            print(f"{sid}\t{row.get('legacy_name') or ''}\t{row.get('classification')}\t{mapping.get(sid) or ''}")
        return 0
    files, base = files_at(args.source.resolve())
    if not files:
        raise Blocked("no .lisp files to inspect")
    if args.write and args.out is None:
        raise Blocked("--write requires --out outside the source tree")
    if args.out is not None and args.out.resolve() == base.resolve():
        raise Blocked("output directory must differ from input directory")
    report = {"schema": "sid8-domain-projection/v1", "mode": "audit-only-not-physical-sens",
              "source_era": args.source_era, "authority_sha256": sha,
              "eligible_single_word_mappings": len(mapping), "files": []}
    errors = 0
    for path in files:
        rel = path.relative_to(base)
        row = {"path": rel.as_posix(), "status": "blocked"}
        try:
            blob = path.read_bytes()
            src = blob.decode("utf-8")
            converted, counts, problems = project(src, mapping, all_rows, args.source_era)
            row.update({"source_sha256": digest(blob), "counts": counts})
            if problems:
                row["blockers"] = problems
                errors += 1
            else:
                row["status"] = "projected" if counts["replaced"] else "unchanged"
                row["projection_sha256"] = digest(converted.encode("utf-8"))
                if args.write:
                    dest = args.out.resolve() / rel.with_suffix(".domain-view")
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    # Exclusive create: no input overwrite or preexisting output overwrite.
                    with dest.open("x", encoding="utf-8", newline="") as fh:
                        fh.write(converted)
                    row["output"] = str(dest)
        except (Blocked, OSError, UnicodeError) as exc:
            errors += 1
            row["blockers"] = [{"reason": str(exc)}]
        report["files"].append(row)
        print(f"{row['status']:>10}  {row['path']}: {row.get('counts', {}).get('replaced', 0)} replacements")
    report["summary"] = {"total": len(files), "blocked": errors,
                         "eligible": len(files) - errors, "converted_heads": sum(x.get("counts", {}).get("replaced", 0) for x in report["files"])}
    if args.report:
        path = args.report.resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
    print(json.dumps(report["summary"], ensure_ascii=False))
    return 2 if errors else 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path, nargs="?", help=".lisp file or directory")
    p.add_argument("--root", type=Path, default=ROOT, help="SENS repo root with authority tables")
    p.add_argument("--source-era", choices=("auto", "legacy", "current"), default="auto")
    p.add_argument("--list-map", action="store_true", help="show all 256 audited SID8 dispositions")
    p.add_argument("--out", type=Path, help="external preview output directory")
    p.add_argument("--write", action="store_true", help="write .domain-view only (never .sens)")
    p.add_argument("--report", type=Path, help="write JSON audit report (new path only)")
    args = p.parse_args(argv)
    if not args.list_map and args.source is None:
        p.error("source is required except with --list-map")
    try:
        return run(args)
    except (Blocked, OSError, KeyError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
