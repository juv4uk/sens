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



def reject_ambiguous_local_bindings(source: str, surfaces):
    """Не переписувати глобальний surface, якщо він став локальним ім'ям.

    Повторно використовуємо чинний AST reader із cond-modernize.py:
    коментарі, лапки та цитовані datum не стають виконуваними зв'язуваннями.
    Недоведені складені форми fail-closed, без спроб підміни семантики.
    """
    import importlib.util
    import sys

    module_name = "_sens_exact_domain_scope_reader"
    parser = sys.modules.get(module_name)
    if parser is None:
        spec = importlib.util.spec_from_file_location(
            module_name, ROOT / "scripts/cond-modernize.py"
        )
        if spec is None or spec.loader is None:
            raise ValueError("current Lisp AST reader is unavailable")
        parser = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = parser
        spec.loader.exec_module(parser)

    try:
        roots = parser.parse(source)
    except parser.Blocked as error:
        raise ValueError("cannot establish local binding scopes: " + str(error)) from error

    quote_heads = {"001", "00000001", "quote", "QUOTE", "як-є"}
    lambda_heads = {"0010", "00001000", "lambda", "LAMBDA"}
    define_heads = {"0011", "00001001", "00001011", "define", "DEFINE", "def", "DEF"}
    let_heads = {
        "001000", "001001", "10011100", "10011101",
        "let", "LET", "let*", "LET*", "letrec", "LETREC",
        "10110011",
    }
    compound_bindings = {"defmacro", "DEFMACRO", "00001010",
                         "macrolet", "MACROLET", "flet", "FLET",
                         "labels", "LABELS"}

    def forbid_name(name, operator):
        if name is not None and name.casefold() in surfaces:
            raise ValueError(
                f"локальне/визначене ім'я {name!r} перетинається з "
                f"доменним surface ({operator}); потрібен доказ scope"
            )

    def parameter_names(node, operator):
        if node.atom is not None:
            if node.atom != ".":
                forbid_name(node.atom, operator)
        else:
            for child in node.children:
                parameter_names(child, operator)

    def walk(node):
        if node.opaque or not node.children:
            return
        parts = node.children
        operator = parts[0].atom
        if operator in quote_heads:
            return
        if operator in compound_bindings:
            raise ValueError(
                f"складене лексичне зв'язування {operator!r} "
                "потребує окремого AST-доказу"
            )
        if operator in lambda_heads:
            if len(parts) < 3:
                raise ValueError("неповна lambda: неможливо довести scope")
            parameter_names(parts[1], operator)
        elif operator in define_heads:
            if len(parts) < 3:
                raise ValueError("неповний define: неможливо довести scope")
            name_form = parts[1]
            name = (name_form.atom if name_form.atom is not None else
                    name_form.children[0].atom if name_form.children else None)
            if name is None:
                raise ValueError("непідтверджений binder у DEFINE")
            forbid_name(name, operator)
        elif operator in let_heads:
            if len(parts) < 3:
                raise ValueError("неповний LET: неможливо довести scope")
            bindings = parts[1]
            if bindings.atom is not None:
                # Named LET uses its own function name before the binding list.
                forbid_name(bindings.atom, operator)
                if len(parts) < 4:
                    raise ValueError("неповний named LET")
                bindings = parts[2]
            if bindings.atom is not None:
                raise ValueError("LET bindings не є списком")
            for binding in bindings.children:
                if not binding.children or binding.children[0].atom is None:
                    raise ValueError("непідтверджений binder у LET")
                forbid_name(binding.children[0].atom, operator)
        for child in parts[1:]:
            walk(child)

    for root in roots:
        walk(root)

def plan(source: str, surfaces, legacy):
    reject_ambiguous_local_bindings(source, surfaces)
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
            if not frame["quoted"]:
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--legacy-source-era-proved", action="store_true")
    args = parser.parse_args()
    surfaces, legacy = load_authority()
    for path in args.paths:
        if path.suffix != ".lisp" or not path.is_file() or path.is_symlink():
            raise ValueError(f"not an original regular .lisp source: {path}")
        original = path.read_text(encoding="utf-8")
        edits = plan(original, surfaces, legacy)
        if any(WORD8.fullmatch(e.source) for e in edits) and not args.legacy_source_era_proved:
            raise ValueError(f"{path}: W8 old/current D8 ambiguity; prove source era first")
        updated = apply_edits(original, edits)
        print(f"{path}: {len(edits)} exact-domain head replacements")
        if args.write and updated != original:
            path.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
