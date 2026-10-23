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
        (root / "knowledge/d1-d11-foundation.json").read_text(encoding="utf-8")
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
    """Return exact call-head offsets shadowed by bindings; never stop peers."""
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

    def mask_comments(text):
        chars = list(text)
        i, state, depth = 0, "code", 0
        while i < len(text):
            if state == "string":
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == '"':
                    state = "code"
                i += 1
                continue
            if state == "line":
                if text[i] == "\n":
                    state = "code"
                else:
                    chars[i] = " "
                i += 1
                continue
            if state == "block":
                if text.startswith("#|", i):
                    chars[i:i + 2] = [" ", " "]
                    depth += 1
                    i += 2
                elif text.startswith("|#", i):
                    chars[i:i + 2] = [" ", " "]
                    depth -= 1
                    i += 2
                    if depth == 0:
                        state = "code"
                else:
                    if text[i] != "\n":
                        chars[i] = " "
                    i += 1
                continue
            if text[i] == '"':
                state = "string"
                i += 1
            elif text[i] == ";":
                chars[i] = " "
                state = "line"
                i += 1
            elif text.startswith("#|", i):
                chars[i:i + 2] = [" ", " "]
                depth = 1
                state = "block"
                i += 2
            else:
                i += 1
        if state == "block":
            raise ValueError("unterminated block comment")
        return "".join(chars)

    try:
        forms = reader.Parser(
            reader.tokenize(mask_comments(source), source_surface="укр")
        ).parse_program()
    except reader.MigrationError as error:
        raise ValueError(f"AST_PARSE_ERROR: {error}") from error

    shadowed_offsets = set()
    lambda_heads = {
        identity.bits for identity in surfaces.values()
        if identity.domain == "D4" and identity.label.upper() == "LAMBDA"
    }
    define_heads = {
        identity.bits for identity in surfaces.values()
        if identity.domain == "D4" and identity.label.upper() == "DEFINE"
    }
    foundation = json.loads(
        (ROOT / "knowledge/d1-d11-foundation.json").read_text(encoding="utf-8")
    )
    if foundation.get("status") != "owner-ratified":
        raise ValueError("SOURCE_FORM_ERROR: основа доменів не ратифікована")
    let_heads = {
        bits for bits, label in foundation["domains"]["D6"]["residents"].items()
        if label in {"LET", "LET*"}
    }
    let_star_heads = {
        bits for bits, label in foundation["domains"]["D6"]["residents"].items()
        if label == "LET*"
    }
    if len(let_heads) != 2 or len(let_star_heads) != 1:
        raise ValueError("SOURCE_FORM_ERROR: координати D6 LET змінилися")
    lambda_heads |= {"lambda", "функція"}
    define_heads |= {"define", "визначити", "def"}
    let_heads |= {"let", "let*", "нехай", "нехай*", "нехай-послідовно"}
    let_star_heads |= {"let*", "нехай*", "нехай-послідовно"}

    def atom_name(node):
        return (
            node.tok.text.casefold()
            if isinstance(node, reader.Atom) else None
        )

    def binding_list(node, context):
        if not isinstance(node, reader.ListNode) or node.tail is not None:
            raise ValueError(
                f"SOURCE_FORM_ERROR: {context}: очікувався звичайний список"
            )
        return node.items

    def bound_name(node, context):
        name = atom_name(node)
        if name is None:
            raise ValueError(
                f"SOURCE_FORM_ERROR: {context}: очікувалося атомарне ім'я"
            )
        if name in surfaces:
            shadowed_offsets.add(node.tok.offset)
            return {name}
        return set()

    def bound_names(node, context):
        # Match the actual SENS evaluator's three supported lambda-list shapes:
        # (x y), (x y . rest), and a bare symbol such as args. LET bindings
        # remain strict proper lists through binding_list(); only parameter
        # binding uses this more permissive, evaluator-backed grammar.
        if isinstance(node, reader.Atom):
            return bound_name(node, context)
        if not isinstance(node, reader.ListNode):
            raise ValueError(
                f"SOURCE_FORM_ERROR: {context}: очікувався список, dotted-список або атомарне ім'я"
            )
        names = set()
        for item in node.items:
            names |= bound_name(item, context)
        if node.tail is not None:
            names |= bound_name(node.tail, context)
        return names

    def head_and_args(node):
        if not isinstance(node, reader.ListNode) or not node.items:
            return None, []
        return atom_name(node.items[0]), node.items[1:]

    def global_definition_name(node):
        name, args = head_and_args(node)
        surface = surfaces.get(name or "")
        role = surface.label.upper() if surface is not None else ""
        if role == "DEFINE" or name in define_heads:
            if not args:
                return None
            target = args[0]
            if isinstance(target, reader.Atom):
                return atom_name(target)
            if isinstance(target, reader.ListNode) and target.items:
                return atom_name(target.items[0])
        if name in {"defun", "defmacro"} and args:
            return atom_name(args[0])
        return None

    global_names = {
        name for form in forms
        if (name := global_definition_name(form)) in surfaces
    }

    def visit(node, bound):
        if isinstance(node, reader.Quote):
            return
        if not isinstance(node, reader.ListNode) or not node.items:
            return
        head = node.items[0]
        name = atom_name(head)
        args = node.items[1:]
        if name is None:
            for child in node.items:
                visit(child, bound)
            return

        if name in bound:
            shadowed_offsets.add(head.tok.offset)
            for child in args:
                visit(child, bound)
            return
        if name in {"quote", "як-є", "001"}:
            return

        surface = surfaces.get(name)
        role = surface.label.upper() if surface is not None else ""
        if role == "LAMBDA" or name in lambda_heads:
            if not args:
                raise ValueError("SOURCE_FORM_ERROR: LAMBDA без параметрів")
            local = bound | bound_names(args[0], "параметр LAMBDA")
            for child in args[1:]:
                visit(child, local)
            return
        if role == "DEFINE" or name in define_heads:
            if not args:
                raise ValueError("SOURCE_FORM_ERROR: DEFINE без імені")
            target = args[0]
            if isinstance(target, reader.Atom):
                bound_name(target, "ім'я DEFINE")
                for child in args[1:]:
                    visit(child, bound | global_names)
            elif isinstance(target, reader.ListNode) and target.items:
                bound_name(target.items[0], "голова DEFINE")
                params = reader.ListNode(target.items[1:], target.tail, target.tok)
                local = bound | global_names | bound_names(
                    params, "параметр DEFINE"
                )
                for child in args[1:]:
                    visit(child, local)
            else:
                raise ValueError("SOURCE_FORM_ERROR: некоректний DEFINE")
            return
        if name in {"defun", "defmacro"}:
            if len(args) < 2 or atom_name(args[0]) is None:
                raise ValueError("SOURCE_FORM_ERROR: некоректне оголошення функції")
            bound_name(args[0], "ім'я оголошеної функції")
            local = bound | global_names | bound_names(
                args[1], "параметр оголошеної функції"
            )
            for child in args[2:]:
                visit(child, local)
            return
        if name in let_heads:
            if not args:
                raise ValueError("SOURCE_FORM_ERROR: LET без списку зв'язувань")
            bindings = binding_list(args[0], "LET")
            local = set(bound)
            for item in bindings:
                if isinstance(item, reader.Atom):
                    local_name = atom_name(item)
                    initializer = None
                    bound_name(item, "змінна LET")
                else:
                    pair = binding_list(item, "пара LET")
                    if len(pair) != 2 or atom_name(pair[0]) is None:
                        raise ValueError("SOURCE_FORM_ERROR: некоректна пара LET")
                    local_name = atom_name(pair[0])
                    bound_name(pair[0], "змінна LET")
                    initializer = pair[1]
                if name in let_star_heads:
                    if initializer is not None:
                        visit(initializer, local)
                elif initializer is not None:
                    visit(initializer, bound)
                if local_name in surfaces:
                    local.add(local_name)
            for child in args[1:]:
                visit(child, local)
            return
        if name in {"flet", "labels", "macrolet"}:
            if not args:
                raise ValueError(
                    "SOURCE_FORM_ERROR: локальні функції без декларацій"
                )
            declarations = binding_list(args[0], name)
            signatures = []
            local_names = set()
            for declaration in declarations:
                parts = binding_list(declaration, "локальна функція")
                if len(parts) < 2 or atom_name(parts[0]) is None:
                    raise ValueError("SOURCE_FORM_ERROR: некоректна локальна функція")
                local_name = atom_name(parts[0])
                bound_name(parts[0], "ім'я локальної функції")
                if local_name in surfaces:
                    local_names.add(local_name)
                params = bound_names(parts[1], "параметр локальної функції")
                signatures.append((parts[2:], params))
            for body, params in signatures:
                function_scope = bound | params
                if name in {"labels", "macrolet"}:
                    function_scope |= local_names
                for child in body:
                    visit(child, function_scope)
            body_scope = bound | local_names
            for child in args[1:]:
                visit(child, body_scope)
            return

        for child in args:
            visit(child, bound)

    for form in forms:
        visit(form, global_names)
    return shadowed_offsets


