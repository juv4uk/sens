#!/usr/bin/env python3
"""Міграція Lisp-голів тільки за ратифікованими D3/D4 українськими поверхнями.

Старі восьмибітні слоти не визначають поточну identity/викличність.
T5M — лише транспорт уже сформованих слів.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WORD8 = re.compile(r"[01]{8}\Z")
FIELD = re.compile(r'\((ук|укр|san|en|LISP|sym)\s+("(?:\\.|[^"\\])*"|\(\)|[^()\s]+)\)')
SAFE_OLD = {
    ("D3", "QUOTE"), ("D3", "ATOM"), ("D3", "EQ"),
    ("D3", "CAR"), ("D3", "CDR"), ("D3", "CONS"),
    ("D4", "LAMBDA"), ("D4", "DEFINE"),
}


@dataclass(frozen=True)
class Identity:
    domain: str
    bits: str
    label: str
    українська: str


@dataclass(frozen=True)
class Edit:
    start: int
    end: int
    source: str
    identity: Identity


def load_authority(root: Path = ROOT):
    foundation = json.loads(
        (root / "knowledge/d1-d9-foundation.json").read_text(encoding="utf-8")
    )
    if foundation.get("status") != "owner-ratified":
        raise ValueError("missing exact-domain owner authority")

    surfaces = {}
    ambiguous = set()
    for domain in ("D3", "D4"):
        table = (root / "lib/domains" / (domain.lower() + ".lisp")).read_text(encoding="utf-8")
        residents = foundation["domains"][domain]["residents"]
        for line in table.splitlines():
            row = re.match(r"^\s*\(([01]{3,4})\s+(.*)$", line)
            if not row:
                continue
            bits, tail = row.groups()
            if len(bits) != int(domain[1:]):
                continue
            label = residents.get(bits)
            if label is None:
                raise ValueError(f"owner table drift at {domain}:{bits}")
            fields = dict(FIELD.findall(tail))
            raw_ukr = fields.get("укр", "()")
            if raw_ukr == "()":
                if label != "EMPTY":
                    raise ValueError(f"missing Ukrainian projection at {domain}:{bits}")
                continue
            українська = json.loads(raw_ukr) if raw_ukr.startswith('"') else raw_ukr
            if not isinstance(українська, str) or not українська:
                raise ValueError(f"invalid Ukrainian projection at {domain}:{bits}")
            identity = Identity(domain, bits, label, українська)
            for _, raw in FIELD.findall(tail):
                if raw == "()":
                    continue
                surface = json.loads(raw) if raw.startswith('"') else raw
                key = surface.casefold()
                if key in surfaces and surfaces[key] != identity:
                    ambiguous.add(key)
                else:
                    surfaces[key] = identity
    for key in ambiguous:
        del surfaces[key]
    if not all(x in surfaces for x in ("car", "quote", "перше", "атом?")):
        raise ValueError("missing owner-ratified D3 surfaces")

    return surfaces


def reject_shadowed_surfaces(source: str, surfaces) -> None:
    """Owner policy: no SHADOWED_SURFACE_BLOCK / BINDING_FORM_BLOCK.

    Ukrainian surface spellings as DEFINE names, LAMBDA parameters, or LET
    variables are intentional (opt-in aliases and natural ukr binding names).
    T5M / SENS handles scope. Do not reintroduce artificial blockers.
    """
    return


def plan(source: str, surfaces):
    reject_shadowed_surfaces(source, surfaces)
    frames, edits = [], []
    pending_quote = False
    i = 0
    while i < len(source):
        if source.startswith("#;", i):
            raise ValueError("reader discard requires independent parser proof")
        if source.startswith("#|", i):
            depth = 1
            i += 2
            while depth and i < len(source):
                if source.startswith("#|", i):
                    depth += 1
                    i += 2
                elif source.startswith("|#", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
            if depth:
                raise ValueError("unterminated block comment")
            continue
        ch = source[i]
        if ch in " \t\r\n":
            i += 1
            continue
        if ch == ";":
            while i < len(source) and source[i] not in "\r\n":
                i += 1
            continue
        if ch == '"':
            i += 1
            while i < len(source):
                if source[i] == '\\':
                    i += 2
                    continue
                if source[i] == '"':
                    i += 1
                    break
                i += 1
            else:
                raise ValueError("unterminated string")
            pending_quote = False
            continue
        if ch == "'":
            pending_quote = True
            i += 1
            continue
        if ch == ",":
            raise ValueError("quasiquote unquote needs independent AST proof")
        if ch == "(":
            frames.append(i)
            pending_quote = False
            i += 1
            continue
        if ch == ")":
            if not frames:
                raise ValueError("extra closing parenthesis")
            frames.pop()
            pending_quote = False
            i += 1
            continue
        if ch in "[]{}":
            raise ValueError("unsupported reader character")
        start = i
        while i < len(source) and source[i] not in " \t\r\n;()\"'[]{}":
            i += 1
        token = source[start:i]
        if pending_quote:
            pending_quote = False
            continue
        key = token.casefold()
        if key in surfaces and frames:
            # only migrate call-head position: first atom after open paren with no prior sibling
            # Approximate: if the last non-space after '(' is this token, it is a head
            open_at = frames[-1]
            between = source[open_at + 1:start]
            if between.strip() == "":
                identity = surfaces[key]
                if identity.українська.casefold() != key:
                    edits.append(Edit(start, i, token, identity))
        pending_quote = False
    if frames:
        raise ValueError("unterminated list")
    return edits


def apply_edits(source: str, edits):
    if not edits:
        return source, 0
    parts = []
    last = 0
    count = 0
    for edit in sorted(edits, key=lambda e: e.start):
        if edit.start < last:
            raise ValueError("overlapping migration edit")
        if source[edit.start:edit.end] != edit.source:
            raise ValueError("source changed since planning")
        parts.append(source[last:edit.start])
        parts.append(edit.identity.українська)
        last = edit.end
        count += 1
    parts.append(source[last:])
    return "".join(parts), count


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Міграція Lisp-голів тільки за ратифікованими D3/D4 українськими поверхнями.\n"
            "Старі восьмибітні слоти не визначають поточну identity/викличність. T5M — лише\n"
            "транспорт уже сформованих слів."
        )
    )
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    surfaces = load_authority()
    staged = []
    for raw in args.paths:
        path = Path(raw)
        if not path.is_file() or path.suffix != ".lisp":
            raise ValueError(f"not an original regular .lisp source: {path}")
        original = path.read_text(encoding="utf-8")
        edits = plan(original, surfaces)
        updated, count = apply_edits(original, edits)
        if args.write and count:
            path.write_text(updated, encoding="utf-8")
        staged.append((path, original, updated, count))
    for path, _original, _updated, count in staged:
        print(f"{path}: {count} exact-domain Ukrainian head replacements")


if __name__ == "__main__":
    main()
