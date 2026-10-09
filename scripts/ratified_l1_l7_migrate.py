#!/usr/bin/env python3
"""L1-L7 ratified legacy-to-canon staging gate.

Reuses the existing three-pass S-expression reader and physical T5 codec.
Conservative by design: no source overwrite, no invented D10 coordinates,
no truthiness inference, no retired-form replay and no unproven semantic oracle.
This is a migration *stage*, not a replacement for runtime semantic proofs.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from domain_tables import read_domain_table
from sens_t5_codec import encode_projection, decode_bytes, parse_words, typed_sha256

spec = importlib.util.spec_from_file_location("_l1_l7_existing_reader", SCRIPTS / "migrate-three-pass.py")
if spec is None or spec.loader is None:
    raise RuntimeError("canonical three-pass reader unavailable")
reader = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = reader
spec.loader.exec_module(reader)

EXACT_BIT = re.compile(r"[01]\Z")
EXACT_CODE = re.compile(r"[01]{3,9}\Z")
RETIRED = {"structural-kind", "identity-relation", "structural_kind", "identity_relation"}
LEGACY_HELPERS = {"equal?", "null", "null?"}
EXACT_D3_PREDICATES = {"010", "101"}
CONDITIONAL = "110"
QUOTATION = "001"


class Block(Exception):
    def __init__(self, rule: str, detail: str):
        super().__init__(detail)
        self.rule, self.detail = rule, detail


@dataclass
class Context:
    source_era: str = "auto"
    events: list[dict] = field(default_factory=list)
    proposals: set[str] = field(default_factory=set)

    def record(self, rule: str, detail: str) -> None:
        self.events.append({"rule": rule, "detail": detail})

    def stop(self, rule: str, detail: str, proposal: str | None = None) -> None:
        if proposal:
            self.proposals.add(proposal)
        raise Block(rule, detail)


def registry():
    """Read existing ratified tables, never derive an address from an English name."""
    by_name: dict[str, set[str]] = {}
    by_code: dict[str, object] = {}
    predicate_codes: set[str] = set(EXACT_D3_PREDICATES)
    # D7 is Text/Sound and not an executable-function domain.
    for width in (3, 4, 5, 6, 8, 9):
        for row in read_domain_table(ROOT / "lib" / "domains" / f"d{width}.lisp"):
            by_code[row.bits] = row
            for name in (row.uk, row.ukr, row.san, row.en, row.lisp, row.sym):
                if name and name != "()":
                    by_name.setdefault(name, set()).add(row.bits)
            if row.en and row.en.endswith("?"):
                predicate_codes.add(row.bits)
    return by_name, by_code, predicate_codes


def atom(text: str, original):
    return reader.Atom(reader.Tok("ATOM", text, original.tok.offset))


def head(node):
    if isinstance(node, reader.ListNode) and node.items and isinstance(node.items[0], reader.Atom):
        return node.items[0].tok.text
    return None


class Normalizer:
    def __init__(self, context: Context):
        self.ctx = context
        self.names, self.codes, self.predicates = registry()

    def callable(self, name: str) -> str:
        ctx = self.ctx
        if name.lower() in RETIRED:
            ctx.stop("L5", f"retired executable form {name}: archaeology only, exclude from live corpus")
        if name in {"t", "T"}:
            ctx.stop("L2", "t is not a special executable operation")
        if name in LEGACY_HELPERS:
            # L4: only the actual D8 resident is accepted; a D3 macro must be
            # supplied by an independently proved law generator, not invented here.
            d8 = {bits for bits in self.names.get(name, ()) if len(bits) == 8}
            if len(d8) != 1:
                ctx.stop("L4", f"{name}: no unique D8 resident; D3 law-generated expansion required", name)
            code = next(iter(d8))
            ctx.record("L4", f"{name} -> D8:{code}")
            return code
        if EXACT_CODE.fullmatch(name):
            if len(name) == 7 or name not in self.codes:
                ctx.stop("L3", f"no callable current domain coordinate for {name}", name)
            if len(name) == 8 and ctx.source_era != "current":
                ctx.stop("L3", f"W8 {name} is ambiguous with historical SID8; explicitly prove current era")
            return name
        matches = self.names.get(name, ())
        if len(matches) != 1:
            ctx.stop("L3", f"{name}: missing or ambiguous current domain coordinate; D10 proposal", name)
        code = next(iter(matches))
        if code == "000":
            ctx.stop("L3", "D3 EMPTY is structural, not callable", name)
        ctx.record("L3", f"{name} -> D{len(code)}:{code}")
        return code

    def exact_predicate(self, node) -> bool:
        if isinstance(node, reader.Atom) and EXACT_BIT.fullmatch(node.tok.text):
            return True
        if isinstance(node, reader.ListNode):
            return head(node) in self.predicates
        return False

    def walk(self, node, *, data=False):
        if isinstance(node, reader.Quote):
            return node  # lexical quote is DATA; no executable-head conversion
        if isinstance(node, (reader.Atom, reader.String)):
            return node
        if not isinstance(node, reader.ListNode):
            self.ctx.stop("L7", "unknown reader node")
        if data or not node.items:
            return node
        if node.tail is not None:
            self.ctx.stop("L3", "executable dotted list requires an explicit law")
        first = node.items[0]
        if not isinstance(first, reader.Atom):
            self.ctx.stop("L3", "computed callable head has no static domain identity")
        code = self.callable(first.tok.text)
        items = [atom(code, first)]
        if code == QUOTATION:
            items.extend(node.items[1:])  # protect quoted data
        elif code == CONDITIONAL:
            for clause in node.items[1:]:
                if not isinstance(clause, reader.ListNode) or clause.tail is not None:
                    self.ctx.stop("L1", "COND clause must be a proper two-part list")
                if len(clause.items) != 2:
                    self.ctx.stop("L1", "legacy three-part or malformed COND: preserve polarity, require oracle")
                test, expr = clause.items
                if isinstance(test, reader.Atom) and test.tok.text in {"t", "T"}:
                    test = atom("1", test)
                    self.ctx.record("L2", "(t expression) -> (1 expression), no global t special form")
                else:
                    test = self.walk(test)
                if not self.exact_predicate(test):
                    self.ctx.stop("L1", "COND test not proved exact PredicateBit 1/0")
                items.append(reader.ListNode([test, self.walk(expr)], None, clause.tok))
            self.ctx.record("L1", "exhausted COND has no injected else; canonical result must be structural EMPTY ()")
        elif code == "0010":  # D4 LAMBDA: parameter identifiers are binders, not calls.
            if len(node.items) < 3:
                self.ctx.stop("L3", "LAMBDA has no complete binder/body evidence")
            items.append(node.items[1])
            items.extend(self.walk(expr) for expr in node.items[2:])
        elif code == "0011":  # D4 DEFINE: name or signature is binding data.
            if len(node.items) < 3:
                self.ctx.stop("L3", "DEFINE has no complete target/body evidence")
            items.append(node.items[1])
            items.extend(self.walk(expr) for expr in node.items[2:])
        else:
            items.extend(self.walk(expr) for expr in node.items[1:])
        return reader.ListNode(items, None, node.tok)


def exact_words(node):
    """Exact-domain D2/D3 mechanical emitter; no free-text atom frame guesses."""
    if isinstance(node, reader.Quote):
        return ["10", "001", "00", *exact_words(node.value), "01"]
    if isinstance(node, reader.String):
        raise Block("L3", "string has no verified executable Text7/D2 atom frame")
    if isinstance(node, reader.Atom):
        name = node.tok.text
        if EXACT_BIT.fullmatch(name) or (EXACT_CODE.fullmatch(name) and len(name) != 7):
            return [name]
        raise Block("L3", f"unframed/non-domain data {name!r}; defer to canonical binder/atom emitter")
    if isinstance(node, reader.ListNode):
        if node.tail is not None:
            raise Block("L3", "dotted data needs independently certified projection")
        if not node.items:
            return ["000"]
        result = ["10"]
        for i, child in enumerate(node.items):
            if i:
                result.append("00")
            result.extend(exact_words(child))
        return result + ["01"]
    raise Block("L7", "reader node is not known to exact-domain emitter")


def migrate(source: str, ctx: Context):
    try:
        forms = reader.Parser(reader.tokenize(reader.strip_comments(source))).parse_program()
    except (reader.MigrationError, RecursionError, ValueError) as exc:
        ctx.stop("L7", f"unparseable source: {exc}; unchanged, owner-review list")
    normalized = Normalizer(ctx)
    new_forms = [normalized.walk(form) for form in forms]
    words = []
    for i, form in enumerate(new_forms):
        if i:
            words.append("00")
        words.extend(exact_words(form))
    if not words:
        ctx.stop("L7", "empty file has no admitted executable program")
    projection = " ".join(words) + "\n"
    try:
        checked = parse_words(projection)
        payload = encode_projection(projection)
        if decode_bytes(payload) != checked:
            ctx.stop("ORACLE", "physical T5 roundtrip changed typed words")
    except Exception as exc:
        ctx.stop("L3", f"canonical physical emitter rejected program: {exc}")
    return payload, typed_sha256(words)


def run_oracle(executable: Path, source: Path, candidate: Path):
    """Independent oracle executable must emit two matching semantic digests."""
    proc = subprocess.run([str(executable), str(source), str(candidate)],
                          capture_output=True, text=True, timeout=120, check=False)
    if proc.returncode:
        raise Block("ORACLE", f"independent oracle rejected candidate (exit {proc.returncode})")
    try:
        report = json.loads(proc.stdout)
        original = report["source_semantic_sha256"]
        current = report["candidate_semantic_sha256"]
    except (ValueError, KeyError, TypeError):
        raise Block("ORACLE", "oracle must provide source_semantic_sha256 and candidate_semantic_sha256")
    if not (re.fullmatch(r"[a-f0-9]{64}", original)
            and re.fullmatch(r"[a-f0-9]{64}", current)
            and original == current):
        raise Block("ORACLE", "semantic digests differ or are invalid")
    return original


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("target", type=Path, help="one .lisp file or source directory")
    ap.add_argument("--source-era", choices=("auto", "current"), default="auto")
    ap.add_argument("--report", type=Path)
    ap.add_argument("--apply", action="store_true", help="write new .sens file only after oracle PASS")
    ap.add_argument("--out", type=Path, help="separate output root; existing targets never overwritten")
    ap.add_argument("--oracle-bin", type=Path, help="independent semantic oracle: source-path candidate-path -> JSON digests")
    args = ap.parse_args(argv)
    if args.apply and (args.out is None or args.oracle_bin is None):
        ap.error("--apply requires both --out and --oracle-bin")
    if args.out is not None and not args.apply:
        ap.error("--out is meaningful only with --apply")
    if not args.target.exists():
        ap.error("source not found")
    files = ([args.target] if args.target.is_file()
             else sorted(args.target.rglob("*.lisp")))
    base = args.target.parent if args.target.is_file() else args.target
    rows = []
    for path in files:
        ctx = Context(args.source_era)
        relative = path.relative_to(base)
        row = {"path": relative.as_posix(), "source_sha256": None,
               "status": "BLOCK", "rules": [], "d10_proposals": []}
        try:
            raw = path.read_bytes()
            row["source_sha256"] = hashlib.sha256(raw).hexdigest()
            if "fixtures" in path.parts:
                ctx.stop("L6", "fixture requires regeneration by canonical generator; do not hand-edit")
            payload, digest = migrate(raw.decode("utf-8"), ctx)
            row["physical_sha256"] = hashlib.sha256(payload).hexdigest()
            row["typed_word_sha256"] = digest
            if args.apply:
                target = args.out / relative.with_suffix(".sens")
                if target.exists() or target.is_symlink() or target.resolve() == path.resolve():
                    ctx.stop("EMIT", "destination exists or aliases source; no overwrite")
                with tempfile.TemporaryDirectory() as directory:
                    staged = Path(directory) / "candidate.sens"
                    staged.write_bytes(payload)
                    row["semantic_sha256"] = run_oracle(args.oracle_bin, path, staged)
                target.parent.mkdir(parents=True, exist_ok=True)
                # no clobber: exclusive creation, not a copy into an existing file
                with target.open("xb") as destination:
                    destination.write(payload)
                row["status"] = "EMITTED-ORACLE-PASS"
            else:
                row["status"] = "DRY-RUN-ORACLE-REQUIRED"
        except (Block, UnicodeError, OSError, RecursionError, subprocess.TimeoutExpired) as exc:
            row["reason"] = str(exc)
            row["blocked_rule"] = exc.rule if isinstance(exc, Block) else "L7"
        row["rules"] = ctx.events
        row["d10_proposals"] = sorted(ctx.proposals)
        rows.append(row)
    report = {"schema": "sens-ratified-l1-l7-migration/v1",
              "ratified_rules": ["L1", "L2", "L3", "L4", "L5", "L6", "L7"],
              "note": "typed_word_sha256 is transport integrity, not semantic equivalence",
              "results": rows}
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 4 if any(r["status"] == "BLOCK" for r in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
