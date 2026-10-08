#!/usr/bin/env python3
"""#4430 — conservative Ukrainian <-> typed words <-> physical T5 triplet proof.

Deliberately bounded: D1 predicates, D3 CAR/COND/QUOTE(EMPTY)/CONS,
D4 CAAR on a proved nested CONS pair, and D2 syntax. Not general D1-D9.
grammar. Unknown numbers, Text7, strings, binders, operators, aliases and
quoted forms BLOCK. This is a read-only canary proof, NOT a universal SENS
renderer, language authority or release admission.
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
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from domain_tables import read_domain_table
from sens_t5_codec import SensT5Error, decode_bytes, encode_words, typed_sha256

CONVERTER = SCRIPTS / "migrate-three-pass.py"
SPEC = importlib.util.spec_from_file_location("uk_t5_canonical_three_pass", CONVERTER)
assert SPEC and SPEC.loader
three_pass = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = three_pass
SPEC.loader.exec_module(three_pass)

SCHEMA = "sens-uk-t5-view-bounded-proof/v1"


class ProjectionBlocked(ValueError):
    pass


def uk_surface(width: int) -> dict[str, str]:
    """Read exact 'ук' cells from owner's domain table, never English aliases."""
    if width not in (1, 3, 4):
        raise ProjectionBlocked("no ratified Ukrainian renderer for this width")
    # Parse structural () through the canonical table reader. Regex token
    # matching excluded D3:000 and wrongly blocked the whole D3 authority.
    rows = [(row.bits, row.uk) for row in read_domain_table(
        ROOT / f"lib/domains/d{width}.lisp"
    )]
    if (len(rows) != 2 ** width or
            any(name is None for _, name in rows) or
            len({bits for bits, _ in rows}) != len(rows) or
            len({name for _, name in rows}) != len(rows)):
        raise ProjectionBlocked(f"D{width}: nonunique or incomplete ук authority")
    return dict(rows)


class WordParser:
    def __init__(self, words: list[str]):
        self.words = words
        self.index = 0

    def take(self) -> str:
        if self.index >= len(self.words):
            raise ProjectionBlocked("unterminated D2 list")
        result = self.words[self.index]
        self.index += 1
        return result

    def term(self, depth: int = 0):
        if depth > 256:
            raise ProjectionBlocked("D2 structure depth exceeds bounded proof")
        token = self.take()
        if token == "10":
            if self.index == len(self.words) or self.words[self.index] == "01":
                raise ProjectionBlocked("D2 empty list must use D3 000")
            children = [self.term(depth + 1)]
            while True:
                nxt = self.take()
                if nxt == "01":
                    break
                if nxt != "00":
                    raise ProjectionBlocked("D2 list requires one separator between items")
                children.append(self.term(depth + 1))
            return ("list", tuple(children))
        if token == "000":
            return ("empty",)
        if token in ("0", "1"):
            return ("predicate", token)
        if token in ("001", "100", "110", "111", "1000"):
            return ("head", token)
        raise ProjectionBlocked(f"outside bounded D1/D3 callable or data law: {token!r}")

    def parse(self):
        if not self.words:
            raise ProjectionBlocked("empty exact-word program")
        result = self.term()
        if self.index != len(self.words):
            raise ProjectionBlocked("multiple top-level forms are not yet admitted here")
        return result


def is_nil_pair_expression(node) -> bool:
    """Admit only QUOTE(EMPTY) and proper nested CONS of already proved pairs.

    This proves the currently exercised D3 CONS/D4 CAAR fixture cohort, NOT
    arbitrary quotation, list data, lexical variables, or unknown procedures.
    """
    if node[0] != "list":
        return False
    parts = node[1]
    if len(parts) == 2 and parts[0] == ("head", "001"):
        return parts[1] == ("empty",)
    if len(parts) == 3 and parts[0] == ("head", "111"):
        return is_nil_pair_expression(parts[1]) and is_nil_pair_expression(parts[2])
    return False


def render_uk(node, d1: dict[str, str], d3: dict[str, str],
              d4: dict[str, str]) -> str:
    kind = node[0]
    if kind == "empty":
        return "()"
    if kind == "predicate":
        return d1[node[1]]
    if kind != "list":
        raise ProjectionBlocked("callable head outside executable list")
    items = node[1]
    if not items or items[0][0] != "head":
        raise ProjectionBlocked("unknown callable head or COND clause context")
    opcode = items[0][1]
    if opcode == "001":
        if len(items) != 2 or items[1] != ("empty",):
            raise ProjectionBlocked("D3 QUOTE only admits exact D3 EMPTY data here")
        return "(" + d3[opcode] + " ())"
    if opcode == "111":
        if not is_nil_pair_expression(node):
            raise ProjectionBlocked("D3 CONS requires two proved nil-pair operands")
        return "(" + d3[opcode] + " " + " ".join(
            render_uk(part, d1, d3, d4) for part in items[1:]) + ")"
    if opcode == "1000":
        if len(items) != 2 or not is_nil_pair_expression(items[1]):
            raise ProjectionBlocked("D4 CAAR requires one proved nested CONS argument")
        return "(" + d4[opcode] + " " + render_uk(items[1], d1, d3, d4) + ")"
    if opcode == "100":
        if len(items) != 2:
            raise ProjectionBlocked("D3 CAR requires exactly one argument")
        return "(" + d3[opcode] + " " + render_uk(items[1], d1, d3, d4) + ")"
    if opcode == "110":
        if len(items) < 2:
            raise ProjectionBlocked("D3 COND requires at least one paired clause")
        clauses = []
        for item in items[1:]:
            if item[0] != "list" or len(item[1]) != 2:
                raise ProjectionBlocked("D3 COND requires two-part D2 clause records")
            clauses.append("(" + " ".join(render_uk(x, d1, d3, d4)
                                          for x in item[1]) + ")")
        return "(" + d3[opcode] + " " + " ".join(clauses) + ")"
    raise ProjectionBlocked("unratified callable in bounded renderer")


