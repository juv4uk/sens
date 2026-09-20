# Island Compatibility Language Contract (#749)

See Ukrainian sibling specification: [ISLAND-COMPATIBILITY-LANGUAGE-CONTRACT-749.uk.md](ISLAND-COMPATIBILITY-LANGUAGE-CONTRACT-749.uk.md).

## 1. Purpose

`my-lisp` owns its language semantics and coordinates autonomous execution islands:

- **Common Lisp** — native Lisp execution/runtime;
- **Prolog** — unification, search and backtracking;
- **Datalog** — relational closure/fixpoint;
- **CLIPS** — production rules, working memory and agenda.

Compatibility must not require any island to adopt another island's internal ontology.

## 2. Authority boundary

```text
SID -> my-lisp semantic identity
identity -> zero / one / many execution witnesses
kernel call -> native/opaque island observation
explicit bridge/projection -> ordinary my-lisp data when justified
```

The SID registry and Lisp-owned laws define what a my-lisp identity means. A kernel may execute, observe or witness an identity; it does not acquire authority to redefine it.

Removing, replacing or failing a kernel does not renumber or reinterpret the SID registry.

## 3. Mechanical call boundary

The common boundary is deliberately smaller than a common result model:

```text
target kernel
+ opaque SID
+ kernel-local payload
+ provenance
        |
        v
native / opaque kernel observation
+ producer identity
+ preserved provenance
```

The shared C ABI transports bytes and identity. It does **not** define a universal `island-result`, truth type, proof type, substitution type, tuple type or working-memory type.

Examples remain native:

```text
Common Lisp -> Lisp value / runtime observation
Prolog      -> zero or more substitutions / search observations
Datalog     -> relation tuples / closure observations
CLIPS       -> facts / agenda firings / working-memory observations
```

An explicit bridge may project one native result into ordinary my-lisp data, but the projection is a separate operation and must retain enough producer/provenance information to remain auditable.

## 4. Multiplicity is not truth

When an island protocol exposes result cardinality, `0`, `1` and `N` are observations about that completed call.

They are **not** a universal truth algebra.

In particular:

- zero Prolog substitutions means that invocation produced zero substitutions;
- an empty Datalog relation means that relation observation contains zero tuples;
- zero CLIPS firings means that run fired zero rules;
- a Common Lisp call may legitimately return the Lisp value `()`.

None of those facts, by itself, authorizes my-lisp to conclude `FALSE`, refutation, unknown, conflict, or negation-as-failure.

Literal `()` remains canon() in the language and must not be silently reused as a protocol-level "zero results" sentinel.

## 5. 0 / 1 / N paths

The outer compatibility requirement is only that my-lisp can preserve these cases without collapse:

```text
0 results -> explicit observation: producer + cardinality/native payload
1 result  -> explicit observation: producer + one native result
N results -> explicit observation: producer + native multiplicity
```

The concrete representation may differ by island. A Prolog substitution stream, Datalog tuple set and CLIPS agenda delta do not need to be wrapped into one invented semantic datatype merely because all three have cardinality.

## 6. Cross-island flow

Cross-island communication is explicit and partial:

```text
Island A native result
        |
        v
my-lisp observes producer + provenance + native result
        |
        +-- explicit projection/bridge exists --> Island B input
        |
        `-- no justified bridge -------------> preserve result; stop there
```

A missing bridge is legal. It is better to preserve an untranslated native result than to invent semantic equivalence.

Pairwise bridges are preferred when correspondence is known. No universal interchange semantics is assumed.

## 7. What this contract forbids

- kernel-owned SID meaning;
- SID renumbering when a kernel changes;
- a mandatory universal result ontology;
- automatic native-result -> truth coercion;
- treating zero answers as refutation;
- treating literal `()` as protocol no-result;
- claiming semantic equivalence merely because two islands can exchange bytes.

## 8. Current evidence

The Lisp-owned authority is `contracts/island-compat-contract.lisp`, executed by `tests/fixtures/island-compat-witness.lisp`.

The existing kernel C ABI, kernel host and per-kernel integration tests remain **mechanical witnesses**. They demonstrate transport/execution; they do not define the semantics above.

The next acceptance work for #749 should demonstrate real 0/1/N paths and an explicit cross-island bridge while preserving each producer's native result domain.
