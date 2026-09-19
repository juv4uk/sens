# Island Compatibility Language Contract (#749)

See Ukrainian sibling specification: [ISLAND-COMPATIBILITY-LANGUAGE-CONTRACT-749.uk.md](ISLAND-COMPATIBILITY-LANGUAGE-CONTRACT-749.uk.md).

## 1. Context and Purpose

As defined in ADR-005 and Issue #749 (`[P0][KERNEL-COMPAT-LANGUAGE-1]`), `my-lisp` does not implement monolithic, embedded reasoning engines for every formal discipline. Instead, the language serves as a small, honest semantic and coordination substrate, orchestrating autonomous execution islands:
- **Common Lisp**: ANSI-standard rich symbolic execution runtime.
- **Prolog**: SLD resolution, unification, and depth-first search/backtracking.
- **Datalog**: Monotonic bottom-up fixpoint closure and relational queries.
- **CLIPS**: Production rules and RETE agenda activation.
- **Future Kernels**: Custom specialized domain provers.

A language feature must be evaluated by whether it composes cleanly with these islands without imposing a foreign ontology or collapsing the boundaries between execution models.

## 2. Core Architectural Invariants

### 2.1 The Identity and Execution Model

```text
SID -> identity
identity -> local Lisp meaning and/or execution witnesses
kernel call -> opaque/native result
result -> ordinary my-lisp data or explicit native handle/view
```

1. **Semantic ID (SID) Sovereignty**:
   Semantic IDs belong exclusively to the `my-lisp` continuous 8-bit registry (`00000000..10100111`) and language laws. A kernel never owns or renumbers an SID.
2. **Witness Relationship**:
   A kernel is an execution witness for zero, one, or multiple SIDs. Removal or failure of a kernel does not alter, renumber, or invalidate the `my-lisp` semantic registry.
3. **Ontological Autonomy**:
   No kernel is forced to adopt another kernel's internal result representation. Prolog deals in substitutions and choice points; Datalog deals in ground tuple relations; CLIPS deals in working memory assertions and rule activations; Common Lisp deals in ANSI s-expressions.
4. **Uniform Mechanical Invocation**:
   All communication across the boundary occurs through an opaque mechanical transport (`island-exchange` / `island-call` over byte spans and C-ABI vtables).

## 3. Minimal Language-Facing Call/Result Contract

### 3.1 The Outer Contract

The outer invocation contract is defined as:

```lisp
(island-call target-kernel sid payload-bytes-or-expression [provenance])
  -> (island-result :status <status> :count <n> :items (<item> ...) :raw-payload <bytes>)
```

### 3.2 Answer Multiplicity and Distinguishability

A core design requirement of Issue #749 is handling the spectrum of answer multiplicities and resolving the ambiguity between "no answer" and "an answer that happens to be empty":

1. **0-Answer (Failure / No Result)**:
   - Status: `:none`
   - Count: `0`
   - Items: `()`
   - Representation: `(island-result :status :none :count 0 :items ())`
   - Semantics: The query failed, the goal is unprovable (negation-as-failure), or no matching relation exists.
2. **1-Answer (Deterministic / Single Result)**:
   - Status: `:one`
   - Count: `1`
   - Items: `(value)`
   - Representation: `(island-result :status :one :count 1 :items (value))`
   - **Crucial Invariant**: If the evaluated value is the literal empty list `()`, it is represented as:
     `(island-result :status :one :count 1 :items (()))`
     This distinguishes `0-answers` (`items ()`) from `1-answer of empty list` (`items (())`).
3. **N-Answers (Multi-Solution / Stream / Relational Set)**:
   - Status: `:many`
   - Count: `N`
   - Items: `(sol-1 sol-2 ... sol-N)`
   - Representation: `(island-result :status :many :count N :items (...))`
   - Semantics: Multiple variable bindings from Prolog backtracking, a set of derived tuples from Datalog fixpoint, or multiple rule firings from CLIPS.
4. **Error / Malformed Boundary**:
   - Status: `:error`
   - Representation: `(island-result :status :error :reason "..." :raw-payload ...)`

## 4. Cross-Island Data Flow and Bridges

Islands do not share internal heap structures. When a result flows from Island A to Island B:

```text
[Island A: Datalog]
       |
       | derives reachability tuples
       v
[my-lisp Coordinator]  <-- receives (island-result :status :many :items ((reach a b) (reach b c) (reach a c)))
       |
       | inspects & formats ordinary s-expression data
       v
[Island B: Prolog]     <-- receives axioms + goal query
       |
       | executes SLD resolution with backtracking over Datalog-derived facts
       v
[my-lisp Coordinator]  <-- receives verified path or policy deduction
```

- **Ordinary Data Projection**: S-expressions are the lingua franca of `my-lisp`. Data returned by one kernel is unpacked into ordinary Lisp pairs and symbols, which can be inspected, filtered, or passed into the input of a second kernel.
- **Explicit Handles**: When payload sizes or opaque state require it, native handles are preserved without mutating or flattening internal kernel ontologies.

## 5. Summary of Compliance

- [x] Minimal language-facing kernel call/result contract defined.
- [x] 0-answer, 1-answer, and N-answer paths distinguished deterministically.
- [x] Literal `()` distinguished from no-result.
- [x] Lisp -> Prolog and Lisp -> Datalog demonstrated without embedding their engines in `my-lisp`.
- [x] Cross-island data flow demonstrated through ordinary data composition.
- [x] Semantic authority remains anchored in `my-lisp` registry and laws.
