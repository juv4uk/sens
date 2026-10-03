# #2472 — Phase-D transformation-footprint audit

Status: research-only.

This audit compares the already-merged D1-D4 countermodels by **how much of
the program interface they must rewrite**.

It deliberately does not answer DERIVED-vs-NEW by itself.

## Result

| Operation | Countermodel | Transformation footprint |
|---|---|---|
| GO | finite state + tail recursion | local PROG-region rewrite |
| RETURN | explicit exit continuation | call-chain protocol rewrite |
| SETQ | explicit immutable store | observer/store-graph protocol rewrite |

## GO

The generated driver owns an explicit:

```text
(state remaining acc)
```

and all label transfers become tail calls to that synthetic driver.

The control state can therefore remain inside the transformed PROG region.

This is the strongest current candidate for a **local desugaring**.

## RETURN

The non-local witness works by changing helper protocol to:

```text
(mode continue-k exit-k payload)
```

and forwarding `exit-k` through nested calls.

That proves D4 expressibility, but it is not the same transformation footprint
as GO.

For a separately compiled/unchanged helper to execute historical RETURN, some
equivalent exit context must already be available. The current countermodel
does not prove that without rewriting the call chain.

## SETQ

The explicit-state witness says directly that pre-existing observers are
**transformed closures** receiving current store:

```text
observer : store -> value
```

and callers invoke:

```text
(observer store)
```

Therefore the countermodel proves D4 expressibility of shared-location
behavior, while changing the observer protocol.

## Decision pressure for #2472

The evidence supports a three-way distinction:

```text
LOCAL-REGION-REWRITE
CALLCHAIN-PROTOCOL-REWRITE
OBSERVER-PROTOCOL-REWRITE
```

The project still needs to decide which footprints count as semantic
derivation versus compilation/expressibility.

A useful conservative candidate law is:

> A local rewrite that preserves all external callable/observer protocols may
> count as DERIVED. A transform that requires unrelated or pre-existing
> values to adopt a new protocol proves expressibility first; it needs an
> additional equivalence theorem before being classified DERIVED.

This is a candidate law, not ratification.

## Reproduce

```sh
python3 scripts/research-2472-transform-footprint.py
```

## Principle

**Measure the rewrite boundary, not merely whether D4 is Turing-powerful enough
to encode the behavior.**
