# Architecture Inventory: Small Honest Core & Kernel Archipelago (#746)

**Status:** Accepted under #746
**Date:** 2026-09-19
**Parents:** #695, #730, ADR-005
**Related:** #223, #225, #685, #701, #712, #713, #714, #715, #725

Ukrainian counterpart: [LANGUAGE-SIMPLIFY-CORE-INVENTORY-746.uk.md](LANGUAGE-SIMPLIFY-CORE-INVENTORY-746.uk.md)

---

## 1. Principle

Following the archipelago transition, `my-lisp` transitions from a monolithic engine to a small, honest semantic and coordination language:

```text
my-lisp = small honest semantic and coordination language
kernels = autonomous islands of native execution and reasoning
```

`my-lisp` no longer attempts to be a monolithic omnibus engine embedding:
- Prolog's SLD resolution and backtracking engine;
- Datalog's relational deductive closure and fixpoint computation;
- CLIPS's RETE production system, agenda, and working memory;
- Common Lisp's extensive ANSI runtime and compiler environment.

Instead, `my-lisp` focuses on its primary responsibilities:
1. **canon() (`()`)** as absence-ground and list terminator;
2. **Contiguous 8-bit Semantic ID (SID) registry** (`00000001..10101000`);
3. **Classical Lisp data structure operations** (`cons`, `car`, `cdr`, `atom`, `eq`);
4. **Honest local evaluation** of expressions and first-class lexical functions (`lambda`);
5. **Mechanical dispatch and coordination** of requests to autonomous islands via opaque bytes (C-ABI / KernelHost / KernelRouter);
6. **Preservation of native island results side-by-side** without collapsing them into an artificial universal ontology.

---

## 2. Capability Inventory

Inventory categories:
- **`KEEP`**: Retained in canonical `my-lisp` core as primary semantic responsibility.
- **`DERIVE`**: Derived in Lisp on top of primitives without expanding core evaluator.
- **`ROUTE-TO-KERNEL`**: Delegated to the corresponding autonomous island; duplicated core logic retired.
- **`EXPERIMENTAL`**: Research structures (multi-valued projections, cross-island consensus).

