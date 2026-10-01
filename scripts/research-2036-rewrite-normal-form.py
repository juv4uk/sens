#!/usr/bin/env python3
"""#2036 research-only typed rewrite/proof-normal-form countermodel.

This deliberately does NOT make binary path/address semantic authority.
It asks whether a small typed normalization calculus can explain the same
selector evidence, preserve refactoring invariance, refuse weak semantic
quotients, and represent recursion without infinite inlining.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Term:
    op: str
    args: tuple["Term | str", ...] = ()
    role: str | None = None


@dataclass(frozen=True)
class Evidence:
    implementation_equal: bool
    semantic_identical: bool


def substitute(term: Term | str, name: str, replacement: Term | str):
    if term == name:
        return replacement
    if isinstance(term, str):
        return term
    return Term(
        term.op,
        tuple(substitute(arg, name, replacement) for arg in term.args),
        term.role,
    )


def normalize(term: Term | str, helpers: dict[str, Term]) -> Term | str:
    if isinstance(term, str):
        return term

    normalized_args = tuple(normalize(arg, helpers) for arg in term.args)

    if term.op in helpers:
        helper = helpers[term.op]
        if len(normalized_args) != 1:
            raise ValueError("bounded helper model supports unary helpers only")
        expanded = substitute(helper, "$0", normalized_args[0])
        return normalize(expanded, helpers)

    # Recursive/SCC references remain finite proof atoms rather than inlining.
    if term.op == "scc-ref":
        return Term("scc-ref", normalized_args, term.role)

    return Term(term.op, normalized_args, term.role)


def size(term: Term | str) -> int:
    if isinstance(term, str):
        return 1
    return 1 + sum(size(arg) for arg in term.args)


def selector_projection(term: Term | str) -> str | None:
    """Optional compact projection after normalization; never identity authority."""
    ops: list[str] = []
    cur = term
    while isinstance(cur, Term) and cur.op in {"car", "cdr"} and len(cur.args) == 1:
        ops.append(cur.op)
        cur = cur.args[0]
    if cur != "x" or not ops:
        return None

    root = "101" if ops[0] == "car" else "110"
    suffix = "".join("0" if op == "car" else "1" for op in ops[1:])
    return root + suffix


def may_semantic_quotient(left: Term, right: Term, evidence: Evidence) -> bool:
    # Same normalized executable term is insufficient by itself.
    return evidence.semantic_identical and left == right


def main() -> None:
    direct = Term("car", (Term("cdr", ("x",)),))

    helpers_a = {"tail": Term("cdr", ("$0",))}
    helpers_b = {"q": Term("cdr", ("$0",))}
    factored_a = Term("car", (Term("tail", ("x",)),))
    factored_b = Term("car", (Term("q", ("x",)),))

    n_direct = normalize(direct, {})
    n_a = normalize(factored_a, helpers_a)
    n_b = normalize(factored_b, helpers_b)

    assert n_direct == n_a == n_b
    assert selector_projection(n_direct) == "1011"

    # Same executable term, but typed semantic evidence does not yet permit collapse.
    second = Term("car", (Term("cdr", ("x",)),), role="sequence-ordinal")
    cadr = Term("car", (Term("cdr", ("x",)),), role="pair-navigation")
    second_exec = Term("car", (Term("cdr", ("x",)),))
    cadr_exec = Term("car", (Term("cdr", ("x",)),))

    weak = Evidence(implementation_equal=True, semantic_identical=False)
    assert normalize(second_exec, {}) == normalize(cadr_exec, {})
    assert not may_semantic_quotient(second, cadr, weak)

    # Direct alias is still not promoted automatically without typed semantic evidence.
    fourth = Term("car", (Term("cdr", (Term("cdr", (Term("cdr", ("x",)),)),)),), role="sequence-ordinal")
    cadddr = Term("car", (Term("cdr", (Term("cdr", (Term("cdr", ("x",)),)),)),), role="pair-navigation")
    assert selector_projection(Term("car", (Term("cdr", (Term("cdr", (Term("cdr", ("x",)),)),)),))) == "101111"
    assert not may_semantic_quotient(fourth, cadddr, weak)

    # Recursive evaluator cluster represented finitely.
    eval_scc = Term("scc-ref", ("eval/apply/evcon/evlis",), role="recursive-proof-cluster")
    wrapped = Term("uses", (eval_scc, "environment"))
    n_wrapped = normalize(wrapped, {})
    assert isinstance(n_wrapped, Term)
    assert "scc-ref" in repr(n_wrapped)

    print("selector-normal-form")
    print(f"direct={n_direct}")
    print(f"helper-a={n_a}")
    print(f"helper-b={n_b}")
    print(f"projection={selector_projection(n_direct)}")
    print(f"normal-form-size={size(n_direct)}")

    print("\nequivalence-guard")
    print("second/cadr executable-normal-form-equal=true")
    print("second/cadr semantic-quotient=false")
    print("fourth/cadddr semantic-quotient=false")

    print("\nrecursion")
    print(f"finite-scc-proof={n_wrapped}")

    print("\nRESULT")
    print("PASS: tiny typed rewrite model explains selector refactoring invariance,")
    print("      keeps weak equivalence from collapsing meaning, and represents SCC recursion finitely.")
    print("STATUS: countermodel remains conjectural; confluence/coverage/cost still unproven.")


if __name__ == "__main__":
    main()
