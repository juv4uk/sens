#!/usr/bin/env python3
"""Fail-closed guard for #4166: current tier-1 *constitutive* COND rows must
not carry generic truthiness.

Consumes the existing Lisp-owned transition overlay
(`conformance-transition-witness.lisp`, `supersedes-expr`) instead of inventing
a second classification framework.  A row superseded there no longer owns the
current denominator; every other tier-1 constitutive COND row must obey
`contracts/answer-contract.lisp` D3:110:
    clause-shape = (test expression)  -> each clause has exactly 2 elements
                                         (test + expression); clause COUNT is not fixed
    zero-equals-empty / generic-truthiness / three-part-clause = forbidden
"""
import re, sys, pathlib

FIX = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "conformance.lisp")
OVL = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "conformance-transition-witness.lisp")


def rows(text):
    out = []
    for chunk in text.split('((expr . "')[1:]:
        expr = chunk.split('")', 1)[0]
        tier = re.search(r"\(tier \. (\d+)\)", chunk)
        role = re.search(r'\(role \. "([^"]+)"\)', chunk)
        out.append({"expr": expr,
                    "tier": int(tier.group(1)) if tier else None,
                    "role": role.group(1) if role else None})
    return out


def superseded(text):
    return set(re.findall(r'\(supersedes-expr \. "((?:[^"\\]|\\.)*)"\)', text))


def top_level_groups(s):
    groups, depth, start = [], 0, None
    for j, ch in enumerate(s):
        if ch == "(":
            if depth == 0:
                start = j
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                groups.append(s[start:j + 1])
    return groups


def cond_clauses(expr):
    """expr = '(cond ...)' or '(за-умовою ...)'; return its top-level clauses."""
    body = expr[expr.find(" ") + 1:]
    if body.endswith(")"):
        body = body[:-1]              # drop exactly the outer form's closing paren
    return top_level_groups(body)


def clause_elems(clause):
    inner = clause[1:-1]
    toks, depth, buf = [], 0, ""
    for ch in inner:
        if ch == "(":
            if depth == 0 and buf.strip():
                toks.append(buf.strip()); buf = ""
            depth += 1; buf += ch
        elif ch == ")":
            depth -= 1; buf += ch
            if depth == 0:
                toks.append(buf); buf = ""
        elif depth == 0 and ch.isspace():
            if buf.strip():
                toks.append(buf.strip()); buf = ""
        else:
            buf += ch
    if buf.strip():
        toks.append(buf.strip())
    return toks


def test_head(clause):
    inner = clause[1:-1].lstrip()
    m = re.match(r"(t|\(\)|-?\d+(?:\.\d+)?)(?=[\s)]|$)", inner)
    return m.group(1) if m else None


def main():
    text = FIX.read_text(encoding="utf-8")
    sup = superseded(OVL.read_text(encoding="utf-8"))
    offenders, scanned, skipped = [], 0, []
    for r in rows(text):
        if r["tier"] != 1 or r["role"] != "constitutive":
            continue
        e = r["expr"]
        if not (e.startswith("(cond ") or e.startswith("(за-умовою ")):
            continue
        scanned += 1
        if e in sup:
            skipped.append(e)
            continue
        cl = cond_clauses(e)
        why = []
        if len(cl) == 0:
            why.append("empty-COND (no clauses)")
        for c in cl:
            if len(clause_elems(c)) != 2:
                why.append(f"clause-shape={len(clause_elems(c))} elements (must be test+expression)")
            th = test_head(c)
            if th == "t":
                why.append("bare-T-truthiness")
            if th and re.fullmatch(r"-?\d+(\.\d+)?", th):
                why.append("numeric-truthiness")
        if why:
            offenders.append((e, sorted(set(why))))
    print(f"scanned {scanned} tier-1 constitutive COND rows; "
          f"overlay supersedes {len(sup)} expr(s) ({len(skipped)} of them COND)")
    if offenders:
        print("FAIL (fail-closed): current tier-1 denominator carries generic truthiness:")
        for e, why in offenders:
            print("  -", e, "->", ", ".join(why))
        return 1
    print("OK: no generic truthiness in the current tier-1 constitutive COND denominator")
    return 0


sys.exit(main())
