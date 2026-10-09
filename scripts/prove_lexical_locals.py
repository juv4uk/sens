#!/usr/bin/env python3
"""Доказове зняття людських назв ТІЛЬКИ з локальних посилань Lambda.

Читає існуючий трипрохідний парсер, НЕ створює .sens, D7-текстовий framing,
числовий wire-local чи новий executable oracle. Функціональні історичні
коди зберігаються як provenance без оголошення поточної семантики.
"""
from __future__ import annotations

import argparse
import hashlib
from functools import lru_cache
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
# Independent cross-check against owner-ratified D3/D4 tables. Never used
# to *create* a mapping: the canonical historical successor map must provide
# exactly these already proven current identities first.
RATIFIED_FOCUS_SUCCESSORS = {
    DEFINE: ("D4", "0011"),
    LAMBDA: ("D4", "0010"),
    QUOTE: ("D3", "001"),
    HISTORICAL_LIST: ("D4", "1110"),
    HISTORICAL_APPEND: ("D4", "1111"),
}
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


@lru_cache(maxsize=1)
def historical_successor_registry() -> dict:
    """SAME audited three-pass map used by the production migration CLI.

    Current domain identity belongs to D1-D9 source/registry owners, not a
    guessed D8 interpretation of old 8-bit spelling.
    """
    data = parser.load_foundation(ROOT / "knowledge/d1-d9-foundation.json")
    legacy, current, historical = parser.build_three_pass_maps(
        data,
        ROOT / "crates/sens/src/domain_surface_registry_generated.rs",
        ROOT / "crates/sens/src/semantic_registry_generated.rs",
        ROOT / "crates/sens/src/semantic_registry.rs",
        ROOT / "crates/sens/src/eval/necessary_forms_generated.rs",
        ROOT / "contracts/core1-historical-sid-map.lisp",
        ROOT / "knowledge/sens8-current-coverage-v1.json",
    )
    return legacy


def audited_current_head(historical_w8: str) -> dict:
    """Resolve a recorded OLD function head to one ratified current resident."""
    if historical_w8 not in (DEFINE, LAMBDA, QUOTE, HISTORICAL_LIST, HISTORICAL_APPEND):
        raise BindingBlocked("historical head not admitted to original bounded witness")
    registry = historical_successor_registry()
    converter = parser.Resolver(registry, {}, {}, source_era="legacy")
    try:
        words, pass_name = converter.head(parser.Tok("ATOM", historical_w8, 0))
    except parser.MigrationError as exc:
        raise BindingBlocked("historical successor is missing owner audit") from exc
    identity = registry.get(historical_w8)
    if (pass_name != "pass1-sens8" or identity is None or
            len(words) != 1 or identity[0] != words[0] or
            identity[1] not in ("D3", "D4") or
            len(words[0]) != int(identity[1][1:]) or
            (identity[1], words[0]) != RATIFIED_FOCUS_SUCCESSORS[historical_w8]):
        raise BindingBlocked("historical successor is not a single D3/D4 current resident")
    return {
        "old_w8": historical_w8,
        "current_domain": identity[1],
        "current_exact_word": words[0],
        "provenance": "canonical-owner-audited-three-pass-legacy",
        "current_runtime_admitted_by_this_proof": False,
    }


def lower_lambda(node, env: tuple[tuple[str, ...], ...], *, depth: int = 0,
                 declared_globals: dict[str, int] | None = None) -> dict:
    if depth > 128:
        raise BindingBlocked("bounded lexical nesting depth exceeded")
    parts = plain_list(node)
    if len(parts) != 3 or atom(parts[0]) != LAMBDA:
        raise BindingBlocked("only historical exact W8 LAMBDA (params) body supported")
    params = tuple(map(binder_name, plain_list(parts[1])))
    if len(params) != len(set(params)):
        raise BindingBlocked("duplicate local parameter")
    result = lower_expr(parts[2], (params,) + env, depth=depth + 1,
                        declared_globals=declared_globals)
    return {"kind": "lambda-local-coordinates",
            "historical_head_successor": audited_current_head(LAMBDA),
            "arity": len(params),
            "body": result}


