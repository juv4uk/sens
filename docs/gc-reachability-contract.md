# GC reachability contract

**Status:** CONTRACT PROJECTION · **Authority:** #2544 · **Docs follow-up:** #2547
**Scope:** language/runtime boundary only. Collector implementation remains substrate-private.

## 1. Canonical law

```text
reachable from declared roots -> survives
unreachable managed object   -> may become reusable storage
collector choice             -> must not change semantic result
```

Garbage collection is a **mechanism**, not SENS semantics.

A semantic operation must not be able to distinguish:

- whether a collection occurred;
- when it occurred;
- how often it occurred;
- whether mark-sweep, copying, arenas, host ownership, or another admitted
  mechanism reclaimed storage.

Engineering telemetry may exist, but only out of band from semantic
observation and conformance.

## 2. Hard exclusions

The language contract does not admit:

- weak references;
- finalizers;
- resurrection of unreachable values;
- a semantic `gc-journal`, `gc-stats`, `gc-promote`, collection counter,
  pause clock, mark bit, heap slot, address, generation, forwarding address, or
  free-list link;
- semantic identity derived from collector/storage metadata.

Explicit resource lifetime belongs to explicit capabilities/lifecycle APIs, not
to finalization.

## 3. Root law

A collector may reclaim a managed object only after an exact root traversal
proves it unreachable.

Every runtime/substrate must define its root categories mechanically. Typical
categories may include active environments, evaluation temporaries, explicit
handles, globals, stacks, registers, or static runtime tables, but no category
is ratified merely by analogy with a historical implementation.

If a substrate declares an immortal/static basis, it is outside reclamation by
that substrate's collector. Immortality is a representation contract, not a
semantic property of the binary identity itself.

## 4. Child-trace law

Every **landed managed object representation** must provide an exact child-edge
visitor. #2548 owns the representation census.

Current design candidates already documented in this repository include Pair,
Closure/Lambda, Environment and Vector.

Do not pre-ratify edges for representations that are not yet landed:

- managed Rational/exact-Q and any bignum/limb chain;
- Text7/string backing;
- Map or other aggregate types.

When such a representation lands, its complete edge law must be added with an
executable falsifier before the collector may reclaim it.

## 5. Safe points

Collection may run only where the implementation can prove the root set
complete.

Allocation failure/threshold is a valid first candidate because Lisp 1.5 used
free-storage exhaustion as a collection trigger, but modern SENS safe points
must be proved from the current evaluator/compiler/runtime, not inherited from
history.

## 6. Historical donors

### LISP 1.5 / McCarthy lineage

The LISP 1.5 Programmer's Manual describes:

1. active list structure reachable from fixed base registers;
2. marking reachable car/cdr chains;
3. a linear sweep of free storage;
4. rebuilding the free-storage list from unmarked cells.

Primary manual:
https://www.softwarepreservation.org/projects/LISP/book/LISP%201.5%20Programmers%20Manual-1961.07.14.pdf

SENS adopts the **reachability/reclamation law**, not sign-bit marking, machine
register layout, word format, or the historical root inventory.

### Cheney 1970

C. J. Cheney, *A Nonrecursive List Compacting Algorithm*, Communications of the
ACM 13(11), 677–678 (1970), DOI 10.1145/362790.362798.

This is a copying/compacting mechanism donor only. Substrate choice is owned by #2544 and its active mechanism lanes (`wsm-os-lisp#60`, `fpga-lisp#49`); copying must beat alternatives on measured memory/timing evidence before adoption.

## 7. Required witnesses

#2551 owns the adversarial corpus. At minimum:

- reachable pair graph survives;
- unreachable graph becomes reusable;
- deep graph does not overflow the host marker stack;
- cycles are handled by a tracing collector;
- closure/environment and aggregate edges survive;
- allocation works after reclamation;
- stale/malformed handles fail closed;
- normal and stress-GC executions have the same semantic result;
- swapping collector mechanisms does not change semantics;
- future managed Rational/bignum representations require their own reachable
  long-chain witness before admission.

## 8. Relation to older GC documents

The August 2026 GC documents remain valuable historical/design evidence, but
the following statements are superseded by the #2544 mechanism boundary (documented by #2547):

- "GC is part of machine semantics" as semantic authority;
- `(gc-journal)` as language semantics;
- `(gc-promote ...)` resurrection;
- weak references/finalizers as a future language feature.

Telemetry, quarantine experiments, or owner-facing trust tooling may still
exist as **external engineering instrumentation** provided the running SENS
program cannot observe or branch on them.

## Principle

**GC preserves reachability; it never defines meaning.**
