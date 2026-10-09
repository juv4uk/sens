# D10 research: Maling's 1959 Lisp differentiation demonstration

**Decision today: HOLD / research only.** This is not a selected D10 resident and has no coordinate or runtime authority.

## Why this is a historical lead

The Computer History Museum's LISP 1.5 archive lists K. Maling's *The LISP Differentiation Demonstration Program* as MIT AI Memo 10, a six-page document grouped with the project's 1959 Lisp memos. It links the scan at [AIM-010](https://bitsavers.org/pdf/mit/ai/aim/AIM-010.pdf). The same archive places the demonstration among the early Lisp documentation, separate from McCarthy's foundational S-expression memo. Archive index: [LISP 1.5 family](https://softwarepreservation.computerhistory.org/LISP/lisp15_family.html); archival finding aid: [Herbert Stoyan collection](https://archive.computerhistory.org/resources/access/text/finding-aids/102703236-Stoyan/102703236-Stoyan.pdf).

**Important source boundary:** the scan is the historical donor; the precise finite contract below is our modern, bounded formalization for review. This dossier does not claim to reproduce every rule or the literal source code in AIM-010.

## Proposed observable law

Given a finite, acyclic symbolic expression over integer constants, named variables, addition and multiplication, plus a target variable, return the **symbolic expression** for its formal derivative. The contract deliberately returns the direct unsimplified tree; it does not claim algebraic simplification, a normal form, numeric evaluation, or finite-difference reconstruction.

```text
Expr ::= Const(integer) | Var(name) | Add(Expr, Expr) | Mul(Expr, Expr)

D(Const(n), x) = Const(0)
D(Var(y), x)   = Const(1) if y = x, else Const(0)
D(Add(a,b), x) = Add(D(a,x), D(b,x))
D(Mul(a,b), x) = Add(Mul(D(a,x), b), Mul(a, D(b,x)))
```

Examples:
- `D(Const(7), x) = Const(0)`
- `D(Var(x), x) = Const(1)`
- `D(Var(y), x) = Const(0)`
- `D(Mul(Var(x), Var(x)), x) = Add(Mul(Const(1), Var(x)), Mul(Var(x), Const(1)))`

The product example is intentionally not simplified to `Add(Var(x), Var(x))`: simplifying the output would be a separate law and must not be smuggled into this one.

## Falsifiers and dedup boundary

A numeric derivative value at one point is not symbolic differentiation. Returning 1 for a non-target variable, using a wrong product rule, mutating the input tree, or silently simplifying/reordering output falsifies this exact contract.

Likely neighboring laws need explicit comparison before any D10 selection:
- the Babbage finite-difference idea reconstructs a polynomial from a finite value sequence; this operation differentiates a symbolic expression;
- Boolean prime implicants are logic minimization, not calculus;
- Pāṇini's staged `DERIVE-VERB-*` family operates on linguistic forms, not polynomial expression trees;
- generic evaluators, map/recursion, and expression operations may make this a derived library function.

That last point is the main unresolved question. Derivability is not automatically exclusion, but this PR does **not** decide Core-versus-library minimality.

## Evidence and gates

The JSON dossier pins the historical source, input/output contract, witnesses, falsifiers, and review limits. The Python oracle generates the symbolic derivative and compares its polynomial meaning with an independently implemented coefficient-map derivative. The SWI-Prolog oracle provides a second executable implementation with its own coefficient algebra. CI must report the real oracle results; no runtime parity in SENS is claimed.

Scope is source/tests/docs/workflow plus exactly one **pending-review** row `D10P-0015` in `knowledge/d10-proposal-ledger.tsv`. No D10 inventory/state, selection history, D1–D9, D2, T5, or executable `.sens` changes. The proposal remains `selected=false`, `coordinate=null`, `ratified=false`, `status=pending-review`; owner/peer review and Core-vs-library minimality remain unresolved.