def lower_expr(node, env: tuple[tuple[str, ...], ...], *, depth: int = 0,
               declared_globals: dict[str, int] | None = None):
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
        if declared_globals is not None and value in declared_globals:
            # Source-only declaration-order pointer, NOT current T5 global law.
            return {"kind": "GlobalReferenceCandidate",
                    "declaration_ordinal_source_only": declared_globals[value],
                    "source_name_provenance_only": value,
                    "runtime_binding_admitted": False}
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
        return {"kind": "quote-empty-historical-w8", "datum": "D3:000",
                "historical_head_successor": audited_current_head(QUOTE)}
    if head == LAMBDA:
        return lower_lambda(node, env, depth=depth + 1,
                            declared_globals=declared_globals)
    if declared_globals is not None and head in declared_globals:
        # A local head takes precedence: do not accidentally call a global.
        if any(head in frame for frame in env):
            raise BindingBlocked("shadowed global callable requires local-call law")
        return {"kind": "GlobalCallCandidate",
                "declaration_ordinal_source_only": declared_globals[head],
                "source_name_provenance_only": head,
                "runtime_binding_admitted": False,
                "arguments": [lower_expr(x, env, depth=depth + 1,
                                          declared_globals=declared_globals)
                              for x in parts[1:]]}
    if head not in ALLOWED_CALLS:
        raise BindingBlocked("unknown historical/global callable head; no name dispatch")
    return {"kind": "historical-call-proven-current-head-not-admitted",
            "historical_w8": head,
            "historical_head_successor": audited_current_head(head),
            "arguments": [lower_expr(x, env, depth=depth + 1,
                                      declared_globals=declared_globals)
                          for x in parts[1:]]}


def lower_definitions(source: str, *, expected_names: tuple[str, ...] | None = None) -> dict:
    """A symbolic source-side lexical witness, explicitly NOT physical .sens."""
    forms = source_forms(source)
    if not forms:
        raise BindingBlocked("no historical executable definitions")
    # Pass 1: stable source-order candidate binding slots, not a new D-code.
    # A complete pass before lowering permits forward global references.
    items_by_form = []
    declared_globals: dict[str, int] = {}
    for form in forms:
        items = plain_list(form)
        if len(items) != 3 or atom(items[0]) != DEFINE:
            raise BindingBlocked("top-level must be historical DEFINE name LAMBDA")
        name = binder_name(items[1])
        if name in declared_globals:
            raise BindingBlocked("duplicate top-level DEFINE name")
        declared_globals[name] = len(items_by_form)
        items_by_form.append((name, items[2]))
    names = tuple(name for name, _ in items_by_form)
    if expected_names is not None and names != expected_names:
        raise BindingBlocked("expected original definitions changed")
    definitions = []
    for ordinal, (name, body) in enumerate(items_by_form):
        expression = lower_lambda(body, (), declared_globals=declared_globals)
        definitions.append({
            "source_global_name_provenance_only": name,
            "global_declaration_ordinal_source_only": ordinal,
            "global_binding_runtime_admitted": False,
            "historical_define_successor": audited_current_head(DEFINE),
            "local_coordinate_body": expression,
        })
    expected = RATIFIED_FOCUS_SUCCESSORS
    # A small exact original witness MUST agree with independently ratified
    # resident coordinates; no historical integer-to-width fallback.
    for old_w8, (domain, bits) in expected.items():
        current = audited_current_head(old_w8)
        if (current["current_domain"], current["current_exact_word"]) != (domain, bits):
            raise BindingBlocked("historical successor disagrees with ratified current D3/D4")
    return {
        "schema": "sens-historical-local-coordinate-evidence/v1",
        "status": "LEXICAL_COORDINATES_PROVEN__PHYSICAL_NOT_ADMITTED",
        "global_names_encoded": False,
        "global_declaration_order_source_only_proven": True,
        "global_binding_runtime_admitted": False,
        "global_declaration_count": len(definitions),
        "source_global_export_manifest": [
            {"ordinal_source_only": item["global_declaration_ordinal_source_only"],
             "source_name_provenance_only": item["source_global_name_provenance_only"],
             "runtime_binding_admitted": False}
            for item in definitions
        ],
        "d2_or_d7_framing_defined": False,
        "current_callable_domain_identity_proven": False,
        "historical_head_successors_proven": True,
        "historical_head_successors": {
            old: audited_current_head(old)
            for old in (DEFINE, LAMBDA, QUOTE, HISTORICAL_LIST, HISTORICAL_APPEND)
        },
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
