# Semantic Ownership Audit: Classifying Authority, Witness, Adapter, and Execution Mechanism (#733)

**Status:** Proposed / Complete under #733
**Date:** 2026-09-19
**Parent:** #726
**Related:** #730, #734, #746, #748, #749, COMMON-LISP-KERNEL-1

Ukrainian counterpart: [SEMANTIC-OWNERSHIP-AUDIT-733.uk.md](SEMANTIC-OWNERSHIP-AUDIT-733.uk.md)
Machine-readable Lisp inventory: [`contracts/semantic-ownership-audit-733.lisp`](../../contracts/semantic-ownership-audit-733.lisp)

---

## 1. Objective and Mental Model

Before `my-lisp` can be simplified around a minimal, honest semantic coordination core (#726, #746), we must perform an unyielding audit of ownership across the codebase.

The foundational principle of this audit is the **Critical Distinction**:

> **Does this component define WHAT THE LANGUAGE MEANS, or only HOW AN IMPLEMENTATION EXECUTES IT?**

No component is classified by historical location or file naming alone. A `.lisp` file that implements an experimental inference algorithm may be a historical execution mechanism, while a `.rs` table mapping immutable SIDs to evaluator constructs acts as a witness of canonical meaning.

```text
+------------------------------------------------------------------------+
|                          WHAT THE LANGUAGE MEANS                       |
|   (Semantic Authority: Canon 0, McCarthy 7, SID Registry, Laws)        |
+------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------+
|                    HOW IT IS WITNESSED IN LISP DATA                    |
|   (Semantic Witnesses: Invariant Checkers, Conformance Corpora)        |
+------------------------------------------------------------------------+
                                    |
         +--------------------------+--------------------------+
         |                                                     |
         v                                                     v
+-----------------------------------+ +----------------------------------+
|    HOW THE SUBSTRATE EXECUTES     | |     HOW WE TALK TO ISLANDS       |
|    (Execution Mechanism)          | |     (Kernel Adapters)            |
|    - Rust parser, Bignum, VM      | |     - C-ABI vtables              |
|    - Closures, Env, Allocations   | |     - Prolog, Datalog, CLIPS, CL |
+-----------------------------------+ +----------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------+
|                   CANDIDATES FOR DEMOTION OR DELETION                  |
|    (Historical Experiments / In-Lisp Engines / Domain Subsystems)      |
|    - lib/reason.lisp, lib/forward.lisp, lib/knowledge.lisp, yantra.lisp|
+------------------------------------------------------------------------+
```

---

## 2. Classification Taxonomy

1. **`semantic-authority`**: Defines the inviolable meaning of the language (Canons, laws, identity registries, core derivation semantics).
2. **`semantic-witness`**: Pure Lisp data or runner that observes and verifies that language laws hold without relying on host-coded expectations.
3. **`compatibility-reference`**: External standards or surface synonym references (e.g., ANSI Common Lisp, Ukrainian surface profiles).
4. **`execution-mechanism`**: Concrete host substrate implementation (Rust runtime, bignum, memory layouts, parsers, evaluators).
5. **`kernel-adapter`**: Mechanical foreign calling boundary / C-ABI bridge to autonomous execution islands.
6. **`historical-experiment`**: Monolithic in-Lisp engine or complex subsystem candidate for demotion to an optional package, delegation to an island, or retirement.
7. **`unknown` (ambiguous)**: Boundary element requiring an explicit empirical experiment before moving.

---

## 3. Audit of Priority Areas

### 3.1 Parser & Reader
- **Files:** `crates/my-lisp/src/parser.rs`
- **Classification:** `execution-mechanism`
- **Rationale:** The concrete recursive-descent parser, token cursors, and span tracking are pure host execution mechanics. The grammatical laws of S-expressions belong to semantic authority, but this Rust implementation is an execution mechanism.

### 3.2 Evaluator & Trampoline Loop
- **Files:** `crates/my-lisp/src/eval/mod.rs`, `crates/my-lisp/src/eval/builtins.rs`
- **Classification:** `execution-mechanism`
- **Rationale:** Tail-call trampolining, Rust stack frames, evaluation step control, and error unwinding are substrate mechanics.

### 3.3 Closures & Environment Machinery
- **Files:** `crates/my-lisp/src/environment.rs`, `crates/my-lisp/src/eval/closures.rs`
- **Classification:** `execution-mechanism`
- **Rationale:** `Rc<RefCell<Frame>>` hash maps, iterative drop worklists, and parameter destructuring represent the physical execution model.

### 3.4 Runtime Value Representation & Allocation
- **Files:** `crates/my-lisp/src/value.rs`, `crates/my-lisp/src/layout.rs`, `crates/my-lisp/src/ir.rs`
- **Classification:** `execution-mechanism`
- **Rationale:** Physical enum tags, pointer representation, alignment, and intermediate bytecode instructions belong to substrate execution.

### 3.5 Arithmetic Implementation & Bignum
- **Files:** `crates/my-lisp/src/bignum.rs`, `crates/my-lisp/src/eval/arithmetic.rs`
- **Classification:** `execution-mechanism`
- **Rationale:** Arbitrary-precision integer algorithms, Karatsuba multiplication, and rational reduction are host execution algorithms.

### 3.6 Standard List, Vector, and Map Implementation
- **Files:** `lib/core.lisp` (`list`, `append`, `reverse`, `nth`), `lib/persistent-map.lisp`, `lib/persistent-vector.lisp`
- **Classification:**
  - `lib/core.lisp`: `semantic-authority` (canonical derived semantics in Lisp).
  - `lib/persistent-map.lisp`: `historical-experiment` (AVL tree map, demote to optional package).
  - `lib/persistent-vector.lisp`: `historical-experiment` (32-way trie, demote to optional package).

### 3.7 Native Execution & Lowering Hooks
- **Files:** `crates/my-lisp/src/eval/special_forms/` (`io.rs`, `json.rs`, `digest.rs`, `codepoint.rs`)
- **Classification:** `execution-mechanism`
- **Rationale:** OS filesystem access, JSON wire decoding, SHA-256 calculation, and UTF-8 codepoint conversion.

### 3.8 Backward-Chaining Inference (`lib/reason.lisp`)
- **Files:** `lib/reason.lisp`
- **Classification:** `historical-experiment`
- **Rationale:** An in-Lisp backward-chaining Prolog-like engine with indexing. In the archipelago architecture, backward resolution is delegated to the autonomous Prolog island (`wsm-prolog-kernel`). Demote `lib/reason.lisp` to an optional reasoning package.

### 3.9 Forward-Chaining Rule Engine (`lib/forward.lisp` & `lib/clips-import.lisp`)
- **Files:** `lib/forward.lisp`, `lib/clips-import.lisp`
- **Classification:** `historical-experiment`
- **Rationale:** An in-Lisp CLIPS-style RETE forward-chaining rule engine and working memory. Production rules are now delegated to the autonomous CLIPS island (`wsm-clips-kernel`). Demote to an optional package or retire.

### 3.10 Unification Helpers (`lib/unify.lisp`, `lib/unify-observe.lisp`)
- **Files:** `lib/unify.lisp`
- **Classification:** `historical-experiment`
- **Rationale:** Robinson first-order unification with occurs check in Lisp. First-order unification belongs to the Prolog/Datalog islands. Retain `lib/unify-observe.lisp` as a witness if needed, and demote `unify.lisp` to an optional package.

### 3.11 Relational Closure & Datalog Helpers
- **Files:** Relational queries in `lib/knowledge.lisp`, `crates/wsm-datalog-kernel`
- **Classification:**
  - `crates/wsm-datalog-kernel`: `kernel-adapter`
  - In-Lisp deductive closure helpers: `historical-experiment` (delegate to Datalog island).

### 3.12 Semantic Registry & Canon Laws
- **Files:** `lib/canon.lisp`, `lib/surface/semantic-registry.lisp`, `crates/my-lisp/src/eval/canon.rs`
- **Classification:** `semantic-authority`
- **Rationale:** Canon 0 `()`, McCarthy 7 axioms, and the contiguous 8-bit SID registry constitute the immutable foundation of `my-lisp`.

### 3.13 Surface Mappings
- **Files:** `lib/surface/uk.lisp`, `lib/surface/sa.lisp`, `lib/surface/український-профіль-джерела.lisp`
- **Classification:** `compatibility-reference`
- **Rationale:** Linguistic surface synonyms that map human spellings to the canonical 8-bit SIDs.

### 3.14 Semantic Graph Experiments
- **Files:** `experiments/ground-graph.lisp`, `lib/surface/semantic-registry-experiment.lisp`
- **Classification:** `historical-experiment`
- **Rationale:** Research indexing of ternary semantic relationships `(endpoint relation endpoint)`. Demote to research packages.

---

## 4. Comprehensive Inventory Summary

| Category | Count | Representative Items |
| :--- | :---: | :--- |
| **`semantic-authority`** | **10** | `lib/canon.lisp`, `lib/surface/semantic-registry.lisp`, `contracts/answer-contract.lisp`, `contracts/island-compat-contract.lisp`, `lib/core.lisp`, `contracts/exact-q-binary-contract.lisp`, `contracts/structural-observation-contract.lisp`, `lib/macro.lisp`, `lib/result-status.lisp`, `crates/my-lisp/src/eval/canon.rs` |
| **`semantic-witness`** | **6** | `tests/fixtures/island-compat-witness.lisp`, `tests/fixtures/answer-contract-witness.lisp`, `tests/fixtures/conformance.lisp`, `tests/fixtures/canon-laws-v2-witness.lisp`, `lib/meta-eval.lisp`, `lib/surface/peer-identity-acceptance.lisp` |
| **`execution-mechanism`** | **12** | `parser.rs`, `eval/mod.rs`, `environment.rs`, `value.rs`, `bignum.rs`, `arithmetic.rs`, `closures.rs`, `special_forms/io.rs`, `special_forms/json.rs`, `ir.rs`, `layout.rs`, `wsm-kernel-host` |
| **`kernel-adapter`** | **5** | `wsm-kernel-c-abi`, `wsm-prolog-kernel`, `wsm-datalog-kernel`, `wsm-clips-kernel`, `wsm-common-lisp-kernel` |
| **`compatibility-reference`**| **4** | ANSI Common Lisp conformance test suite, `lib/surface/uk.lisp`, `lib/surface/sa.lisp`, legacy `lib/core.lisp.fasl` (current bootstrap is `lib/core4.lisp.fasl`) |
| **`historical-experiment`** | **10** | `lib/reason.lisp`, `lib/forward.lisp`, `lib/clips-import.lisp`, `lib/unify.lisp`, `lib/knowledge.lisp`, `lib/world.lisp`, `lib/yantra.lisp`, `lib/persistent-map.lisp`, `lib/persistent-vector.lisp`, `experiments/ground-graph.lisp` |
| **`unknown` (ambiguous)** | **6** | `lib/si.lisp`, `lib/quantity.lisp`, `lib/time.lisp`, `lib/translation.lisp`, `lib/content-store.lisp`, `lib/tcp.lisp` |

Total Audited Entities: **53**

---

## 5. Ambiguous Items & Required Experiments

The audit identifies 6 components whose classification is genuinely ambiguous and must not be moved or deleted without empirical experiments:

1. **`lib/si.lisp` & `lib/si-derived.lisp` (Physical Dimensions)**:
   - *Ambiguity:* Is physical dimension checking a core semantic typing law of `my-lisp`, or an optional domain package?
   - *Required Experiment:* Build a standalone `packages/si-units` slice and verify if core evaluator/stdlib requires any SI knowledge to function.
2. **`lib/quantity.lisp` (Exact Quantities with Units)**:
   - *Ambiguity:* How tightly coupled is `quantity` to exact rational arithmetic?
   - *Required Experiment:* Test whether quantities can be implemented purely as tagged pairs over standard `Rational` arithmetic in user-space.
3. **`lib/time.lisp` (Calendar Arithmetic Without Clock)**:
   - *Ambiguity:* Does Gregorian calendar arithmetic belong in the core stdlib, or should it be delegated to Common Lisp island's extensive time libraries?
   - *Required Experiment:* Compare performance, footprint, and portability of `lib/time.lisp` against a Common Lisp island bridge.
4. **`lib/translation.lisp` & `lib/narrate.lisp` (Surface Translation)**:
   - *Ambiguity:* Is translation between human surfaces a language coordinator function or a linguistic utility?
   - *Required Experiment:* Measure whether the coordinator can rely strictly on 8-bit SIDs while translating surfaces only at the outer REPL/display boundary.
5. **`lib/content-store.lisp` & `lib/lisp-fs.lisp` (Content-Addressed Storage)**:
   - *Ambiguity:* Should immutable CAS be a host capability primitive or a pure Lisp structural data store?
   - *Required Experiment:* Benchmark SHA-256 CAS persistence in host Rust versus S-expression CAS in pure Lisp.
6. **`lib/tcp.lisp` & `lib/process.lisp` (Host Capability Wrappers)**:
   - *Ambiguity:* Where does the exact capability boundary lie between coordination language code and the host security sandbox?
   - *Required Experiment:* Test capability scoping and sandbox deny-lists under constrained execution.

---

## 6. Next Steps for Core Simplification (#726, #748, #747)

With this audit established in machine-readable Lisp data:
1. **Demote Pyramidal Logic (#748):** Isolate `lib/reason.lisp` and `lib/forward.lisp` into optional packages; route queries to `wsm-prolog-kernel` and `wsm-clips-kernel`.
2. **Free Primitive Budget (#747):** Verify that the 10 `semantic-authority` items form a closed, sufficient core without requiring bloated Rust builtins.
3. **Slim Core Repository (#726):** Safely prune or demote the 10 identified `historical-experiment` files without risking semantic drift or breakage.
