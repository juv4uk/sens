#!/usr/bin/env python3
"""#2189: how do the standalone-envelope width streams (B, B2, B*) do on the word widths of REAL programs?  Research-only.

The word widths of real programs are not on `main` yet (no canonical binary program corpus), so this derives them from real
Lisp source under an EXPLICIT assumption, stated in code:

    ( ) .  ................ 2 bits  (racanā2)
    quote atom eq cond cons car cdr nil ... 3 bits  (bīja3, ratified; `'` = QUOTE)
    apply eval lambda define not evcon evlis list caar cadr cdar cddr lookup bind ... 4 bits  (ratified D4)
    every other token (a user name, a number, a string, a `c1-…` helper) ... 8 bits  (a Function8-sized identity)

It measures the framing bytes of B (count + 3 bits per width), B2 (run-length) and B* on (a) a whole file as one message and
(b) each top-level form as its own message. The widths are an assumption about a FUTURE encoding, not a measurement of one.
"""

from __future__ import annotations

import importlib.util
import re
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("tail", HERE / "research-2189-tail-length.py")
tail = importlib.util.module_from_spec(spec)
sys.modules["tail"] = tail
spec.loader.exec_module(tail)

D2 = {"(", ")", "."}
D3 = {"quote", "atom", "eq", "cond", "cons", "car", "cdr", "nil", "'"}
D4 = {"apply", "eval", "lambda", "define", "not", "evcon", "evlis", "list", "caar", "cadr", "cdar", "cddr", "lookup", "bind"}


def tokens(text: str):
    text = re.sub(r";[^\n]*", "", text)
    text = re.sub(r'"(?:[^"\\]|\\.)*"', "STR", text)
    return re.findall(r"[()']|[^\s()']+", text)


def width_of(tok: str) -> int:
    low = tok.lower()
    if low in D2:
        return 2
    if low in D3:
        return 3
    if low in D4:
        return 4
    return 8


def forms(toks):
    depth, cur, out = 0, [], []
    for t in toks:
        cur.append(t)
        depth += (t == "(") - (t == ")")
        if depth == 0 and cur:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def seq_of(ws):
    return tuple((w, 0) for w in ws)           # values do not matter for the framing of the widths


def framing(ws):
    seq = seq_of(ws)
    pb = (sum(ws) + 7) // 8
    return len(tail.enc_b(seq)) - pb, len(tail.enc_b2(seq)) - pb, len(tail.enc_bstar(seq)) - pb, pb, len(tail.enc_b4(seq)) - pb


def main(argv):
    root = Path(argv[1]) if len(argv) > 1 else HERE.parent
    files = ["lib/core1.lisp", "lib/core2.lisp", "lib/core3.lisp", "lib/core4.lisp", "benchmarks/lists.lisp", "benchmarks/recursion.lisp"]
    print("# research-2189 program widths (ASSUMED widths of real Lisp source: see the module docstring)\n")
    print("whole file as ONE message:")
    print(f"  {'file':26} {'words':>6} {'payload B':>9} {'runs':>5}   framing bytes   B   B2   B*   B4")
    for f in files:
        p = root / f
        if not p.exists():
            continue
        ws = [width_of(t) for t in tokens(p.read_text(encoding="utf-8"))]
        if not ws:
            continue
        b, b2, bs, pb, b4 = framing(ws)
        runs = len(tail.runs_of(ws))
        print(f"  {f:26} {len(ws):>6} {pb:>9} {runs:>5}                 {b:>3} {b2:>4} {bs:>4} {b4:>4}")
    print("\neach top-level form as its own message (mean framing bytes per form, and the share of forms where each is the cheapest):")
    for f in files:
        p = root / f
        if not p.exists():
            continue
        fs = [[width_of(t) for t in form] for form in forms(tokens(p.read_text(encoding="utf-8")))]
        fs = [w for w in fs if w]
        if not fs:
            continue
        rows = [framing(w) for w in fs]
        mean = [round(statistics.mean(r[i] for r in rows), 2) for i in (0, 1, 2, 4)]
        b_best = sum(1 for r in rows if r[0] <= r[1]) / len(rows)
        print(f"  {f:26} {len(fs):>5} forms   B {mean[0]:>6}  B2 {mean[1]:>6}  B* {mean[2]:>6}  B4 {mean[3]:>6}   B <= B2 in {b_best:.0%} of forms")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
