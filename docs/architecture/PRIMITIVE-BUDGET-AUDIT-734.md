# Primitive Budget Audit: 197 Experimental IDs under the 256-ID Constraint (#734)

**Status:** Proposed / Complete under #734
**Date:** 2026-09-19
**Parents:** #730, #726
**Related:** #728, #733, #746, #748, COMMON-LISP-KERNEL-1

Ukrainian counterpart: [PRIMITIVE-BUDGET-AUDIT-734.uk.md](PRIMITIVE-BUDGET-AUDIT-734.uk.md)
Machine-readable Lisp inventory: [`contracts/primitive-budget-audit-734.lisp`](../../contracts/primitive-budget-audit-734.lisp)
Executable genealogy experiments: [`experiments/function-genealogy.lisp`](../../experiments/function-genealogy.lisp)

---

## 1. Context and the Hard 256-ID Budget

In the new four-kernel archipelago architecture (Common Lisp, Prolog, CLIPS, Datalog), `my-lisp` is no longer the monolithic omnibus runtime. Common Lisp is the Lisp execution kernel (#732), Prolog handles backward-chaining resolution, Datalog manages relational deductive closure, and CLIPS owns RETE production rules.

Consequently, `my-lisp`'s role is strictly that of a **small, honest semantic coordination language**.

The central architectural constraint is the **Single 8-Bit Semantic ID (SID) Budget**:
```text
00000000 .. 11111111
= exactly 256 total primitive identity slots
```

### Core Principles
1. **Intentional Scarcity:** No widening to 16 bits or private per-kernel ID spaces. Scarcity forces us to discover genuinely foundational, compositional primitives rather than copying each island's internal vocabulary into the core.
2. **Earned Admission:** An operation earns an 8-bit primitive identity only if it enables an externally observable operation that cannot be composed or represented as ordinary data.
3. **Measurement Baseline:** The current 197 allocated identities (168 in the core registry + 29 archipelago interaction primitives) form a measurement baseline, leaving 59 unallocated slots ($256 - 197 = 59$).

---

## 2. Classification of the 197 Experimental IDs

Every single one of the 197 experimental identities is accounted for and classified in [`contracts/primitive-budget-audit-734.lisp`](../../contracts/primitive-budget-audit-734.lisp):

| Category | Count | Description & Representative Entries |
| :--- | :---: | :--- |
| **`primitive-essential`** | **37** | Foundational operations: Canon 0 `()`, McCarthy 7 (`quote`, `atom`, `eq`, `cons`, `car`, `cdr`, `cond`), evaluator binders (`lambda`, `define`, `defmacro`), exact arithmetic (`+`, `-`, `*`, `/`, `mod`, `quotient`), order/equality (`<`, `=`), predicates (`symbol?`, `string?`, `string<?`), core strings, vectors, `read`, `eval`. |
| **`primitive-shared`** | **25** | Cross-kernel operational primitives: `kernel`, `callable`, `request`, `response`, `source`, `target`, `payload`, `invoke`, `observe`, `route`, `relation`, `bridge`, `transport`, `result`, `status`, `start`, `stop`, `restart`, `snapshot`, `measure`, `producer`, `owns-callable`, `can-call`, `can-observe`, `has-transport`. |
| **`derived-operation`** | **60** | Derivable in pure Lisp on top of primitives: `second`, `third`, `fourth`, `fifth`, `caar`, `cadr`, `cddr`, `cadddr`, `list`, `not`, `and`, `or`, `let`, `let*`, `min-list`, `max-list`, `abs`, `min`, `max`, `isqrt`, `map`, `filter`, `reduce`. |
| **`surface-only`** | **1** | Syntactic aliases: `def` (alias for `define`). |
| **`ordinary-data`** | **34** | Concepts that can be ordinary S-expression symbols/data: kernel identifiers (`lisp-kernel`, `prolog-kernel`, `clips-kernel`, `datalog-kernel`), internal unification logic variables, and proof tags. |
| **`runtime-mechanism`** | **19** | Host substrate OS/IO capabilities: `process-run`, `tcp-read`, `tcp-write`, `tcp-listen`, `read-file`, `write-file`, `sha256-hex`, `json-parse`, `vector-set!`, `env`. |
| **`compatibility-only`** | **1** | Historical buffer calculation helper: `largest-chunk`. |
| **`experimental-evidence`** | **20** | Epistemic/evidence structures from early experiments: `evidence?`, `observation?`, `intent?`, `tell`, `retract`. |
| **Total Accounted** | **197** | **Headroom remaining: 59 unallocated slots** |

---

## 3. Reclaim Candidates & Budget Headroom

The audit identifies **109 reclaim candidates** across the 197 baseline IDs:
- **60 derived operations:** Composite accessors, boolean combinators, and list utilities that can be derived in `lib/core.lisp`.
- **34 ordinary data entities:** Subsystem identifiers that can be ordinary quoted symbols rather than reserved 8-bit primitive SIDs.
- **20 experimental evidence structures:** Domain tags from earlier monolithic experiments that belong in user packages or Datalog relations.

By demoting these reclaim candidates from inviolable 8-bit primitive status to ordinary library functions or data, the core coordination language can easily operate with **~60 to 70 essential and shared primitives**, leaving **over 180 slots available** for future cross-island coordination.

---

## 4. Requirement 4: Seemingly Redundant IDs That Must Remain Distinct

The audit establishes that observational equivalence on a subset of data does **not** justify collapsing distinct semantic identities.

### Case Study: `second` (`00101111`, index 47) vs `cadr` (`00110100`, index 52)
In [`experiments/function-genealogy.lisp`](../../experiments/function-genealogy.lisp), the witness evaluates:
```lisp
(sample-equivalent-two-unary? second cadr sample-a sample-b)
  -> (structural-relation same)
```
On proper lists, `(second x)` and `(cadr x)` return identical values. However, they represent two fundamentally distinct ontological categories:
1. **`cadr`** is a **Cartesian pair algebra projection**: it explicitly denotes `(car (cdr x))`. It belongs to the structural pair-navigation family alongside `caar`, `cdar`, `cddr`.
2. **`second`** is a **sequence ordinal accessor**: it denotes the element at index 1 of a linear sequence. It belongs to the collection family alongside `first`, `third`, `fourth`, `fifth`.

Collapsing `cadr` into `second` would corrupt pair algebra and impose sequence semantics onto binary pair structures. Therefore, they **must remain distinct identities**.

Additional examples:
- **`empty-list` `()` (`00000000`) vs `quote` (`00000001`):** `()` is the ground absence object; `quote` is an evaluation control form.
- **`pair` (`00101110`) vs `list` (`00100111`):** `pair` is strictly binary (arity 2); `list` is an open variadic constructor `(lambda args args)`.

---

## 5. Requirement 5: Current IDs That Can Be Demoted from Primitive Status

The audit identifies multiple operations currently occupying 8-bit primitive slots that can be safely demoted without breaking language expressiveness.

### Case Study 1: `fourth` (`00110001`) and `cadddr` (`00110110`)
Executable evidence in [`experiments/function-genealogy.lisp`](../../experiments/function-genealogy.lisp) demonstrates:
```lisp
(def experiment-fourth
  (lambda (values)
    (car (cdr (cdr (cdr values))))))

(def experiment-cadddr
  (lambda (values)
    (car (cdr (cdr (cdr values))))))
```
Both `fourth` and `cadddr` are identical compositions of `car` and `cdr`. They require zero host or substrate support. They can be demoted from 8-bit primitive status to derived functions in `lib/core.lisp`.

### Case Study 2: `min-list` (`00010111`) and `max-list` (`00011000`)
Both operations are composite list reductions:
```lisp
(def min-list (lambda (items) (reduce min items)))
(def max-list (lambda (items) (reduce max items)))
```
Allocating two distinct 8-bit primitive slots for convenience reduction helpers is an unjustified expenditure of the 256-ID budget. Both are demoted to derived library functions.

### Case Study 3: `not` (`00100001`), `and` (`10011010`), `or` (`10011011`)
All three are derived in pure Lisp over `cond`:
- `(not x)` expands to `(cond (x ()) (t t))`.
- `and` and `or` are short-circuiting macros generating nested `cond` forms.
None requires an opaque 8-bit primitive slot in the core coordinator.

---

## 6. Summary of Acceptance Criteria

- [x] **Account for all 197 experimental IDs:** 168 core registry + 29 archipelago IDs fully enumerated in `contracts/primitive-budget-audit-734.lisp`.
- [x] **Identify reclaim candidates with evidence:** 109 reclaim candidates identified and classified with executable rationale.
- [x] **Preserve the <=256 hard budget:** 197 current baseline < 256 (59 unused slots); potential core reduction to ~65 primitives (>180 headroom).
- [x] **Record at least one case where redundant IDs must remain distinct:** Documented `second` vs `cadr`, `()` vs `quote`, and `pair` vs `list`.
- [x] **Record at least one case where an ID can be demoted:** Demonstrated demotion of `fourth`/`cadddr`, `min-list`/`max-list`, and boolean operators.
- [x] **Verified by automated witness test:** `primitive_budget_audit_734_accounts_for_197_ids_under_256_constraint` passing in `crates/my-lisp/tests/witness_authority.rs`.
