# LIFE architecture pattern catalog — evidence before mechanism

Issue: #793  
Status: bounded research catalog  
Authority: **research evidence only** — this file does not define my-lisp semantics.

## Non-collapse rule

Two axes remain independent:

```text
execution paradigms: Common Lisp | Prolog | Datalog | CLIPS
my-lisp substrates:  Rust | GraalVM | WASM/C | future FPGA
```

A precedent may suggest a mechanism on either axis. It may not turn one execution
paradigm into the implementation language for the others, and it may not turn one
substrate into semantic authority. SID meaning remains my-lisp-owned.

## Decision vocabulary

- **borrow** — the mechanism can be reused with the same architectural role.
- **adapt** — the mechanism is useful only after tightening ownership/provenance boundaries.
- **reject** — the precedent would collapse native domains or semantic authority.

## Pattern catalog

### 1. Kernel discovery and lifecycle — ADAPT

**External precedent.** MetaCall separates per-language loaders from the core and
gives loaders an initialize/load/clear lifecycle. Its plugin architecture permits
runtime-specific components to be loaded and unloaded independently.

Sources:
- https://core.metacall.io/
- https://github.com/metacall/core-landing-page/blob/master/docs/docs.md

**Current my-lisp evidence.**
- `experiments/metacall-pattern-audit-789.lisp`
- `contracts/life-1-contract.lisp`
- `crates/my-lisp/src/eval/capabilities.rs`

**Adopted rule.** Discover and start a kernel through an explicit mechanical
descriptor/handle. Availability is an observation. It never mints or changes a SID.

**Rejected part.** Do not introduce one universal foreign-value ontology as the
price of lifecycle uniformity.

---

### 2. Invocation boundary — ADAPT

**External precedent.** GraalVM Truffle uses an explicit interoperability protocol
with standardized messages for foreign values. Languages can interoperate through
that protocol without each language implementation directly knowing every other
language.

Sources:
- https://www.graalvm.org/jdk21/reference-manual/espresso/interoperability/
- https://www.graalvm.org/jdk21/graalvm-as-a-platform/language-implementation-framework/

**Current my-lisp evidence.**
- `contracts/island-compat-contract.lisp`
- `tests/fixtures/island-compat-witness.lisp`
- `crates/wsm-kernel-c-abi/`

**Adopted rule.** Borrow the idea of one explicit mechanical invocation protocol,
but keep the payload producer-native and the semantic ID opaque.

**Rejected part.** Interop protocol messages must not become a shared language
semantics or a universal result type.

---

### 3. Native-result references — ADAPT

**External precedent.** OpenCog AtomSpace distinguishes stable/immutable Atom
identity from attached Values used for changing metadata or observations.

Sources:
- https://github.com/opencog/atomspace/blob/master/opencog/README.md
- https://wiki.opencog.org/w/AtomSpace

**Current my-lisp evidence.**
- `crates/wsm-native-result-types/src/lib.rs`
- `experiments/atomspace-pattern-audit-791.lisp`

**Adopted rule.** A stable observation/native-result reference may identify a
producer-owned result without copying or normalizing the payload. Lifecycle,
timestamps, costs, and capability metadata may be attached separately.

**Rejected part.** Do not adopt a central AtomSpace-like knowledge ontology or
universal truth/attention attachment.

---

### 4. Explicit bridge admission — BORROW

**External precedent.** KIF was designed as an interchange language among
heterogeneous knowledge systems rather than as a required internal representation
for every participating system.

Source:
- https://logic.stanford.edu/people/genesereth/papers.html
  (Michael Genesereth, *Knowledge Interchange Format*, 1991)

**Current my-lisp evidence.**
- `contracts/island-compat-contract.lisp`
- `contracts/life-1-contract.lisp`
- `docs/architecture/ISLAND-COMPATIBILITY-LANGUAGE-CONTRACT-749.md`

**Adopted rule.** Bridges are explicit, partial, inspectable conversions. A missing
bridge is legal. Source native results remain available after projection.

