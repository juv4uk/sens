#!/usr/bin/env python3
"""Fail-closed in-place Lisp migration to ratified D3/D4 call heads.

A source migration is not a T5 executable/oracle certificate. Historical
eight-bit words are ambiguous with modern D8 unless source era is proved.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WORD8 = re.compile(r"[01]{8}\Z")
TARGET = re.compile(r"D([3-9]):([01]{3,9})")
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
    audit = json.loads(
        (root / "knowledge/sens8-current-coverage-v1.json").read_text(encoding="utf-8")
    )
    if foundation.get("status") != "owner-ratified":
        raise ValueError("missing exact-domain owner authority")
    if audit.get("status") != "AUDIT-COMPLETE" or len(audit.get("rows", [])) != 256:
        raise ValueError("historical donor audit is incomplete")

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
            identity = Identity(domain, bits, label)
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

    legacy = {}
    seen = set()
    for row in audit["rows"]:
        code = row["legacy_code"]
        if not WORD8.fullmatch(code) or code in seen:
            raise ValueError("duplicate/invalid legacy cell")
        seen.add(code)
        if row.get("classification") not in {
            "DIRECT-CURRENT-IDENTITY", "CURRENT-PROJECTION-DERIVED"
        }:
            continue
        targets = TARGET.findall(row.get("current_target") or "")
        if len(targets) != 1:
            continue
        domain, bits = "D" + targets[0][0], targets[0][1]
        label = foundation["domains"][domain]["residents"].get(bits)
        if (domain, label) in SAFE_OLD:
            legacy[code] = Identity(domain, bits, label)
    if len(seen) != 256:
        raise ValueError("historical cells missing")
    return surfaces, legacy


def plan(source: str, surfaces, legacy, *, reject_unmapped_w8: bool = False):
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
        c = source[i]
        if c == ";":
            end = source.find("\n", i)
            i = len(source) if end < 0 else end
            continue
        if c == '"':
            # A string in first position consumes the list head; the next
            # atom is an argument, never another executable call head.
            if frames and frames[-1]["first"]:
                frames[-1]["first"] = False
            i += 1
            while i < len(source):
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
        while i < len(source) and not source[i].isspace() and source[i] not in "()'\";,":
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
                # Незіставлена восьмибітна голова — ні старий SID8, ні
                # чинний D8 не можуть бути вгадані з однакових бітів.
                if reject_unmapped_w8 and WORD8.fullmatch(token) and token not in legacy:
                    line = source.count("\n", 0, start) + 1
                    raise ValueError(
                        f"рядок {line}: неоднозначна виконувана W8/D8-голова {token}; "
                        "не можна частково переписувати файл"
                    )
                identity = surfaces.get(token.casefold()) or legacy.get(token)
                if identity and token != identity.bits:
                    edits.append(Edit(start, i, token, identity))
                if token.casefold() in {"quote", "як-є"} or token in {
                    "001", "00000001"
                }:
                    frame["quote_children"] = True
        pending_quote = False
    if frames:
        raise ValueError("unterminated list")
    return edits


def apply_edits(source: str, edits: list[Edit]):
    result = source
    last = len(source)
    for edit in sorted(edits, key=lambda x: x.start, reverse=True):
        if not (0 <= edit.start < edit.end <= last):
            raise ValueError("overlapping migration edit")
        if source[edit.start:edit.end] != edit.source:
            raise ValueError("source changed since planning")
        result = result[:edit.start] + edit.identity.bits + result[edit.end:]
        last = edit.start
    return result


def prepare_batch(paths, surfaces, legacy, *, for_write=False, legacy_source_era_proved=False):
    """Підготувати ВСІ файли до запису, перш ніж торкатися будь-якого джерела."""
    staged = []
    for path in paths:
        if path.suffix != ".lisp" or not path.is_file() or path.is_symlink():
            raise ValueError(f"не звичайний оригінальний файл .lisp: {path}")
        original = path.read_text(encoding="utf-8")
        edits = plan(original, surfaces, legacy, reject_unmapped_w8=for_write)
        if any(WORD8.fullmatch(edit.source) for edit in edits) and not legacy_source_era_proved:
            raise ValueError(
                f"{path}: неоднозначність старого W8 і чинного D8; "
                "спочатку доведіть епоху джерела"
            )
        staged.append((path, original, apply_edits(original, edits), len(edits)))
    return staged


def write_batch(staged):
    """Відмовити до першого запису, якщо хоч одне джерело змінилося."""
    for path, original, _, _ in staged:
        if path.read_text(encoding="utf-8") != original:
            raise ValueError(f"{path}: джерело змінилося після планування; запис заблоковано")
    for path, original, updated, _ in staged:
        if updated != original:
            path.write_text(updated, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--legacy-source-era-proved", action="store_true")
    args = parser.parse_args()
    surfaces, legacy = load_authority()
    staged = prepare_batch(
        args.paths,
        surfaces,
        legacy,
        for_write=args.write,
        legacy_source_era_proved=args.legacy_source_era_proved,
    )
    for path, _, _, count in staged:
        print(f"{path}: {count} точнодоменних замін виконуваних голів")
    if args.write:
        write_batch(staged)


if __name__ == "__main__":
    main()
