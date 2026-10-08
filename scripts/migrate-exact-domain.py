#!/usr/bin/env python3
"""Migrate executable Lisp heads to current exact-domain SENS words.

Current authority is read from:
  lib/domains/d3.lisp ... lib/domains/d6.lisp
  lib/surface/semantic-registry.lisp (legacy 8-bit -> exact successor)

Only executable list heads are changed. Strings, comments, quoted data,
ordinary arguments, and already exact 3..6 bit words are left alone.

Usage:
  python3 scripts/migrate-exact-domain.py --check FILE...
  python3 scripts/migrate-exact-domain.py --write FILE...
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from domain_tables import read_domain_table

DOMAIN_PATHS = [ROOT / "lib" / "domains" / f"d{width}.lisp" for width in range(3, 7)]
REGISTRY_PATH = ROOT / "lib" / "surface" / "semantic-registry.lisp"

# Contract 11.8 compiler-call admission is a separate law from identity
# resolution. Never narrow a legacy identity into a non-admitted callable.
ADMITTED_CALLABLES = {
    "D3": frozenset({"001", "010", "011", "100", "101", "110", "111"}),
    "D4": frozenset({"0010", "0011"}),
}

ROW_RE = re.compile(r'^\s*\(([01]{8})\s+(.*)\)\s*$')
FIELD_RE = re.compile(
    r'\((en|uk|ukr|sa|sym)\s+("(?:\\\\.|[^"\\\\])*"|\(\)|[^()\s]+)\)'
)

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

def decode_registry_value(raw: str) -> str | None:
    if raw == "()":
        return None
    if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
        return raw[1:-1]
    return raw

def load_authority() -> tuple[dict[str, Identity], dict[str, Identity]]:
    surfaces: dict[str, Identity] = {}
    by_en: dict[str, list[Identity]] = {}

    for path in DOMAIN_PATHS:
        for row in read_domain_table(path):
            if row.domain == "D3" and row.bits == "000":
                continue
            identity = Identity(
                row.domain,
                row.bits,
                row.en or row.lisp or row.bits,
            )
            for value in (row.en, row.uk, row.ukr, row.san, row.lisp, row.sym):
                if not value:
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
    for line in registry.splitlines():
        match = ROW_RE.match(line)
        if not match:
            continue
        sid, payload = match.groups()
        fields = {
            namespace: decode_registry_value(raw)
            for namespace, raw in FIELD_RE.findall(payload)
        }
        en = fields.get("en")
        if not en:
            continue
        candidates = {
            (item.domain, item.bits): item
            for item in by_en.get(en.lower(), [])
        }
        if len(candidates) == 1:
            legacy[sid] = next(iter(candidates.values()))

    return surfaces, legacy

def _consume_line_comment(text: str, start: int, size: int) -> tuple[int, str]:
    end = text.find("\n", start)
    if end < 0:
        end = size
    return end, text[start:end]


def _consume_block_comment(text: str, start: int, size: int) -> tuple[int, str]:
    end = start + 2
    depth = 1
    while end < size and depth:
        if text.startswith("#|", end):
            depth += 1
            end += 2
        elif text.startswith("|#", end):
            depth -= 1
            end += 2
        else:
            end += 1
    if depth:
        raise ValueError("unterminated #| ... |# comment")
    return end, text[start:end]


def _consume_string(text: str, start: int, size: int) -> tuple[int, str]:
    end = start + 1
    while end < size:
        if text[end] == "\\" and end + 1 < size:
            end += 2
        elif text[end] == '"':
            end += 1
            return end, text[start:end]
        else:
            end += 1
    raise ValueError("unterminated string")


def _consume_quote(text: str, start: int, size: int) -> tuple[int, str]:
    end = start + 2 if start + 1 < size and text[start:start + 2] == ",@" else start + 1
    return end, text[start:end]


def _consume_atom(text: str, start: int, size: int) -> tuple[int, str]:
    delimiters = set("();\"",)
    end = start
    while end < size:
        current = text[end]
        if current.isspace() or current in delimiters or current == chr(96):
            break
        if text.startswith("#|", end):
            break
        end += 1
    if end == start:
        raise ValueError(f"cannot tokenize {text[start]!r} at offset {start}")
    return end, text[start:end]


def tokens(text: str):
    i = 0
    size = len(text)
    backquote = chr(96)

    while i < size:
        ch = text[i]
        if ch.isspace():
            i += 1
            continue
        if ch == ";":
            end, value = _consume_line_comment(text, i, size)
            yield ("comment", i, end, value)
            i = end
            continue
        if text.startswith("#|", i):
            end, value = _consume_block_comment(text, i, size)
            yield ("comment", i, end, value)
            i = end
            continue
        if ch == '"':
            end, value = _consume_string(text, i, size)
            yield ("string", i, end, value)
            i = end
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
            end, value = _consume_quote(text, i, size)
            yield ("quote", i, end, value)
            i = end
            continue

        end, value = _consume_atom(text, i, size)
        yield ("atom", i, end, value)
        i = end


def _push_atom_edit(
    edits: list[Edit],
    start: int,
    end: int,
    value: str,
    surfaces: dict[str, Identity],
    legacy: dict[str, Identity],
) -> None:
    if re.fullmatch(r"[01]{3,6}", value):
        return

    identity = (
        legacy.get(value) if re.fullmatch(r"[01]{8}", value) else surfaces.get(value)
    )
    if identity is None:
        return
    if identity.bits not in ADMITTED_CALLABLES.get(identity.domain, ()):
        return
    edits.append(Edit(start, end, value, identity))


def _walk_plan_token(
    kind: str,
    start: int,
    end: int,
    value: str,
    stack: list[dict[str, bool]],
    quoted_next: bool,
    edits: list[Edit],
    surfaces: dict[str, Identity],
    legacy: dict[str, Identity],
) -> bool:
    if kind == "quote":
        return True
    if kind in {"string", "comment", "close"}:
        if kind == "string" and stack:
            stack[-1]["head"] = False
        if kind == "close":
            if not stack:
                raise ValueError(f"unexpected ')' at offset {start}")
            stack.pop()
        return False
    if kind == "open":
        parent_quoted = bool(stack and stack[-1]["quoted"])
        stack.append({"quoted": parent_quoted or quoted_next, "head": True})
        return False
    if kind != "atom" or not stack:
        return False

    frame = stack[-1]
    is_head = frame["head"]
    quoted = frame["quoted"]
    frame["head"] = False
    if not is_head or quoted:
        return False
    _push_atom_edit(edits, start, end, str(value), surfaces, legacy)
    return False


def plan(
    text: str, surfaces: dict[str, Identity], legacy: dict[str, Identity]
) -> list[Edit]:
    stack: list[dict[str, bool]] = []
    quoted_next = False
    edits: list[Edit] = []

    for kind, start, end, value in tokens(text):
        if kind == "quote":
            quoted_next = True
            continue
        if _walk_plan_token(
            kind,
            start,
            end,
            value,
            stack,
            quoted_next,
            edits,
            surfaces,
            legacy,
        ):
            quoted_next = True
        else:
            quoted_next = False

    if stack:
        raise ValueError("unterminated list")
    return edits

def apply_edits(text: str, edits: list[Edit]) -> str:
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

    try:
        surfaces, legacy = load_authority()
    except (OSError, UnicodeError, ValueError) as exc:
        parser.error(str(exc))

    failed = False
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

            rewritten = apply_edits(source, edits)
            if rewritten != source:
                path.write_text(rewritten, encoding="utf-8")

            if plan(rewritten, surfaces, legacy):
                raise ValueError("non-idempotent migration: executable heads remain")

        except (OSError, UnicodeError, ValueError) as exc:
            print(f"{path}: ERROR: {exc}", file=sys.stderr)
            failed = True

    return 2 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())
