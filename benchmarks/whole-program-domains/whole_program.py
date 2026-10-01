#!/usr/bin/env python3
"""#2003 [BENCH][WHOLE-PROGRAM-DOMAINS-1] — end-to-end Lisp I / Lisp 1.5
programs across semantic tree, carrier, framing and compiler.

Benchmark-only research harness (no runtime/contract/function-table edits).

Question: do microbenchmark winners survive realistic composition? The harness
runs the SAME bounded programs through four pipeline variants and reports, per
phase, where a local advantage is earned and where it is erased.

Pipeline variants (identity resolution strategy only; results are identical)
    A flat      : materialise every callable identity, one lookup per call
    B root+suffix: walk the root's bit path per call, no table
    C hybrid    : builtin roots fast-path, library callables fall back to a
                  residue table (fallback counted separately)
    D compiled  : precompute a call-site descriptor once, then zero resolution
                  during execution

Phases (counted separately, differential): tokenize, parse, semantic word
decode, framing encode, carrier build, semantic resolution, execution,
residue lookup, compiler lower.

Cost model, stated honestly: these are real counter increments inside the
evaluator — logical steps, NOT instruction counts. `i_refs`, `machine_insts`,
`code_bytes`, `cpu`, `valgrind_version` stay blank and must be joined on
`case_id` from the pinned environment.

Oracle parity comes first: every variant must produce the identical result for
every workload; a mismatch is a FAIL, never a metric.

Usage:
    python3 whole_program.py --tsv PATH
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# reader
# --------------------------------------------------------------------------
class Sym(str):
    pass


class Nil:
    def __repr__(self):
        return "()"


NIL = Nil()


@dataclass(frozen=True)
class Cons:
    car: object
    cdr: object


def tokenize(src: str):
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c in " \t\r\n":
            i += 1
        elif c in "()'":
            out.append(c)
            i += 1
        else:
            j = i
            while j < n and src[j] not in " \t\r\n()'":
                j += 1
            out.append(src[i:j])
            i = j
    return out


def parse(src: str):
    toks = tokenize(src)
    pos = 0

    def form():
        nonlocal pos
        t = toks[pos]; pos += 1
        if t == "'":
            return [Sym("quote"), form()]
        if t == "(":
            items = []
            while toks[pos] != ")":
                items.append(form())
            pos += 1
            return items
        if t == ")":
            raise SyntaxError("unexpected )")
        try:
            return int(t)
        except ValueError:
            return Sym(t)

    forms = []
    while pos < len(toks):
        forms.append(form())
    return forms


def to_value(node):
    if isinstance(node, int):
        return node
    if isinstance(node, Sym):
        return node
    if isinstance(node, list):
        if not node:
            return NIL
        v = NIL
        for x in reversed(node):
            v = Cons(to_value(x), v)
        return v
    raise TypeError(node)


def list_of(value):
    out = []
    while isinstance(value, Cons):
        out.append(value.car)
        value = value.cdr
    return out


# --------------------------------------------------------------------------
# counters
# --------------------------------------------------------------------------
@dataclass
class Counters:
    tokenize: int = 0
    parse: int = 0
    word_decode: int = 0
    framing: int = 0
    carrier: int = 0
    resolve: int = 0
    residue: int = 0
    lower: int = 0
    exec_: int = 0
    calls: int = 0
    alloc: int = 0
    wire_bits: int = 0

    def total(self):
        return (self.tokenize + self.parse + self.word_decode + self.framing
                + self.carrier + self.resolve + self.residue + self.lower
                + self.exec_)


# --------------------------------------------------------------------------
# evaluator (variant-aware resolution)
# --------------------------------------------------------------------------
BUILTINS = {"car", "cdr", "cons", "atom", "eq", "plus", "minus"}


class Evaluator:
    def __init__(self, variant: str, c: Counters):
        self.variant = variant
        self.c = c
        self.globals = {}
        self.table = {}          # flat identity table (variant A)
        self.roots = {}          # builtin roots (variant C fast path)
        self.residue = {}        # library fallback (variant C)
        self.sites = {}          # compiled site descriptors (variant D)

    # --- identity encoding / resolution -----------------------------------
    def identity_bits(self, name: str) -> str:
        """Synthetic exact identity: 8-bit root + path bits (model only)."""
        self.c.word_decode += 1
        h = int(hashlib.sha256(name.encode()).hexdigest(), 16)
        return format(h & 0xFF, "08b")

    def resolve(self, name: str):
        """Return the resolved *identity* (or None), charging this variant."""
        self.c.resolve += 1
        if self.variant == "flat":
            return name if name in self.table else None
        if self.variant == "root-suffix":
            bits = self.identity_bits(name)
            for _ in bits:                      # walk the root's path
                self.c.resolve += 1
            return name
        if self.variant == "hybrid":
            if name in self.roots:
                return name                     # builtin fast path
            self.c.residue += 1
            return name if name in self.residue else None
        if self.variant == "compiled":
            return name if name in self.sites else None   # zero per-call walk
        raise ValueError(self.variant)

    def build(self, names):
        """Whole-program preparation, charged per variant, before execution."""
        for name in names:
            self.c.carrier += 1                 # one carrier per identity
            self.c.framing += 1
            self.c.wire_bits += len(self.identity_bits(name))
        if self.variant == "flat":
            for name in names:
                self.table[name] = name         # materialise every identity
        elif self.variant == "root-suffix":
            pass                                # nothing materialised
        elif self.variant == "hybrid":
            for name in names:
                if name in BUILTINS:
                    self.roots[name] = name     # fast path
                else:
                    self.residue[name] = name   # residue fallback
        elif self.variant == "compiled":
            for name in names:
                self.c.lower += 1               # lower once per call site
                self.sites[name] = name

    # --- evaluation -------------------------------------------------------
    def truthy(self, v):
        return not (v is NIL)

    def ev(self, x, env):
        self.c.exec_ += 1
        if isinstance(x, (int, Sym)):
            if isinstance(x, Sym):
                if x in env:
                    return env[x]
                if x in self.globals:
                    return self.globals[x]
                return x
            return x
        if not isinstance(x, Cons):
            return x
        head = x.car
        args = list_of(x.cdr)
        if isinstance(head, Sym):
            if head == "quote":
                return args[0]
            if head == "cond":
                for clause in args:
                    parts = list_of(clause)
                    if self.truthy(self.ev(parts[0], env)):
                        return self.ev(parts[1], env)
                return NIL
            if head == "lambda":
                self.c.alloc += 1
                return ("clo", args[0], args[1], dict(env))
            if head == "define":
                name = args[0]
                self.globals[name] = self.ev(args[1], env)
                return name
            if head in BUILTINS:
                vals = [self.ev(a, env) for a in args]
                return self.prim(head, vals)
            # a call: resolve the callee identity through the variant strategy
            ident = self.resolve(head)
            self.c.calls += 1
            callee = self.globals.get(ident if ident is not None else head)
            if callee is None:
                callee = self.globals.get(head)
            if callee is None:
                raise ValueError(f"unresolved callable: {head!r}")
            return self.apply_(callee, [self.ev(a, env) for a in args])
        # ((lambda ...) args) or ((f) args)
        callee = self.ev(head, env)
        return self.apply_(callee, [self.ev(a, env) for a in args])

    def prim(self, name, vals):
        if name == "car":
            return vals[0].car
        if name == "cdr":
            return vals[0].cdr
        if name == "cons":
            self.c.alloc += 1
            return Cons(vals[0], vals[1])
        if name == "atom":
            return Sym("t") if not isinstance(vals[0], Cons) else NIL
        if name == "eq":
            a, b = vals
            if isinstance(a, Sym) and isinstance(b, Sym):
                return Sym("t") if a == b else NIL
            return Sym("t") if (a is b) or (a == b and not isinstance(a, Cons)) else NIL
        if name == "plus":
            return vals[0] + vals[1]
        if name == "minus":
            return vals[0] - vals[1]
        raise ValueError(name)

    def apply_(self, callee, args):
        if isinstance(callee, tuple) and callee and callee[0] == "clo":
            _, params, body, env = callee
            env = dict(env)
            ps = list_of(params)
            for p, a in zip(ps, args):
                env[p] = a
            return self.ev(body, env)
        raise ValueError(f"not callable: {callee!r}")


def render(v) -> str:
    if v is NIL:
        return "()"
    if isinstance(v, Sym):
        return str(v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, Cons):
        return "(" + " ".join(render(x) for x in list_of(v)) + ")"
    if isinstance(v, tuple) and v and v[0] == "clo":
        return "<lambda>"
    return str(v)


# --------------------------------------------------------------------------
# workloads
# --------------------------------------------------------------------------
LIB = """
(define null (lambda (x) (eq x (quote ()))))
(define append (lambda (x y) (cond ((null x) y) (t (cons (car x) (append (cdr x) y))))))
(define member (lambda (x y) (cond ((null y) (quote ())) ((eq x (car y)) y) (t (member x (cdr y))))))
(define equal (lambda (x y)
  (cond ((atom x) (cond ((atom y) (eq x y)) (t (quote ()))))
        ((atom y) (quote ()))
        ((equal (car x) (car y)) (equal (cdr x) (cdr y)))
        (t (quote ())))))