def canonical_uk_from_words(words: list[str]) -> str:
    d1, d3, d4 = uk_surface(1), uk_surface(3), uk_surface(4)
    return render_uk(WordParser(words).parse(), d1, d3, d4) + "\n"


def project_current_uk(source: str) -> list[str]:
    data = three_pass.load_foundation(ROOT / "knowledge/d1-d9-foundation.json")
    legacy, my, upper = three_pass.build_three_pass_maps(
        data,
        ROOT / "crates/sens/src/domain_surface_registry_generated.rs",
        ROOT / "crates/sens/src/semantic_registry_generated.rs",
        ROOT / "crates/sens/src/semantic_registry.rs",
        ROOT / "crates/sens/src/eval/necessary_forms_generated.rs",
        ROOT / "contracts/core1-historical-sid-map.lisp",
        ROOT / "knowledge/sens8-current-coverage-v1.json",
    )
    text7 = three_pass.build_text7(
        data, ROOT / "crates/sens/src/text7_projection_generated.rs"
    )
    resolver = three_pass.Resolver(legacy, my, upper, source_era="auto")
    visible = three_pass.migrate_file(source, resolver, text7)
    if (resolver.counts["pass1-sens8"] or resolver.counts["pass3-lisp15"]
            or resolver.counts["passthrough-head"]
            or resolver.counts["already-exact"]):
        raise ProjectionBlocked("non-ukrainian, historical or unknown source head")
    return visible.split()


def checked_file(path: Path) -> bytes:
    if not path.is_file():
        raise ProjectionBlocked(f"missing triplet file: {path}")
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ProjectionBlocked(f"symlink not admitted for triplet: {path}")
    return path.read_bytes()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify(lisp: Path, sens: Path, view: Path) -> dict:
    """Pure read-only 3-way proof, never creates an executable or a mirror."""
    if lisp.suffix != ".lisp" or sens != lisp.with_suffix(".sens") or view != lisp.with_suffix(""):
        raise ProjectionBlocked("all three inputs must be exact same-stem paths")
    src = checked_file(lisp)
    binary = checked_file(sens)
    readable = checked_file(view)
    try:
        source = src.decode("utf-8")
        words = decode_bytes(binary)
    except (UnicodeError, SensT5Error) as exc:
        raise ProjectionBlocked("invalid source UTF-8 or physical T5") from exc
    canonical_source = canonical_uk_from_words(words).encode("utf-8")
    if src != canonical_source:
        raise ProjectionBlocked("noncanonical українська ук source or wrong T5 semantics")
    canonical_view = (" ".join(words) + "\n").encode("ascii")
    if readable != canonical_view:
        raise ProjectionBlocked("missing, stale or noncanonical ASCII 0/1 view")
    if encode_words(words) != binary:
        raise ProjectionBlocked("physical T5 not byte-canonical")
    try:
        projected = project_current_uk(source)
    except (three_pass.MigrationError, SensT5Error, OSError, ValueError) as exc:
        raise ProjectionBlocked("Ukrainian source could not be encoded to exact words") from exc
    if projected != words or encode_words(projected) != binary:
        raise ProjectionBlocked("Ukrainian source and physical T5 do not agree")
    return {
        "schema": SCHEMA,
        "status": "BOUNDED_TRIPLE_PARITY_ONLY_NOT_RELEASE_ADMISSION",
        "scope": "D1 PREDICATE / D3 CAR COND QUOTE(EMPTY) CONS / D4 CAAR(CONS) / D2",
        "source": str(lisp),
        "sens": str(sens),
        "view": str(view),
        "source_sha256": sha256(src),
        "physical_sha256": sha256(binary),
        "view_sha256": sha256(readable),
        "typed_word_sha256": typed_sha256(words),
        "typed_word_count": len(words),
        "physical_bytes": len(binary),
        "physical_T5_roundtrip": True,
        "canonical_uk_roundtrip": True,
        "canonical_view_roundtrip": True,
        "runtime_oracle_admitted_by_this_audit": False,
        "old_originals_migrated_by_this_audit": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lisp", type=Path, required=True)
    parser.add_argument("--sens", type=Path, required=True)
    parser.add_argument("--view", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = verify(args.lisp, args.sens, args.view)
    except (ProjectionBlocked, OSError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
