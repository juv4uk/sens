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


def reject_shadowed_surfaces(source: str, surfaces) -> set[str]:
    import importlib.util
    import sys

    key = "_sens_three_pass_source_reader_for_shadow_guard"
    reader = sys.modules.get(key)
    if reader is None:
        script = ROOT / "scripts/migrate-three-pass.py"
        spec = importlib.util.spec_from_file_location(key, script)
        if spec is None or spec.loader is None:
            raise ValueError("SOURCE_READER_ERROR: немає AST-reader")
        reader = importlib.util.module_from_spec(spec)
        sys.modules[key] = reader
        try:
            spec.loader.exec_module(reader)
        except BaseException:
            sys.modules.pop(key, None)
            raise

    try:
        forms = reader.Parser(
            reader.tokenize(reader.strip_comments(source))
        ).parse_program()
    except reader.MigrationError as error:
        raise ValueError(f"AST_PARSE_BLOCK: {error}") from error

    shadowed: set[str] = set()

    def collides(node):
        return (
            isinstance(node, reader.Atom)
            and node.tok.text.casefold() in surfaces
        )

    def guard_name(node, context):
        # Не переписувати затінені локальні виклики; незалежні виклики — можна.
        if collides(node):
            shadowed.add(node.tok.text.casefold())

    lambda_heads = {
        item.bits for item in surfaces.values()
        if item.domain == "D4" and item.label.upper() == "LAMBDA"
    }
    define_heads = {
        item.bits for item in surfaces.values()
        if item.domain == "D4" and item.label.upper() == "DEFINE"
    }

    foundation = json.loads(
        (ROOT / "knowledge/d1-d9-foundation.json").read_text(encoding="utf-8")
    )
    if foundation.get("status") != "owner-ratified":
        raise ValueError("SOURCE_FORM_ERROR: основа доменів не ратифікована")
    let_heads = {
        bits for bits, label in foundation["domains"]["D6"]["residents"].items()
        if label in {"LET", "LET*"}
    }
    if len(let_heads) != 2:
        raise ValueError("SOURCE_FORM_ERROR: координати D6 LET змінилися")

    def binding_list(node, context):
        if not isinstance(node, reader.ListNode) or node.tail is not None:
            raise ValueError(f"SOURCE_FORM_ERROR: {context}: непідтверджена форма зв'язувань")
        return node.items

    def guard_parameters(node, context):
        for parameter in binding_list(node, context):
            if not isinstance(parameter, reader.Atom):
                raise ValueError(
                    f"SOURCE_FORM_ERROR: {context}: вкладений параметр без доведеного закону"
                )
            guard_name(parameter, context)

    def visit(node):
        if isinstance(node, reader.Quote):
            return
        if not isinstance(node, reader.ListNode):
            return
        if not node.items:
            return
        head = node.items[0]
        if isinstance(head, reader.Atom):
            spelling = head.tok.text.casefold()
            if spelling in {"quote", "як-є", "001"}:
                return
            surface = surfaces.get(spelling)
            role = (surface.label if surface is not None else "").upper()
            if role == "LAMBDA" or spelling in lambda_heads:
                if len(node.items) < 2:
                    raise ValueError("SOURCE_FORM_ERROR: LAMBDA без параметрів")
                guard_parameters(node.items[1], "параметр LAMBDA")
            if role == "DEFINE" or spelling in define_heads | {"def"}:
                if len(node.items) >= 2:
                    target = node.items[1]
                    if isinstance(target, reader.Atom):
                        guard_name(target, "ім'я DEFINE")
                    elif (isinstance(target, reader.ListNode)
                          and target.items):
                        guard_name(target.items[0], "голова DEFINE")
                        for parameter in target.items[1:]:
                            if not isinstance(parameter, reader.Atom):
                                raise ValueError(
                                    "SOURCE_FORM_ERROR: вкладений параметр DEFINE"
                                )
                            guard_name(parameter, "параметр DEFINE")
                    else:
                        raise ValueError("SOURCE_FORM_ERROR: некоректний DEFINE")

            if spelling in let_heads | {"let", "let*"}:
                if len(node.items) < 2:
                    raise ValueError("SOURCE_FORM_ERROR: LET без списку зв'язувань")
                for item in binding_list(node.items[1], "LET"):
                    if isinstance(item, reader.Atom):
                        guard_name(item, "змінна LET")
                    else:
                        pair = binding_list(item, "пара LET")
                        if not pair or not isinstance(pair[0], reader.Atom):
                            raise ValueError("SOURCE_FORM_ERROR: некоректна пара LET")
                        guard_name(pair[0], "змінна LET")

            if spelling in {"flet", "labels", "macrolet"}:
                if len(node.items) < 2:
                    raise ValueError("SOURCE_FORM_ERROR: локальні функції без декларацій")
                for item in binding_list(node.items[1], spelling):
                    signature = binding_list(item, "локальна функція")
                    if not signature or not isinstance(signature[0], reader.Atom):
                        raise ValueError("SOURCE_FORM_ERROR: некоректна локальна функція")
                    guard_name(signature[0], "ім'я локальної функції")
                    if len(signature) < 2:
                        raise ValueError("SOURCE_FORM_ERROR: немає списку параметрів")
                    guard_parameters(signature[1], "параметр локальної функції")

            if spelling in {"defun", "defmacro"}:
                if len(node.items) < 3 or not isinstance(node.items[1], reader.Atom):
                    raise ValueError("SOURCE_FORM_ERROR: некоректне оголошення функції")
                guard_name(node.items[1], "ім'я оголошеної функції")
                guard_parameters(node.items[2], "параметр оголошеної функції")
        for child in node.items:
            visit(child)
        if node.tail is not None:
            visit(node.tail)

    for form in forms:
        visit(form)
    return shadowed


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
        while operator.lt(i, len(source)) and not source[i].isspace() and source[i] not in "()'\";,:" :
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