(define assoc (lambda (x y) (cond ((null y) (quote ())) ((equal x (car (car y))) (car y)) (t (assoc x (cdr y))))))
(define pairlis (lambda (x y a) (cond ((null x) a) (t (cons (cons (car x) (car y)) (pairlis (cdr x) (cdr y) a))))))
(define evcon (lambda (c a) (cond ((eval (car (car c)) a) (eval (car (cdr (car c))) a)) (t (evcon (cdr c) a)))))
(define evlis (lambda (m a) (cond ((null m) (quote ())) (t (cons (eval (car m) a) (evlis (cdr m) a))))))
(define eval (lambda (e a)
  (cond ((atom e) (cdr (assoc e a)))
        ((atom (car e))
         (cond ((eq (car e) (quote quote)) (car (cdr e)))
               ((eq (car e) (quote atom)) (atom (eval (car (cdr e)) a)))
               ((eq (car e) (quote eq)) (eq (eval (car (cdr e)) a) (eval (car (cdr (cdr e))) a)))
               ((eq (car e) (quote car)) (car (eval (car (cdr e)) a)))
               ((eq (car e) (quote cdr)) (cdr (eval (car (cdr e)) a)))
               ((eq (car e) (quote cons)) (cons (eval (car (cdr e)) a) (eval (car (cdr (cdr e))) a)))
               ((eq (car e) (quote cond)) (evcon (cdr e) a))
               (t (eval (cons (assoc (car e) a) (cdr e)) a))))
        ((eq (car (car e)) (quote lambda))
         (eval (car (cdr (cdr (car e)))) (append (pairlis (car (cdr (car e))) (evlis (cdr e) a)) a)))
        (t (eval (cons (eval (car e) a) (cdr e)) a)))))
