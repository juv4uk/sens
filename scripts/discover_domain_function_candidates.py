#!/usr/bin/env python3
"""Read-only, batched discovery of D1–D10 function candidates.

The exact domain tables supply identity. Active SENS source definitions and
research hits are supporting pointers, never proofs of meaning or callability.
The report is transient; this tool writes no files and creates no registry.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COLUMNS = ("ук", "укр", "san", "en", "LISP", "sym")
EXPECTED = {n: 1 << n for n in range(1, 12)}
# D11 — робочий домен розширення: наповнюється похідними за законом, тож
# повна зайнятість 2048 ще не вимагається (на відміну від ратифікованих D1–D10).
PARTIAL_DOMAINS = {11}
TEXT_SUFFIXES = {".lisp", ".lsp", ".scm", ".ss", ".sld", ".json", ".jsonl",
                 ".md", ".rst", ".txt", ".tsv", ".csv", ".py", ".rs", ".c", ".h", ".bits"}
TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9_?!*+/<>=:-]*")
MAX_RESEARCH_BYTES = 1_000_000


class AuditError(ValueError):
    pass


@dataclass(frozen=True)
class Quoted:
    value: str


SExpr = str | Quoted | list["SExpr"]


def skip_space_comments(text: str, i: int) -> int:
    while i < len(text):
        if text[i].isspace():
            i += 1
        elif text[i] == ";":
            end = text.find("\n", i)
            return len(text) if end < 0 else skip_space_comments(text, end + 1)
        else:
            break
    return i


def read_expr(text: str, i: int = 0) -> tuple[SExpr, int]:
    """Read the bounded S-expression subset used by one-line domain rows."""
    i = skip_space_comments(text, i)
    if i >= len(text):
        raise AuditError("expected expression, found EOF")
    ch = text[i]
    if ch == "(":
        values: list[SExpr] = []
        i += 1
        while True:
            i = skip_space_comments(text, i)
            if i >= len(text):
                raise AuditError("unterminated list")
            if text[i] == ")":
                return ("()" if not values else values), i + 1
            value, i = read_expr(text, i)
            values.append(value)
    if ch == ")":
        raise AuditError("unexpected closing parenthesis")
    if ch == '"':
        i += 1
        out: list[str] = []
        while i < len(text):
            if text[i] == "\\" and i + 1 < len(text):
                out.append(text[i + 1])
                i += 2
            elif text[i] == '"':
                return Quoted("".join(out)), i + 1
            else:
                out.append(text[i])
                i += 1
        raise AuditError("unterminated string")
    if ch in ("'", chr(96)):
        value, end = read_expr(text, i + 1)
        return ["quote" if ch == "'" else "quasiquote", value], end
    if ch == ",":
        prefix = 2 if text.startswith(",@", i) else 1
        value, end = read_expr(text, i + prefix)
        return ["unquote-splicing" if prefix == 2 else "unquote", value], end
    end = i
    while end < len(text) and not text[end].isspace() and text[end] not in '();"':
        end += 1
    if end == i:
        raise AuditError(f"bad token at offset {i}")
    return text[i:end], end


def plain(value: SExpr) -> str:
    if isinstance(value, Quoted):
        return value.value
    if isinstance(value, str):
        return value
    return "()" if value == [] else "<compound>"


def parse_domain_row(line: str, domain: int, line_no: int) -> dict[str, Any] | None:
    try:
        form, _ = read_expr(line)
    except AuditError as exc:
        if re.match(r"^\s*\([01]+\s", line):
            raise AuditError(f"lib/domains/d{domain}.lisp:{line_no}: {exc}") from exc
        return None
    if not isinstance(form, list) or not form or not isinstance(form[0], str):
        return None
    word = form[0]
    if not re.fullmatch(r"[01]+", word):
        return None
    if len(word) != domain:
        raise AuditError(f"D{domain} line {line_no}: width={len(word)}, expected={domain}, code={word}")
    if len(form) != 7:
        raise AuditError(f"D{domain}:{word} line {line_no}: expected six surface columns")
    row: dict[str, Any] = {"domain": domain, "bits": word, "line": line_no}
    for col, node in zip(COLUMNS, form[1:]):
        if not isinstance(node, list) or len(node) != 2 or node[0] != col:
            raise AuditError(f"D{domain}:{word} line {line_no}: malformed {col} column")
        row[col] = plain(node[1])
        row[col + "_quoted"] = isinstance(node[1], Quoted)
    return row


def load_domain_tables(root: Path) -> dict[int, list[dict[str, Any]]]:
    """Verify exact-width keys, complete occupancy and uniqueness."""
    result = {}
    for domain in range(1, 12):
        path = root / "lib" / "domains" / f"d{domain}.lisp"
        if not path.is_file() or path.is_symlink():
            raise AuditError(f"missing or symlinked table: {path.relative_to(root)}")
        rows = []
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            row = parse_domain_row(line, domain, line_no)
            if row is not None:
                rows.append(row)
        words = [row["bits"] for row in rows]
        expected = {format(i, f"0{domain}b") for i in range(1 << domain)}
        duplicates = sorted({word for word in words if words.count(word) > 1})
        missing = sorted(expected - set(words))
        unexpected = sorted(set(words) - expected)
        partial = domain in PARTIAL_DOMAINS
        if duplicates or unexpected or (not partial and (missing or len(rows) != EXPECTED[domain])):
            raise AuditError(f"D{domain} shape: rows={len(rows)}/{EXPECTED[domain]}, "
                             f"duplicates={duplicates[:4]}, missing={missing[:4]}, unexpected={unexpected[:4]}")
        result[domain] = rows
    return result


def mask_comments_and_strings(text: str) -> str:
    """Blank comments/strings while preserving offsets, newlines and code."""
    out = list(text)
    i = 0
    in_string = False
    while i < len(text):
        ch = text[i]
        if in_string:
            if ch == "\\" and i + 1 < len(text):
                if out[i] != "\n":
                    out[i] = " "
                if out[i + 1] != "\n":
                    out[i + 1] = " "
                i += 2
                continue
            if ch == '"':
                in_string = False
            if ch != "\n":
                out[i] = " "
            i += 1
            continue
        if ch == '"':
            out[i] = " "
            in_string = True
            i += 1
            continue
        if ch == ";":
            while i < len(text) and text[i] != "\n":
                out[i] = " "
                i += 1
            continue
        i += 1
    return "".join(out)


def read_atom(text: str, i: int) -> tuple[str, int]:
    while i < len(text) and text[i].isspace():
        i += 1
    start = i
    while i < len(text) and not text[i].isspace() and text[i] not in "()":
        i += 1
    return text[start:i], i


def find_active_sens_definitions(root: Path) -> dict[str, list[str]]:
    """Index top-level SENS DEFINE forms; comments, strings and nested forms are ignored."""
    found: dict[str, set[str]] = {}
    library = root / "lib"
    if not library.is_dir():
        return {}
    for path in sorted(library.rglob("*.lisp")):
        if path.is_symlink() or "domains" in path.relative_to(library).parts:
            continue
        try:
            source = mask_comments_and_strings(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError):
            continue
        depth = 0
        i = 0
        while i < len(source):
            if source[i] == "(":
                if depth == 0:
                    prev = i - 1
                    while prev >= 0 and source[prev].isspace():
                        prev -= 1
                    if prev < 0 or source[prev] not in ("'", chr(96), ","):
                        head, after = read_atom(source, i + 1)
                        if head == "0011":
                            name, _ = read_atom(source, after)
                            if name and name not in {"()", "."} and not re.fullmatch(r"[01]+", name):
                                found.setdefault(name.casefold(), set()).add(path.relative_to(root).as_posix())
                depth += 1
            elif source[i] == ")":
                depth = max(0, depth - 1)
            i += 1
    return {name: sorted(paths) for name, paths in found.items()}


def aliases(row: dict[str, Any]) -> list[str]:
    found = []
    for col in ("ук", "укр", "san", "en", "LISP"):
        value = row[col]
        if row[col + "_quoted"] or value in {"", "()", "<compound>"}:
            continue
        if not re.fullmatch(r"[01]+", value):
            found.append(value)
    return sorted(set(found), key=str.casefold)


D3_ROLE = {
    "000": "structural-empty-not-a-function", "001": "quote-special-form",
    "010": "predicate-function-candidate", "011": "selector-function-candidate",
    "100": "selector-function-candidate", "101": "predicate-function-candidate",
    "110": "conditional-special-form", "111": "constructor-function-candidate",
}
D4_ROLE = {
    "0000": "evaluator-mechanism-candidate", "0001": "evaluator-mechanism-candidate",
    "0010": "syntax-form-lambda", "0011": "syntax-form-define",
    "0100": "predicate-function-candidate", "0101": "predicate-function-candidate",
    "0110": "selector-function-candidate", "0111": "selector-function-candidate",
    "1000": "selector-function-candidate", "1001": "selector-function-candidate",
    "1010": "environment-mechanism-candidate", "1011": "environment-mechanism-candidate",
    "1100": "evaluator-mechanism-candidate", "1101": "evaluator-mechanism-candidate",
    "1110": "list-constructor-function-candidate", "1111": "list-operation-function-candidate",
}
D5_PROTOCOLS = {"EVALQUOTE", "FUNCTION", "FEXPR", "MACRO", "LABEL", "PROG", "GO", "RETURN"}
NON_FUNCTION_DOMAINS = {
    1: "predicate-bit-not-a-function-table",
    2: "structure-not-a-function-table",
    7: "text-data-never-callable",
}


def classify(row: dict[str, Any]) -> tuple[str, bool]:
    domain, bits = row["domain"], row["bits"]
    if domain in NON_FUNCTION_DOMAINS:
        return NON_FUNCTION_DOMAINS[domain], False
    if domain == 3:
        kind = D3_ROLE[bits]
        return kind, kind.endswith("function-candidate")
    if domain == 4:
        kind = D4_ROLE[bits]
        return kind, kind.endswith("function-candidate")
    if domain == 5 and row["en"].upper() in D5_PROTOCOLS:
        return "protocol-or-special-form-candidate", False
    if row["LISP"] == "()" or row["LISP_quoted"]:
        return "resident-without-callable-lisp-surface", False
    return "function-candidate-unclassified", True


def research_mentions(root: Path, tokens_needed: set[str]) -> dict[str, list[str]]:
    """Find exact-token mentions in existing research; a mention is not a law."""
    hits: dict[str, set[str]] = {}
    for start in (root / "knowledge", root / "docs" / "research", root / "research"):
        if not start.is_dir():
            continue
        for path in sorted(start.rglob("*")):
            if path.is_symlink() or not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            try:
                if path.stat().st_size > MAX_RESEARCH_BYTES:
                    continue
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue
            for token in {m.group(0).casefold() for m in TOKEN.finditer(text)} & tokens_needed:
                hits.setdefault(token, set()).add(path.relative_to(root).as_posix())
    return {token: sorted(paths) for token, paths in hits.items()}


def witness_references(root: Path, tokens_needed: set[str]) -> dict[str, list[str]]:
    """Locate exact-token mentions in existing test/witness sources; this is not a PASS."""
    hits: dict[str, set[str]] = {}
    for start in (root / "tests", root / "crates" / "sens" / "tests"):
        if not start.is_dir():
            continue
        for path in sorted(start.rglob("*")):
            if path.is_symlink() or not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            try:
                if path.stat().st_size > MAX_RESEARCH_BYTES:
                    continue
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue
            matched = {match.group(0).casefold() for match in TOKEN.finditer(text)} & tokens_needed
            for token in matched:
                hits.setdefault(token, set()).add(path.relative_to(root).as_posix())
    return {token: sorted(paths) for token, paths in hits.items()}


def discover(root: Path, scan_research: bool = True) -> list[dict[str, Any]]:
    maps = load_domain_tables(root)
    definitions = find_active_sens_definitions(root)
    all_rows = [row for d in range(1, 12) for row in maps[d]]
    needed = {alias.casefold() for row in all_rows for alias in aliases(row)}
    hits = research_mentions(root, needed) if scan_research else {}
    witnesses = witness_references(root, needed)
    result = []
    for row in all_rows:
        domain = row["domain"]
        kind, candidate = classify(row)
        names = aliases(row)
        definitions_here = sorted({p for name in names for p in definitions.get(name.casefold(), [])})
        research_here = sorted({p for name in names for p in hits.get(name.casefold(), [])})
        witness_here = sorted({p for name in names for p in witnesses.get(name.casefold(), [])})
        gate = ("D10 F1–F4 individually required; whole-codebook ratification is insufficient"
                if domain == 10 else "exact law + native positive/negative witness + mechanism must be checked")
        result.append({
            "identity": f"D{domain}:{row['bits']}", "domain": domain, "bits": row["bits"],
            "width": len(row["bits"]), "uk": row["ук"], "ukr": row["укр"],
            "san": row["san"], "en": row["en"], "lisp": row["LISP"], "sym": row["sym"],
            "object_kind": kind, "function_candidate": candidate,
            "source_definition_paths": definitions_here,
            "research_mention_files": len(research_here), "research_paths": research_here[:5],
            "witness_reference_files": len(witness_here), "witness_reference_paths": witness_here[:8],
            "witness_references_are_proofs": False,
            "callability": "NOT_ASSERTED", "evidence_gate": gate,
            "next_step": ("inspect exact law, arity, mechanism, positive/negative native SENS witnesses, and behavioral duplicates"
                          if candidate else "keep object kind; do not promote to an ordinary function call"),
            "source_table": f"lib/domains/d{domain}.lisp:{row['line']}",
        })
    return result


def render_tsv(rows: list[dict[str, Any]]) -> str:
    fields = ["identity", "width", "uk", "ukr", "san", "en", "lisp", "sym", "object_kind",
              "function_candidate", "source_definition_paths", "research_mention_files", "research_paths",
              "witness_reference_files", "witness_reference_paths", "witness_references_are_proofs",
              "callability", "evidence_gate", "source_table"]
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fields, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        row = dict(row)
        row["source_definition_paths"] = ";".join(row["source_definition_paths"])
        row["research_paths"] = ";".join(row["research_paths"])
        row["witness_reference_paths"] = ";".join(row["witness_reference_paths"])
        writer.writerow({field: row.get(field, "") for field in fields})
    return out.getvalue()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--domain", choices=[f"D{n}" for n in range(1, 12)])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--format", choices=("json", "tsv"), default="json")
    parser.add_argument("--no-research-scan", action="store_true")
    parser.add_argument("--candidates-only", action="store_true",
                        help="drop structural/data/syntax residents from the requested batch")
    parser.add_argument("--evidence-first", action="store_true",
                        help="prioritize candidates with source definitions and existing witness references")
    args = parser.parse_args(argv)
    if args.limit < 0:
        parser.error("--limit must be >= 0")
    try:
        rows = discover(args.root.resolve(), scan_research=not args.no_research_scan)
    except (OSError, UnicodeError, AuditError) as exc:
        print(f"DOMAIN-CANDIDATE-AUDIT ERROR: {exc}", file=sys.stderr)
        return 2
    if args.domain:
        domain = int(args.domain[1:])
        rows = [row for row in rows if row["domain"] == domain]
    if args.candidates_only:
        rows = [row for row in rows if row["function_candidate"]]
    if args.evidence_first:
        rows = sorted(
            rows,
            key=lambda row: (
                -int(bool(row["source_definition_paths"])),
                -int(bool(row["witness_reference_paths"])),
                -row["research_mention_files"],
                -row["witness_reference_files"],
                row["domain"],
                row["bits"],
            ),
        )
    if args.limit:
        rows = rows[:args.limit]
    if args.format == "tsv":
        sys.stdout.write(render_tsv(rows))
    else:
        print(json.dumps({
            "schema": "sens.domain-function-candidate-report/v1",
            "authority": "read-only report; not a semantic registry",
            "candidate_count": sum(bool(row["function_candidate"]) for row in rows),
            "reported_rows": len(rows), "callability_asserted": False, "rows": rows,
        }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