def plan(source: str, surfaces, *, legacy_heads=None, unresolved=None):
    # Повноцінний AST-shadow-аналіз потрібний для перейменування named
    # поверхонь. Під час W8-аудиту surfaces={} — у більшості lib-файлів
    # немає жодного W8-виклику, тож примусово розбирати нецільові LAMBDA
    # (зокрема цитовані схеми) було хибним негативним результатом.
    shadowed = reject_shadowed_surfaces(source, surfaces) if surfaces else set()
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
        # Апостроф усередині українського ідентифікатора (ім'я,
        # пам'ять) є символом атома. Лише окремий початковий апостроф
        # позначає QUOTE; не підміняємо ці два різні випадки.
        while operator.lt(i, len(source)) and not source[i].isspace() and source[i] not in ("(", ")", '"', ";", chr(96)):
            if source.startswith("#|", i):
                break
            if source[i] == "'" and not (
                i > start and i + 1 < len(source)
                and source[i - 1].isalpha()
                and source[i + 1].isalpha()
            ):
                break
            if source[i] == ",":
                # Українська десяткова кома належить числу, не quasiquote.
                # Лише один роздільник між ASCII-цифрами; решта ком — синтаксис.
                prefix = source[start:i]
                if not (re.fullmatch(r"-?[0-9]+", prefix)
                        and i + 1 < len(source)
                        and source[i + 1].isascii()
                        and source[i + 1].isdigit()):
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
                    if legacy_heads is None:
                        raise ValueError(
                            "UNQUALIFIED_W8_HEAD: 8 біт — не автоматично D8; "
                            "потрібне історичне походження"
                        )
                    identity = legacy_heads.get(token)
                    if identity is not None:
                        edits.append(Edit(start, i, token, identity))
                        if identity.domain == "D3" and identity.bits == "001":
                            frame["quote_children"] = True
                    elif unresolved is not None:
                        unresolved.append((start, token))
                    else:
                        raise ValueError(f"SID8/Sens8 {token}: немає доведеного наступника")
                    pending_quote = False
                    continue
                identity = surfaces.get(token.casefold())
                if (identity and start not in shadowed
                        and token != identity.українська):
                    edits.append(Edit(start, i, token, identity))
                if token.casefold() in {"quote", "як-є"} or token == "001":
                    frame["quote_children"] = True
        pending_quote = False
    if frames:
        raise ValueError("unterminated list")
    # Реальні W8 виклики також повинні враховувати lexical shadowing.
    # Робимо дорогий AST-прохід ЛИШЕ для W8, які точно замінюємо.
    # У разі неоднозначного binder/quote parser відмовить локально;
    # жодна неперевірена W8-голова не буде переписана.
    if legacy_heads is not None and edits:
        active = {edit.source.casefold(): edit.identity for edit in edits}
        shadowed_w8 = reject_shadowed_surfaces(source, active)
        edits = [edit for edit in edits if edit.start not in shadowed_w8]
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
