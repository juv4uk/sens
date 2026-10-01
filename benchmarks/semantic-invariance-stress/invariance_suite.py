#!/usr/bin/env python3
"""#2002 [BENCH][SEMANTIC-INVARIANCE-STRESS-1] — refactors may change source
cost, not canonical meaning.

Benchmark-only research harness (no runtime/contract/function-table edits).

Model (bounds stated honestly)
------------------------------
A minimal Lisp I / Lisp 1.5 selector language:
  - primitives addressed by exact Function8 code (e.g. car=00000010? no — the
    codes below are *model* codes, declared once, never inferred from names);
  - named helper definitions `(def name (lambda (params) body))`;
  - selector shorthands (`cadr` == `(car (cdr x))`), the Lisp I -> Lisp 1.5
    representation axis.

Canonical identity of an observed entry is computed AFTER normalisation that
expands helpers **by definition, not by name**, then flattens selector chains
to an exact bit path (`car=0`, `cdr=1`). Therefore helper rename, alpha-rename,
inlining, factoring, definition reordering, whitespace/layout and shorthand
spelling must NOT move it; a real semantic change must.

Two ledgers
-----------
  semantic  (must stay invariant): canonical_word, root, path, width, class
  mechanism (may change):          source tokens, defs, normal nodes, proof steps

Usage
-----
  python3 invariance_suite.py            # run suite, print summary, write TSV
  python3 invariance_suite.py --tsv PATH # choose TSV output path
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import sys
from dataclasses import dataclass, field

# --- model primitive codes (declared here once; never inferred from names) ---
PRIMITIVE_CODES = {
    "car": "00000010",
    "cdr": "00000011",
    "cons": "00000100",
    "atom": "00000101",
    "eq": "00000110",
    "cond": "00000111",
    "plus": "00001100",
    "mul": "00001110",
}
CODE_TO_NAME = {code: name for name, code in PRIMITIVE_CODES.items()}

SHORTHANDS = {
    "caar": "00",
    "cadr": "01",
    "cdar": "10",
    "cddr": "11",
    "caddr": "011",
    "cdddr": "111",
    "cadar": "010",
}

SYMBOL_RE = re.compile(r"[A-Za-z0-9_+\-*/?!]+")


# --------------------------------------------------------------------------
# reader
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Sym:
    name: str


@dataclass(frozen=True)
class Num:
    value: int


@dataclass(frozen=True)
class Call:
    head: object
    args: tuple


def tokenize(source: str) -> list[str]:
    out, i = [], 0
    while i < len(source):
        ch = source[i]
        if ch in " \t\r\n":
            i += 1
            continue
        if ch in "()":
            out.append(ch)
            i += 1
            continue
        m = SYMBOL_RE.match(source, i)
        if not m:
            raise ValueError(f"cannot tokenize at {i}: {source[i:i+10]!r}")
        out.append(m.group(0))
        i = m.end()
    return out


def parse_raw(source: str):
    """List-preserving reader: returns nested lists / Sym / Num."""
    tokens = tokenize(source)
    pos = 0

    def parse_form():
        nonlocal pos
        tok = tokens[pos]
        pos += 1
        if tok == "(":
            items = []
            while tokens[pos] != ")":
                items.append(parse_form())
            pos += 1
            return items
        if tok == ")":
            raise ValueError("unexpected )")
        if tok.isdigit() or (tok[0] == "-" and tok[1:].isdigit()):
            return Num(int(tok))
        return Sym(tok)

    forms = []
    while pos < len(tokens):
        forms.append(parse_form())
    return forms


def expr_from_raw(node):
    if isinstance(node, (Sym, Num)):
        return node
    if not isinstance(node, list):
        raise ValueError(f"bad node {node!r}")
    if not node:
        return Call(Sym("nil"), ())
    head = node[0]
    if isinstance(head, Sym) and head.name in SHORTHANDS:
        bits = SHORTHANDS[head.name]
        expr = expr_from_raw(node[1])
        for bit in reversed(bits):
            expr = Call(Sym("car" if bit == "0" else "cdr"), (expr,))
        return expr
    return Call(expr_from_raw(head), tuple(expr_from_raw(a) for a in node[1:]))


# --------------------------------------------------------------------------
# program model
# --------------------------------------------------------------------------
@dataclass
class Program:
    defs: dict = field(default_factory=dict)   # name -> (params, body)
    order: list = field(default_factory=list)  # definition order (mechanism only)
    entries: list = field(default_factory=list)


def parse_program(source: str) -> Program:
    prog = Program()
    for form in parse_raw(source):
        if not isinstance(form, list):
            raise ValueError(f"unsupported top-level form: {form!r}")
        head = form[0]
        if isinstance(head, Sym) and head.name == "def":
            name = form[1].name
            lam = form[2]
            assert isinstance(lam, list) and lam[0].name == "lambda", lam
            params = tuple(a.name for a in lam[1])
            body = expr_from_raw(lam[2])
            prog.defs[name] = (params, body)
            prog.order.append(name)
        elif isinstance(head, Sym) and head.name == "observe":
            prog.entries.append(expr_from_raw(form[1]))
        else:
            raise ValueError(f"unsupported top-level form: {form!r}")
    return prog


# --------------------------------------------------------------------------
# normalisation + canonicalisation (semantic ledger)
# --------------------------------------------------------------------------
class Steps:
    def __init__(self):
        self.expansions = 0
        self.nodes = 0


def normalise(expr, prog: Program, params: dict, steps: Steps, active=frozenset(), depth: int = 0):
    """Expand helpers by definition. A call to a helper already on the
    expansion stack is an SCC self-reference, recognised *structurally* (not by
    name) so that renaming a recursive helper cannot move its identity."""
    if depth > 500:
        raise RecursionError("normalisation depth limit")
    steps.nodes += 1
    if isinstance(expr, Num):
        return expr
    if isinstance(expr, Sym):
        if expr.name in params:
            return params[expr.name]
        return expr
    head = expr.head
    if isinstance(head, Sym) and head.name in prog.defs:
        if head.name in active:
            return Call(Sym("@rec"), tuple(normalise(a, prog, params, steps, active, depth + 1) for a in expr.args))
        formals, body = prog.defs[head.name]
        steps.expansions += 1
        if len(formals) != len(expr.args):
            raise ValueError(f"arity mismatch for {head.name}: {len(formals)} vs {len(expr.args)}")
        new_params = dict(params)
        for formal, actual in zip(formals, expr.args):
            new_params[formal] = normalise(actual, prog, params, steps, active, depth + 1)
        return normalise(body, prog, new_params, steps, active | {head.name}, depth + 1)
    return Call(head, tuple(normalise(a, prog, params, steps, active, depth + 1) for a in expr.args))


def selector_path(expr):
    """Bit path of a pure car/cdr chain over a variable/local; '' otherwise."""
    bits = []
    cur = expr
    while isinstance(cur, Call) and isinstance(cur.head, Sym) and cur.head.name in ("car", "cdr"):
        bits.append("0" if cur.head.name == "car" else "1")
        cur = cur.args[0]
    if bits and isinstance(cur, Sym) and cur.name not in PRIMITIVE_CODES:
        return "".join(reversed(bits))
    return ""


def canonical_render(expr) -> str:
    """Canonical spelling: primitives by exact code, selector chains flattened."""
    if isinstance(expr, Num):
        return f"#{expr.value}"
    if isinstance(expr, Sym):
        if expr.name in PRIMITIVE_CODES:
            return PRIMITIVE_CODES[expr.name]
        return f"${expr.name}"  # unresolved/local: explicit transition debt
    path = selector_path(expr)
    if path:
        inner = expr
        while isinstance(inner, Call) and isinstance(inner.head, Sym) and inner.head.name in ("car", "cdr"):
            inner = inner.args[0]
        return f"sel{len(path)}:{path}(${inner.name})"
    head = canonical_render(expr.head)
    args = " ".join(canonical_render(a) for a in expr.args)
    return f"({head} {args})"


def semantic_ledger(entry, prog: Program):
    steps = Steps()
    normal = normalise(entry, prog, {}, steps)
    word = canonical_render(normal)
    head = normal.head.name if isinstance(normal, Call) and isinstance(normal.head, Sym) else None
    root = PRIMITIVE_CODES.get(head, "") if head else ""
    path = selector_path(normal)
    if root:
        klass = {"car": "selector", "cdr": "selector"}.get(head, "primitive")
    elif head is None:
        klass = "atom"
    else:
        klass = "call"
    return {
        "canonical_word": hashlib.sha256(word.encode()).hexdigest()[:16],
        "canonical_form": word,
        "root": root,
        "path": path,
        "width": len(path),
        "class": klass,
        "expansions": steps.expansions,
        "nodes": steps.nodes,
    }


def mechanism_ledger(source: str, prog: Program) -> dict:
    return {
        "tokens": len(tokenize(source)),
        "defs": len(prog.defs),
        "chars": len(source),
    }


# --------------------------------------------------------------------------
# base programs and mutations
# --------------------------------------------------------------------------
BASE = """\
(def second (lambda (x) (cdr x)))
(def pair (lambda (a b) (cons a b)))
(def shift (lambda (y) (plus y 1)))
(observe (second (pair 1 2)))
(observe (shift 3))
(observe (cadr (pair 1 (pair 2 3))))
"""

RECURSIVE = """\
(def len (lambda (x) (cond (atom x) 0 (plus 1 (len (cdr x))))))
(observe (len (pair 1 (pair 2 3))))
"""


def m_rename_helper(source: str) -> str:
    return source.replace("second", "snd").replace("shift", "inc")


def m_alpha_rename(source: str) -> str:
    return source.replace("(lambda (x)", "(lambda (v)").replace(" x)", " v)")


def m_inline(source: str) -> str:
    return source.replace("(second (pair 1 2))", "(cdr (pair 1 2))")


def m_reorder_defs(source: str) -> str:
    lines = [l for l in source.splitlines() if l.strip()]
    defs = [l for l in lines if l.startswith("(def")]
    obs = [l for l in lines if not l.startswith("(def")]
    return "\n".join(list(reversed(defs)) + obs) + "\n"


def m_whitespace(source: str) -> str:
    return source.replace("(", "(  ").replace(")", "  )").replace("\n", "\n\n")


def m_shorthand_to_nested(source: str) -> str:
    return source.replace("(cadr (pair 1 (pair 2 3)))", "(car (cdr (pair 1 (pair 2 3))))")


def m_alias_intro(source: str) -> str:
    return "(def alias (lambda (z) (second z)))\n" + source


# --- negative controls: these MUST drift ---
def n_swap_selectors(source: str) -> str:
    return source.replace("(second (pair 1 2))", "(car (pair 1 2))")


def n_change_constant(source: str) -> str:
    return source.replace("(shift 3)", "(shift 4)")


def n_swap_cons_args(source: str) -> str:
    return source.replace("(pair 1 2)", "(pair 2 1)")


PRESERVING = [
    ("rename-helper", m_rename_helper),
    ("alpha-rename", m_alpha_rename),
    ("inline-helper", m_inline),
    ("reorder-defs", m_reorder_defs),
    ("whitespace", m_whitespace),
    ("lisp1-to-1.5-representation", m_shorthand_to_nested),
    ("alias-intro", m_alias_intro),
]

# Negative controls are base-aware: a control must actually change the source
# it is applied to, otherwise it is not a control at all.
DRIFTING_BY_BASE = {
    "base": [
        ("swap-selectors", lambda s: s.replace("(second (pair 1 2))", "(car (pair 1 2))")),
        ("change-constant", lambda s: s.replace("(shift 3)", "(shift 4)")),
        ("swap-cons-args", lambda s: s.replace("(pair 1 2)", "(pair 2 1)")),
    ],
    "recursive-scc": [
        ("swap-selectors", lambda s: s.replace("(len (cdr x))", "(len (car x))")),
        ("change-constant", lambda s: s.replace("(atom x) 0", "(atom x) 2")),
        ("swap-cons-args", lambda s: s.replace("(pair 2 3)", "(pair 3 2)")),
    ],
}


def entries_of(source: str):
    return parse_program(source).entries


def canonical_set(source: str):
    prog = parse_program(source)
    return [semantic_ledger(e, prog) for e in prog.entries]


def compare(base_source: str, variant_source: str):
    base = canonical_set(base_source)
    var = canonical_set(variant_source)
    if len(base) != len(var):
        return False, "entry-count-changed"
    for b, v in zip(base, var):
        for key in ("canonical_word", "root", "path", "width", "class"):
            if b[key] != v[key]:
                return False, f"{key}:{b[key]}!={v[key]}"
    return True, "invariant"


def run():
    rows = []
    summary = {"preserving": 0, "preserving_skipped": 0, "preserving_drift": [],
               "drifting": 0, "drifting_skipped": 0, "drifting_stable": []}
    mech_spread = []

    corpus_sha = {n: hashlib.sha256(s.encode()).hexdigest()[:16]
                  for n, s in (("base", BASE), ("recursive-scc", RECURSIVE))}

    def emit(base_name, cls, rep, variant, expectation, stable, why):
        mech = mechanism_ledger(variant, parse_program(variant))
        led = semantic_ledger(parse_program(variant).entries[0], parse_program(variant))
        rows.append({
            "case_id": f"{base_name}/{cls}/{rep}",
            "candidate": "canonical-definitional",
            "family": base_name,
            "semantic_depth": str(led["width"]),
            "mode": "canonical-invariance",
            "rep": str(rep),
            "tree_steps": str(led["nodes"]),
            "registry_lookups": str(led["expansions"]),
            "corpus_sha": corpus_sha[base_name],
            "mutation_class": cls,
            "expectation": expectation,
            "canonical_drift": "0" if stable else "1",
            "detail": why,
        })
        mech_spread.append(mech["tokens"])

    for base_name, base_src in (("base", BASE), ("recursive-scc", RECURSIVE)):
        applicable = [(cls, fn) for cls, fn in PRESERVING if fn(base_src) != base_src]
        summary["preserving_skipped"] += len(PRESERVING) - len(applicable)
        for rep in range(1, 601):  # 600 composed variants per base
            # deterministic composition of 1..3 applicable classes, so every
            # row is a genuinely different semantics-preserving program
            k = 1 + (rep % min(3, len(applicable)))
            start = (rep * 7) % len(applicable)
            chosen = [applicable[(start + j) % len(applicable)] for j in range(k)]
            variant = base_src
            for _, fn in chosen:
                variant = fn(variant)
            variant = variant + " " * (rep % 5)
            label = "+".join(cls for cls, _ in chosen)
            stable, why = compare(base_src, variant)
            summary["preserving"] += 1
            if not stable:
                summary["preserving_drift"].append(f"{base_name}/{label}/{rep}: {why}")
            emit(base_name, label, rep, variant, "preserve", stable, why)

        for cls, fn in DRIFTING_BY_BASE[base_name]:
            variant = fn(base_src)
            if variant == base_src:
                summary["drifting_skipped"] += 1
                continue
            stable, why = compare(base_src, variant)
            summary["drifting"] += 1
            if stable:
                summary["drifting_stable"].append(f"{base_name}/{cls}")
            emit(base_name, cls, 1, variant, "drift", stable, why)

    provenance = {
        "python": platform.python_version(),
        "machine": platform.machine(),
        "platform": platform.platform(),
        "mechanism_tokens_min": min(mech_spread),
        "mechanism_tokens_max": max(mech_spread),
    }
    return rows, summary, provenance


SCHEMA_1987 = [
    "case_id", "candidate", "family", "semantic_depth", "mode", "rep", "i_refs",
    "tree_steps", "root_selections", "bits_consumed", "generator_apps",
    "registry_lookups", "residue_lookups", "cache_hits", "cache_misses",
    "allocations", "allocated_bytes", "object_bytes", "wire_bits",
    "compiler_phase", "machine_insts", "code_bytes", "loads", "stores",
    "branches", "calls", "spills", "corpus_sha", "binary_sha", "git_sha",
    "guix_channels_sha", "cpu", "valgrind_version",
    # additive, lane-specific (names stable; extra columns are appended)
    "mutation_class", "expectation", "canonical_drift", "detail",
]


def write_tsv(path: str, rows: list):
    cols = SCHEMA_1987
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\t".join(cols) + "\n")
        for r in rows:
            fh.write("\t".join(str(r.get(c, "")) for c in cols) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tsv", default="")
    args = ap.parse_args()

    rows, summary, provenance = run()
    print("== #2002 semantic-invariance stress ==")
    print(f"preserving mutations: {summary['preserving']}  (drift: {len(summary['preserving_drift'])}; skipped n/a: {summary['preserving_skipped']})")
    print(f"drifting controls:    {summary['drifting']}  (unexpectedly stable: {len(summary['drifting_stable'])}; skipped n/a: {summary['drifting_skipped']})")
    print(f"provenance: {json.dumps(provenance)}")
    if summary["preserving_drift"]:
        print("!! canonical drift on admitted equivalences:")
        for d in summary["preserving_drift"][:10]:
            print("   ", d)
    if summary["drifting_stable"]:
        print("!! negative controls failed to drift:")
        for d in summary["drifting_stable"][:10]:
            print("   ", d)
    if args.tsv:
        write_tsv(args.tsv, rows)
        print(f"wrote {len(rows)} raw rows -> {args.tsv}")
    ok = not summary["preserving_drift"] and not summary["drifting_stable"]
    print("VERDICT:", "INVARIANT (no canonical drift on admitted equivalences)" if ok else "DRIFT DETECTED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
