#!/usr/bin/env python3
"""Доказове зняття людських назв ТІЛЬКИ з локальних посилань Lambda.

Читає існуючий трипрохідний парсер, НЕ створює .sens, D7-текстовий framing,
числовий wire-local чи новий executable oracle. Функціональні історичні
коди зберігаються як provenance без оголошення поточної семантики.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MIGRATOR = ROOT / "scripts/migrate-three-pass.py"
HISTORICAL_MACHINE_BLOB = "200201b741787c4e144ad4194848acf51d7b439e"
DEFINE = "00001001"
LAMBDA = "00001000"
QUOTE = "00000001"
HISTORICAL_LIST = "00100111"
HISTORICAL_APPEND = "00101001"
ALLOWED_CALLS = {HISTORICAL_LIST, HISTORICAL_APPEND}
IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9-]*\Z")

spec = importlib.util.spec_from_file_location("lexical_local_existing_three_pass", MIGRATOR)
assert spec and spec.loader
parser = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = parser
spec.loader.exec_module(parser)


class BindingBlocked(ValueError):
    """Не вистачає прийнятого закону локального або глобального зв'язування."""


def git_blob(data: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()


def atom(node) -> str | None:
    return node.tok.text if isinstance(node, parser.Atom) else None


def plain_list(node) -> list:
    if not isinstance(node, parser.ListNode) or node.tail is not None:
        raise BindingBlocked("expected ordinary D2 list without dotted tail")
    return node.items


def binder_name(node) -> str:
    value = atom(node)
    if value is None or not IDENTIFIER.fullmatch(value):
        raise BindingBlocked("unratified or ambiguous local/global binder name")
    return value


def source_forms(source: str) -> list:
    return parser.Parser(parser.tokenize(parser.strip_comments(source))).parse_program()


def lower_lambda(node, env: tuple[tuple[str, ...], ...], *, depth: int = 0) -> dict:
    if depth > 128:
        raise BindingBlocked("bounded lexical nesting depth exceeded")
    parts = plain_list(node)
    if len(parts) != 3 or atom(parts[0]) != LAMBDA:
        raise BindingBlocked("only historical exact W8 LAMBDA (params) body supported")
    params = tuple(map(binder_name, plain_list(parts[1])))
    if len(params) != len(set(params)):
        raise BindingBlocked("duplicate local parameter")
    result = lower_expr(parts[2], (params,) + env, depth=depth + 1)
    return {"kind": "lambda-local-coordinates",
            "arity": len(params),
            "body": result}


def lower_expr(node, env: tuple[tuple[str, ...], ...], *, depth: int = 0):
    if depth > 128:
        raise BindingBlocked("bounded lexical nesting depth exceeded")
    if isinstance(node, (parser.Quote, parser.String)):
        raise BindingBlocked("reader quote/string requires separate Text7 data law")
    value = atom(node)
    if value is not None:
        for lexical_depth, frame in enumerate(env):
            if value in frame:
                return {"kind": "Local", "depth": lexical_depth,
                        "index": frame.index(value)}
        raise BindingBlocked("unresolved free variable; no implicit global/symbol fallback")
    parts = plain_list(node)
    if not parts:
        return {"kind": "EmptyD3", "bits": "000"}
    head = atom(parts[0])
    if head == QUOTE:
        if len(parts) != 2:
            raise BindingBlocked("historical QUOTE arity must be exactly 1")
        if not isinstance(parts[1], parser.ListNode) or plain_list(parts[1]):
            raise BindingBlocked("only QUOTE of structural empty is currently bounded")
        return {"kind": "quote-empty-historical-w8", "datum": "D3:000"}
    if head == LAMBDA:
        return lower_lambda(node, env, depth=depth + 1)
    if head not in ALLOWED_CALLS:
        raise BindingBlocked("unknown historical/global callable head; no name dispatch")
    return {"kind": "historical-call-not-current-domain",
            "historical_w8": head,
            "arguments": [lower_expr(x, env, depth=depth + 1)
                          for x in parts[1:]]}


def lower_definitions(source: str, *, expected_names: tuple[str, ...] | None = None) -> dict:
    """A symbolic source-side lexical witness, explicitly NOT physical .sens."""
    forms = source_forms(source)
    if not forms:
        raise BindingBlocked("no historical executable definitions")
    definitions = []
    seen: set[str] = set()
    for form in forms:
        items = plain_list(form)
        if len(items) != 3 or atom(items[0]) != DEFINE:
            raise BindingBlocked("top-level must be historical DEFINE name LAMBDA")
        name = binder_name(items[1])
        if name in seen:
            raise BindingBlocked("duplicate top-level DEFINE name")
        seen.add(name)
        # Top-level textual name stays here only as provenance; it is NOT
        # lowered into a D7 token or invented current callable identity.
        expression = lower_lambda(items[2], ())
        definitions.append({"source_global_name_provenance_only": name,
                            "local_coordinate_body": expression})
    names = tuple(item["source_global_name_provenance_only"] for item in definitions)
    if expected_names is not None and names != expected_names:
        raise BindingBlocked("expected original definitions changed")
    return {
        "schema": "sens-historical-local-coordinate-evidence/v1",
        "status": "LEXICAL_COORDINATES_PROVEN__PHYSICAL_NOT_ADMITTED",
        "global_names_encoded": False,
        "d2_or_d7_framing_defined": False,
        "current_callable_domain_identity_proven": False,
        "independent_current_runtime_oracle_proven": False,
        "original_executable_migrations_admitted": 0,
        "definitions": definitions,
    }


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--source", type=Path,
                     default=ROOT / "lib/machine/block.lisp")
    cli.add_argument("--require-machine-block-provenance", action="store_true")
    args = cli.parse_args(argv)
    try:
        raw = args.source.read_bytes()
        digest = git_blob(raw)
        if args.require_machine_block_provenance and digest != HISTORICAL_MACHINE_BLOB:
            raise BindingBlocked("original lib/machine/block.lisp Git blob changed")
        result = lower_definitions(
            raw.decode("utf-8"),
            expected_names=(
                "machine-block", "machine-block-empty", "machine-block-one",
                "machine-block-append", "machine-block-concat", "machine-block-forms",
            ) if args.require_machine_block_provenance else None,
        )
        result["source_git_blob_sha"] = digest
        result["source_sha256"] = hashlib.sha256(raw).hexdigest()
        result["definition_count"] = len(result["definitions"])
    except (OSError, UnicodeError, BindingBlocked, parser.MigrationError) as exc:
        print("LEXICAL LOCAL BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