**Rejected part.** No interchange form becomes the internal representation of
Common Lisp, Prolog, Datalog, or CLIPS.

---

### 5. Provenance trace — ADAPT

**External precedent.** AtomSpace's separation of stable identity and attached
Values is useful for provenance; KIF demonstrates that interchange records can be
explicit data rather than hidden runtime equivalence.

**Current my-lisp evidence.**
- `contracts/life-1-contract.lisp`
- `crates/wsm-native-result-types/src/lib.rs` (`ObservationRef`,
  `ProvenanceEdge`)

**Adopted rule.** Record `producer → observation → explicit bridge → target
observation` as ordinary provenance data. The bridge reference is opaque to the
storage mechanism.

**Rejected part.** Provenance is not a truth value and cannot retroactively claim
semantic equivalence.

---

### 6. Scheduling and activation — ADAPT

**External precedent.** Hearsay-II/blackboard systems separate knowledge sources,
a shared blackboard data structure, and control; Hearsay-II used opportunistic
scheduling based on blackboard changes.

Sources:
- https://www.cs.cmu.edu/afs/cs/project/tinker-arch/www/html/1998/questions/20.Blackboard.html
- https://www.cs.cmu.edu/~raj-symposium/lesser.html

**Current my-lisp evidence.**
- `experiments/atomspace-pattern-audit-791.lisp`
- `contracts/life-1-contract.lisp`
- kernel-host scheduling/queue mechanisms under `crates/wsm-kernel-host/`

**Adopted rule.** Scheduler priority may use explicit availability, cost, freshness,
or queue metadata to choose *when/where* to execute.

**Rejected part.** A shared blackboard must not become semantic truth authority,
and scheduler priority must not change SID meaning.

---

### 7. Failure isolation — BORROW

**External precedent.** MetaCall's loader/plugin boundaries provide separate
initialization, loading, clearing, and error boundaries for runtimes.

**Current my-lisp evidence.**
- `experiments/metacall-pattern-audit-789.lisp`
- per-kernel tests under `crates/wsm-*-kernel/tests/`
- `contracts/island-compat-contract.lisp`

**Adopted rule.** Kernel startup/transport/native failures stay named at the
mechanical boundary. One island failure does not rewrite another island's result
or the Lisp semantic registry.

**Rejected part.** Do not normalize execution failure into Lisp falsehood, Canon
`()`, or an invented semantic answer.

---

### 8. Missing-kernel behavior — BORROW MECHANISM, REJECT FALLBACK SEMANTICS

**External precedent.** Poplog exposes explicit language subsystems and loaded-state
queries; MetaCall exposes explicit runtime loaders. Both motivate observable runtime
availability.

Current research record:
- `experiments/poplog-pattern-audit-787.lisp`
- `experiments/metacall-pattern-audit-789.lisp`

**Current my-lisp authority/evidence.**
- `contracts/island-compat-contract.lisp`: missing kernel is legal execution availability.
- `contracts/life-1-contract.lisp`: missing source kernel does not change SID meaning.
- Common Lisp kernel tests distinguish missing runtime from semantic result.

**Adopted rule.** `missing-kernel` is execution unavailability, full stop.

**Rejected part.** Never fall back by changing the requested semantic identity,
renumbering the registry, returning Canon 0, or pretending an unavailable producer
returned zero results.

## Cross-pattern invariants

1. **SID is identity; execution mechanisms are evidence/projections.**
2. **Producer-native result domains survive observation.**
3. **Bridge admission is explicit and partial.**
4. **Missing capability is not semantic absence.**
5. **Scheduling metadata is not meaning.**
6. **A substrate may be replaced without changing language semantics.**
7. **No precedent is accepted merely because it is historically successful; every
   borrowed mechanism must preserve the two-axis architecture.**

## Implementation use

Future LIFE-1/LIFE-2 work should cite the relevant pattern above before introducing
a new loader, bridge, scheduler rule, result reference, or failure policy. If a new
mechanism does not fit one of these patterns, record the new evidence and add a
bounded catalog entry rather than silently extending architecture.
