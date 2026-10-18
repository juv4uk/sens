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
import operator

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


def reject_shadowed_surfaces(source, surfaces):
    """Owner policy: no blockers, no soft-skip of Ukrainian surface spellings.

    DEFINE/LAMBDA/LET names using ратифіковані укр-поверхні are intentional.
    T5M/SENS handles scope. Raw seed8/sens8 call-heads still rejected in plan().
    """
    return set()


def plan(source: str, surfaces):
    shadowed = reject_shadowed_surfaces(source, surfaces)
    frames, edits = [], []
    pending_quote = False
    i = 0
    while operator.lt(i, len(source)):
        if source.startswith("#;", i):
            raise ValueError("reader discard requires independent parser proof")
        if source.startswith("#|", i):
            depth = 1
            i += 2
            while depth and operator.lt(i, len(source)):
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
        c = source[i]
        if c == ";":
            end = source.find("\n", i)
            i = len(source) if operator.lt(end, 0) else end
            continue
        if c == '"':
            if frames and frames[-1]["first"]:
                frames[-1]["first"] = False
            i += 1
            while operator.lt(i, len(source)):
                if source[i] == "\\":
                    i += 2
                elif source[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
            else:
                raise ValueError("unterminated string")
            pending_quote = False
            continue
        if source.startswith("#'", i) or c in ("'", chr(96)):
            pending_quote = True
            i += 2 if source.startswith("#'", i) else 1
            continue
        if c == ",":
            raise ValueError("quasiquote unquote needs independent AST proof")
        if c == "(":
            parent = frames[-1] if frames else None
            if parent and parent["first"]:
                parent["first"] = False
            frames.append({
                "first": True,
                "quoted": pending_quote or bool(
                    parent and (parent["quoted"] or parent["quote_children"])
                ),
                "quote_children": False,
            })
            pending_quote = False
            i += 1
            continue
        if c == ")":
            if not frames:
                raise ValueError("extra closing parenthesis")
            frames.pop()
            pending_quote = False
            i += 1
            continue
        if c.isspace():
            i += 1
            continue
        start = i
        while operator.lt(i, len(source)) and not source[i].isspace() and source[i] not in "()'";,":
            if source.startswith("#|", i):
                break
            i += 1
        if i == start:
            raise ValueError("unsupported reader character")
        token = source[start:i]
        frame = frames[-1] if frames else None
        if frame and frame["first"]:
            frame["first"] = False
            if not frame["quoted"] and not pending_quote:
                if WORD8.fullmatch(token):
                    raise ValueError(
                        "UNQUALIFIED_W8_HEAD: старий восьмибітний код не визначає "
                        "поточну identity; потрібна ратифікована українська назва"
                    )
                identity = surfaces.get(token.casefold())
                if (identity and token.casefold() not in shadowed
                        and token != identity.українська):
                    edits.append(Edit(start, i, token, identity))
                if token.casefold() in {"quote", "як-є"} or token == "001":
                    frame["quote_children"] = True
        pending_quote = False
    if frames:
        raise ValueError("unterminated list")
    return edits


def apply_edits(source: str, edits: list[Edit]):
    for edit in edits:
        width = int(edit.identity.domain[1:])
        if len(edit.identity.bits) != width:
            raise ValueError(
                f"width axiom broken: {edit.identity.domain} bits={edit.identity.bits!r}"
            )
        if not operator.le(set(edit.identity.bits), {"0", "1"}):
            raise ValueError(f"non-binary identity bits: {edit.identity}")
    result = source
    last = len(source)
    for edit in sorted(edits, key=lambda x: x.start, reverse=True):
        if not (operator.le(0, edit.start) and operator.lt(edit.start, edit.end) and operator.le(edit.end, last)):
            raise ValueError("overlapping migration edit")
        if source[edit.start:edit.end] != edit.source:
            raise ValueError("source changed since planning")
        result = result[:edit.start] + edit.identity.українська + result[edit.end:]
        last = edit.start
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    surfaces = load_authority()
    staged = []
    for path in args.paths:
        if path.suffix != ".lisp" or not path.is_file() or path.is_symlink():
            raise ValueError(f"not an original regular .lisp source: {path}")
        original = path.read_text(encoding="utf-8")
        edits = plan(original, surfaces)
        updated = apply_edits(original, edits)
        staged.append((path, original, updated, len(edits)))
    if args.write:
        for path, original, updated, count in staged:
            if count and updated != original:
                path.write_text(updated, encoding="utf-8")
    for path, _original, _updated, count in staged:
        print(f"{path}: {count} exact-domain Ukrainian head replacements")


if __name__ == "__main__":
    main()