| Component / Operation | Category | Description | Target Island / Location |
| :--- | :--- | :--- | :--- |
| **canon() `()`** | `KEEP` | Ground absence point, empty list, neutral sentinel | `my-lisp` canon |
| **8-bit SID Registry** | `KEEP` | 168 contiguous byte semantic identities (`00000001..10101000`) | `semantic_registry.rs` |
| **McCarthy-7 Primitives** | `KEEP` | `quote`, `atom`, `eq`, `car`, `cdr`, `cons`, `cond` | `my-lisp` core |
| **Functions & Closures** | `KEEP` | `lambda`, lexical environments, parameter bindings | `environment.rs`, `closures.rs` |
| **Exact Arithmetic** | `KEEP` | Reduced rationals and arbitrary-precision integers | `bignum.rs`, `arithmetic.rs` |
| **Symbols & Strings** | `KEEP` | Immutable symbols, UTF-8 strings, reader, printer | `parser.rs`, `presentation.rs` |
| **Host Capabilities** | `KEEP` | OS interaction boundary (`load`, `read-file`, `kernel-exchange`) | `my-lisp-host`, `wsm-kernel-host` |
| **List Helpers** | `DERIVE` | `cadr`, `caddr`, `list`, `append`, `reverse`, `length` | `lib/core.lisp` |
| **Boolean Combinators** | `DERIVE` | `not`, `and`, `or` over explicit condition forms | `lib/core.lisp` |
| **Higher-Order Functions** | `DERIVE` | `map`, `filter`, `fold-left`, `fold-right` over `lambda` | `lib/core.lisp` |
| **Syntactic Sugar** | `DERIVE` | `let`, `let*`, `begin`/`progn` via `lambda` expansion | `lib/macro.lisp` |
| **Unification & SLD Search** | `ROUTE-TO-KERNEL` | Backtracking, substitutions, 0..N alternative answers | **Prolog Island** (`wsm-prolog-kernel`) |
| **Relational Closure** | `ROUTE-TO-KERNEL` | Deductive fixpoint rules, stratified negation | **Datalog Island** (`wsm-datalog-kernel`) |
| **RETE Production Rules** | `ROUTE-TO-KERNEL` | Fact working memory, rule activation agenda | **CLIPS Island** (`wsm-clips-kernel`) |
| **ANSI CL Environment** | `ROUTE-TO-KERNEL` | Full Common Lisp macros, CLOS, specialized runtime | **Common Lisp Island** (`wsm-common-lisp-kernel`) |
| **Pyramidal Logic** | `EXPERIMENTAL` | Demoted from mandatory foundation to optional evidence projection | Optional projection layer (#748) |
| **Multi-Valued Logic (FOUR)** | `EXPERIMENTAL` | Belnap-Dunn 4-valued bilattice over conflicting island evidence | Bilattice/FOUR projection (#219) |
| **Inter-Island Consensus** | `EXPERIMENTAL` | Multi-kernel quorum and consensus protocols | Quorum/evidence protocols (#702, #703, #705) |

---

## 3. Code Deduplication

1. **`lib/unify.lisp` and `lib/forward.lisp`:**
   - Historical monolithic Lisp prototypes of Prolog and CLIPS are no longer canonical execution authorities.
   - They remain as historical observer artifacts only.
   - Autonomous islands `wsm-prolog-kernel` and `wsm-clips-kernel` own execution authority.
2. **`lib/reason.lisp` (Pyramidal Logic):**
   - The requirement that all reasoning results pass through a multi-tier pyramidal lattice is revoked.
   - Exact mathematics remains exact mathematics (#225).
   - Logic queries route directly to Prolog or Datalog.

---

## 4. Execution Witness: Language-Level Orchestration (#746.5)

Acceptance criterion 5 requires:
> "Demonstrate one program that mixes local Lisp evaluation with at least two island calls."

This is verified by the executable witness:
[`crates/wsm-kernel-host/tests/language_simplify_island_orchestration.rs`](file:///home/agents/GitHub/my-lisp/crates/wsm-kernel-host/tests/language_simplify_island_orchestration.rs)

Program in `my-lisp`:
```lisp
(define pair (lambda (a b) (cons a b)))

(define orchestrate-inquiry
  (lambda (entity)
    ((lambda (req)
       ((lambda (datalog-facts)
          ((lambda (prolog-proof)
             (pair (pair "request" req)
                   (pair (pair "datalog-evidence" datalog-facts)
                         (pair (pair "prolog-evidence" prolog-proof)
                               ()))))
           (island-exchange "prolog" entity)))
        (island-exchange "datalog" entity)))
     (pair "query-target" entity))))

(orchestrate-inquiry "person(alice)")
```

### What this witness proves:
1. **Local Lisp evaluation:** Constructing pairs (`pair`/`cons`), variable binding via pure `lambda`, manipulating data structures without kernel involvement.
2. **Two island calls:** Dispatches to **Datalog** (deductive relational closure) and **Prolog** (unification substitutions) through the mechanical `island-exchange` boundary.
3. **Honest composition:** Native results remain opaque strings/bytes and are composed into a plain Lisp list without artificial domain collapse.
4. **Authority integrity:** Zero semantic authority moved into Rust or the kernels. Rust manages only mechanical lifecycle (`KernelHost`/`KernelRouter`) and byte transport.

---

## 5. Verification Evidence

- `cargo test -p wsm-kernel-host` — 4/4 PASS (including `language_simplify_island_orchestration`).
- `cargo test -p my-lisp --test authority_guard_contract` — 3/3 PASS.
- `cargo test -p xtask --test license_policy` — 3/3 PASS.
- `tests/authority-inventory.tsv` & `tests/authority-inventory.lisp` — recorded as `observer`.
