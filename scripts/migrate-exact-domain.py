#!/usr/bin/env python3
"""Migrate executable Lisp heads to current exact SENS domain words.

Authority:
  lib/domains/d3.lisp ... d6.lisp
  lib/surface/semantic-registry.lisp for legacy 8-bit -> exact successors

Only list heads are rewritten. Strings, comments, quoted data, ordinary
arguments, and already exact 3..6 bit words are untouched.

Usage:
  python3 scripts/migrate-exact-domain.py --check FILE...
  python3 scripts/migrate-exact-domain.py --write FILE...
"""
from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from domain_tables import read_domain_table

DOMAIN_PATHS = [ROOT / "lib" / "domains" / f"d{n}.lisp" for n in range(3, 7)]
REGISTRY_PATH = ROOT / "lib" / "surface" / "semantic-registry.lisp"

@dataclass(frozen=True)
class Identity:
    domain: str
    bits: str
    label: str

@dataclass(frozen=True)
class Edit:
    start: int
    end: int
    source: str
    identity: Identity

def registry_rows(text: str):
    field_re = re.compile(
        r'\((en|uk|ukr|sa|sym)\s+'
        r'("(?:\\.|[^"\\])*"|\(\)|[^()\s]+)\)'
    )
    for line in text.splitlines():
        m = re.match(r'^\s*\(([01]{8})\s+(.*)\)\s*
        if not m:
            continue
        fields = []
        for namespace, raw in field_re.findall(m.group(2)):
            value = ast.literal_eval(raw) if raw.startswith('"') else (
                None if raw == "()" else raw
            )
            fields.append((namespace, value))
        yield m.group(1), fields

def load_authority():
    surfaces: dict[str, Identity] = {}
    by_en: dict[str, list[Identity]] = {}

    for path in DOMAIN_PATHS:
        for row in read_domain_table(path):
            if row.domain == "D3" and row.bits == "000":
                continue
            identity = Identity(
                domain=row.domain,
                bits=row.bits,
                label=row.en or row.lisp or row.bits,
            )
            for value in (row.en, row.uk, row.ukr, row.san, row.lisp, row.sym):
                if not value or value == "()":
                    continue
                old = surfaces.get(value)
                if old is not None and old != identity:
                    raise ValueError(
                        f"ambiguous surface {value!r}: "
                        f"{old.domain}:{old.bits} vs {identity.domain}:{identity.bits}"
                    )
                surfaces[value] = identity
            if row.en:
                by_en.setdefault(row.en.lower(), []).append(identity)

    legacy: dict[str, Identity] = {}
    registry = REGISTRY_PATH.read_text(encoding="utf-8")
    for sid, fields in registry_rows(registry):
        en = next((v for ns, v in fields if ns == "en" and v), None)
        if not en:
            continue
        candidates = {
            (item.domain, item.bits): item
            for item in by_en.get(str(en).lower(), [])
        }
        if len(candidates) == 1:
            legacy[sid] = next(iter(candidates.values()))

    return surfaces, legacy

def scan(text: str):
    i = 0
    n = len(text)
    delimiters = set("();\"',")
    backquote = chr(96)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
            continue
        if ch == ";":
            end = text.find("\n", i)
            if end < 0:
                end = n
            yield ("comment", i, end, text[i:end])
            i = end
            continue
        if text.startswith("#|", i):
            start = i
            depth = 1
            i += 2
            while i < n and depth:
                if text.startswith("#|", i):
                    depth += 1
                    i += 2
                elif text.startswith("|#", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
            if depth:
                raise ValueError("unterminated #| ... |# comment")
            yield ("comment", start, i, text[start:i])
            continue
        if ch == '"':
            start = i
            i += 1
            while i < n:
                if text[i] == "\\" and i + 1 < n:
                    i += 2
                elif text[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
            else:
                raise ValueError("unterminated string")
            yield ("string", start, i, text[start:i])
            continue
        if ch == "(":
            yield ("open", i, i + 1, ch)
            i += 1
            continue
        if ch == ")":
            yield ("close", i, i + 1, ch)
            i += 1
            continue
        if ch in ("'", backquote):
            yield ("quote", i, i + 1, ch)
            i += 1
            continue
        if ch == ",":
            end = i + 2 if i + 1 < n and text[i + 1] == "@" else i + 1
            yield ("quote", i, end, text[i:end])
            i = end
            continue

        start = i
        while i < n:
            current = text[i]
            if current.isspace() or current in delimiters or current == backquote:
                break
            if text.startswith("#|", i):
                break
            i += 1
        if i == start:
            raise ValueError(f"cannot tokenize {text[i]!r} at offset {i}")
        yield ("atom", start, i, text[start:i])

def plan(text: str, surfaces, legacy) -> list[Edit]:
    stack: list[dict[str, bool]] = []
    quoted_next = False
    edits: list[Edit] = []

    for kind, start, end, value in scan(text):
        if kind == "quote":
            quoted_next = True
            continue
        if kind in {"comment", "string"}:
            quoted_next = False
            continue
        if kind == "open":
            parent_quoted = bool(stack and stack[-1]["quoted"])
            stack.append({"quoted": parent_quoted or quoted_next, "head": True})
            quoted_next = False
            continue
        if kind == "close":
            if not stack:
                raise ValueError(f"unexpected ')' at offset {start}")
            stack.pop()
            quoted_next = False
            continue
        if kind != "atom":
            continue

        if not stack:
            quoted_next = False
            continue

        frame = stack[-1]
        is_head = frame["head"]
        quoted = frame["quoted"]
        frame["head"] = False
        if not is_head or quoted:
            quoted_next = False
            continue

        token = str(value)
        # Preserve current exact-width source identities.
        if re.fullmatch(r"[01]{3,6}", token):
            quoted_next = False
            continue

        identity = legacy.get(token) if re.fullmatch(r"[01]{8}", token) else surfaces.get(token)
        if identity is not None:
            edits.append(Edit(start, end, token, identity))
        quoted_next = False

    if stack:
        raise ValueError("unterminated list")
    return edits

def apply(text: str, edits: list[Edit]) -> str:
    for edit in reversed(edits):
        text = text[:edit.start] + edit.identity.bits + text[edit.end:]
    return text

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--check", action="store_true", help="show the plan only")
    parser.add_argument("--write", action="store_true", help="rewrite files in place")
    args = parser.parse_args()

    if args.check and args.write:
        parser.error("--check and --write are mutually exclusive")
    surfaces, legacy = load_authority()

    failures = False
    for path in args.files:
        try:
            source = path.read_text(encoding="utf-8")
            edits = plan(source, surfaces, legacy)
            print(f"{path}: replacements={len(edits)}")
            for edit in edits[:40]:
                line = source.count("\n", 0, edit.start) + 1
                print(
                    f"  line {line}: {edit.source!r} -> "
                    f"{edit.identity.domain}:{edit.identity.bits}"
                )
            if not args.write:
                continue
            rewritten = apply(source, edits)
            if rewritten != source:
                path.write_text(rewritten, encoding="utf-8")
            remaining = plan(rewritten, surfaces, legacy)
            if remaining:
                raise ValueError(
                    f"non-idempotent result: {len(remaining)} executable heads remain"
                )
        except (OSError, UnicodeError, ValueError) as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            failures = True

    return 2 if failures else 0

if __name__ == "__main__":
    raise SystemExit(main())
, line)
        if not m:
            continue
        fields = []
        for namespace, raw in field_re.findall(m.group(2)):
            value = ast.literal_eval(raw) if raw.startswith('"') else (
                None if raw == "()" else raw
            )
            fields.append((namespace, value))
        yield m.group(1), fields

def load_authority():
    surfaces: dict[str, Identity] = {}
    by_en: dict[str, list[Identity]] = {}

    for path in DOMAIN_PATHS:
        for row in read_domain_table(path):
            if row.domain == "D3" and row.bits == "000":
                continue
            identity = Identity(
                domain=row.domain,
                bits=row.bits,
                label=row.en or row.lisp or row.bits,
            )
            for value in (row.en, row.uk, row.ukr, row.san, row.lisp, row.sym):
                if not value or value == "()":
                    continue
                old = surfaces.get(value)
                if old is not None and old != identity:
                    raise ValueError(
                        f"ambiguous surface {value!r}: "
                        f"{old.domain}:{old.bits} vs {identity.domain}:{identity.bits}"
                    )
                surfaces[value] = identity
            if row.en:
                by_en.setdefault(row.en.lower(), []).append(identity)

    legacy: dict[str, Identity] = {}
    registry = REGISTRY_PATH.read_text(encoding="utf-8")
    for sid, fields in registry_rows(registry):
        en = next((v for ns, v in fields if ns == "en" and v), None)
        if not en:
            continue
        candidates = {
            (item.domain, item.bits): item
            for item in by_en.get(str(en).lower(), [])
        }
        if len(candidates) == 1:
            legacy[sid] = next(iter(candidates.values()))

    return surfaces, legacy

def scan(text: str):
    i = 0
    n = len(text)
    delimiters = set("();\"',")
    backquote = chr(96)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
            continue
        if ch == ";":
            end = text.find("\n", i)
            if end < 0:
                end = n
            yield ("comment", i, end, text[i:end])
            i = end
            continue
        if text.startswith("#|", i):
            start = i
            depth = 1
            i += 2
            while i < n and depth:
                if text.startswith("#|", i):
                    depth += 1
                    i += 2
                elif text.startswith("|#", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
            if depth:
                raise ValueError("unterminated #| ... |# comment")
            yield ("comment", start, i, text[start:i])
            continue
        if ch == '"':
            start = i
            i += 1
            while i < n:
                if text[i] == "\\" and i + 1 < n:
                    i += 2
                elif text[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
            else:
                raise ValueError("unterminated string")
            yield ("string", start, i, text[start:i])
            continue
        if ch == "(":
            yield ("open", i, i + 1, ch)
            i += 1
            continue
        if ch == ")":
            yield ("close", i, i + 1, ch)
            i += 1
            continue
        if ch in ("'", backquote):
            yield ("quote", i, i + 1, ch)
            i += 1
            continue
        if ch == ",":
            end = i + 2 if i + 1 < n and text[i + 1] == "@" else i + 1
            yield ("quote", i, end, text[i:end])
            i = end
            continue

        start = i
        while i < n:
            current = text[i]
            if current.isspace() or current in delimiters or current == backquote:
                break
            if text.startswith("#|", i):
                break
            i += 1
        if i == start:
            raise ValueError(f"cannot tokenize {text[i]!r} at offset {i}")
        yield ("atom", start, i, text[start:i])

def plan(text: str, surfaces, legacy) -> list[Edit]:
    stack: list[dict[str, bool]] = []
    quoted_next = False
    edits: list[Edit] = []

    for kind, start, end, value in scan(text):
        if kind == "quote":
            quoted_next = True
            continue
        if kind in {"comment", "string"}:
            quoted_next = False
            continue
        if kind == "open":
            parent_quoted = bool(stack and stack[-1]["quoted"])
            stack.append({"quoted": parent_quoted or quoted_next, "head": True})
            quoted_next = False
            continue
        if kind == "close":
            if not stack:
                raise ValueError(f"unexpected ')' at offset {start}")
            stack.pop()
            quoted_next = False
            continue
        if kind != "atom":
            continue

        if not stack:
            quoted_next = False
            continue

        frame = stack[-1]
        is_head = frame["head"]
        quoted = frame["quoted"]
        frame["head"] = False
        if not is_head or quoted:
            quoted_next = False
            continue

        token = str(value)
        # Preserve current exact-width source identities.
        if re.fullmatch(r"[01]{3,6}", token):
            quoted_next = False
            continue

        identity = legacy.get(token) if re.fullmatch(r"[01]{8}", token) else surfaces.get(token)
        if identity is not None:
            edits.append(Edit(start, end, token, identity))
        quoted_next = False

    if stack:
        raise ValueError("unterminated list")
    return edits

def apply(text: str, edits: list[Edit]) -> str:
    for edit in reversed(edits):
        text = text[:edit.start] + edit.identity.bits + text[edit.end:]
    return text

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--check", action="store_true", help="show the plan only")
    parser.add_argument("--write", action="store_true", help="rewrite files in place")
    args = parser.parse_args()

    if args.check and args.write:
        parser.error("--check and --write are mutually exclusive")
    surfaces, legacy = load_authority()

    failures = False
    for path in args.files:
        try:
            source = path.read_text(encoding="utf-8")
            edits = plan(source, surfaces, legacy)
            print(f"{path}: replacements={len(edits)}")
            for edit in edits[:40]:
                line = source.count("\n", 0, edit.start) + 1
                print(
                    f"  line {line}: {edit.source!r} -> "
                    f"{edit.identity.domain}:{edit.identity.bits}"
                )
            if not args.write:
                continue
            rewritten = apply(source, edits)
            if rewritten != source:
                path.write_text(rewritten, encoding="utf-8")
            remaining = plan(rewritten, surfaces, legacy)
            if remaining:
                raise ValueError(
                    f"non-idempotent result: {len(remaining)} executable heads remain"
                )
        except (OSError, UnicodeError, ValueError) as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            failures = True

    return 2 if failures else 0

if __name__ == "__main__":
    raise SystemExit(main())