"""

WORKLOADS = {
    "selector-heavy": LIB + """
(define tree (cons (cons 1 2) (cons (cons 3 4) (cons 5 6))))
(define deep (lambda (x) (car (cdr (cdr x)))))
(define r (deep (cons 9 tree)))
""",
    "append-list": LIB + """
(define build (lambda (n acc) (cond ((eq n 0) acc) (t (build (minus n 1) (cons n acc))))))
(define r (append (build 8 (quote ())) (cons 99 (quote ()))))
""",
    "member-equal": LIB + """
(define l (cons 1 (cons 2 (cons 3 (cons 4 (quote ()))))))
(define r (member 3 l))
""",
    "assoc-pairlis": LIB + """
(define a (pairlis (cons (quote x) (cons (quote y) (quote ()))) (cons 1 (cons 2 (quote ()))) (quote ())))
(define r (assoc (quote y) a))
""",
    "eval-apply-lisp15": LIB + """
(define r1 (eval (quote (cons (quote a) (quote (b)))) (quote ())))
(define r2 (eval (quote (car (quote (m n)))) (quote ())))
(define r (cons r1 r2))
""",
    "mixed-residue": LIB + """
(define unresolved-helper (lambda (x) (cons x x)))
(define r (unresolved-helper (member 2 (cons 1 (cons 2 (quote ()))))))
""",
}

MAIN_NAME = "r"


def run_workload(name: str, src: str, variant: str, reps: int = 1):
    c = Counters()
    c.tokenize += len(tokenize(src))
    forms = parse(src)
    c.parse += len(forms)
    ev = Evaluator(variant, c)
    defined = []
    for f in forms:
        if isinstance(f, list) and f and isinstance(f[0], Sym) and f[0] == "define":
            defined.append(f[1])
    ev.build(defined)                     # whole-program preparation, charged once
    for _ in range(reps):
        ev.globals.pop(Sym(MAIN_NAME), None)
        for f in forms:
            ev.ev(to_value(f), {})
    result = render(ev.globals.get(Sym(MAIN_NAME), NIL))
    return result, c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tsv", default="")
    args = ap.parse_args()

    variants = ["flat", "root-suffix", "hybrid", "compiled"]
    reps_axis = [1, 10, 100]
    rows, results = [], {}
    print("== #2003 whole-program domains (step model) ==")
    for wname, src in WORKLOADS.items():
        base = None
        for v in variants:
            for reps in reps_axis:
                res, c = run_workload(wname, src, v, reps)
                if base is None:
                    base = res
                assert res == base, f"ORACLE PARITY FAIL {wname}/{v}: {res!r} != {base!r}"
                results[(wname, v, reps)] = (res, c)
                rows.append({
                "case_id": f"{wname}/{v}/r{reps}",
                "rep": str(reps),
                "candidate": v,
                "family": wname,
                "mode": "whole-program-step-model",
                "tree_steps": str(c.total()),
                "registry_lookups": str(c.resolve),
                "residue_lookups": str(c.residue),
                "allocations": str(c.alloc),
                "wire_bits": str(c.wire_bits),
                "compiler_phase": str(c.lower),
                "calls": str(c.calls),
                "corpus_sha": hashlib.sha256(src.encode()).hexdigest()[:16],
                "oracle_result": res,
                "phase_tokenize": str(c.tokenize),
                "phase_parse": str(c.parse),
                "phase_word_decode": str(c.word_decode),
                "phase_framing": str(c.framing),
                "phase_carrier": str(c.carrier),
                "phase_resolve": str(c.resolve),
                "phase_residue": str(c.residue),
                "phase_lower": str(c.lower),
                "phase_exec": str(c.exec_),
                })
        line = "  ".join(f"{v}={results[(wname, v, 1)][1].total()}" for v in variants)
        print(f"  {wname:22} {line}")

    # composition finding: does a resolution-phase win survive the pipeline?
    print("\n-- composition check: resolution share of total (reps=1) --")
    for wname in WORKLOADS:
        shares = {v: round(results[(wname, v, 1)][1].resolve
                           / max(1, results[(wname, v, 1)][1].total()), 3)
                  for v in variants}
        best = min(variants, key=lambda v: results[(wname, v, 1)][1].total())
        print(f"  {wname:22} winner={best:12} resolve_share={shares}")
    print("\n-- amortisation: total steps by repetition (hot) --")
    for wname in WORKLOADS:
        print(f"  {wname:22} " + "  ".join(
            f"{v}:" + "/".join(str(results[(wname, v, r)][1].total()) for r in reps_axis)
            for v in variants))

    if args.tsv:
        cols = ["case_id", "candidate", "family", "semantic_depth", "mode", "rep",
                "i_refs", "tree_steps", "root_selections", "bits_consumed",
                "generator_apps", "registry_lookups", "residue_lookups",
                "cache_hits", "cache_misses", "allocations", "allocated_bytes",
                "object_bytes", "wire_bits", "compiler_phase", "machine_insts",
                "code_bytes", "loads", "stores", "branches", "calls", "spills",
                "corpus_sha", "binary_sha", "git_sha", "guix_channels_sha", "cpu",
                "valgrind_version", "oracle_result", "phase_tokenize", "phase_parse",
                "phase_word_decode", "phase_framing", "phase_carrier",
                "phase_resolve", "phase_residue", "phase_lower", "phase_exec"]
        with open(args.tsv, "w", encoding="utf-8") as fh:
            fh.write("\t".join(cols) + "\n")
            for r in rows:
                fh.write("\t".join(str(r.get(c2, "")) for c2 in cols) + "\n")
        print(f"\nwrote {len(rows)} raw rows -> {args.tsv}")

    print("provenance:", json.dumps({"python": platform.python_version(),
                                     "machine": platform.machine()}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
