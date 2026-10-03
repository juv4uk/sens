# #2506 — D6 binding-policy generator witness

Status: research-only.

## Domain record

```text
DOMAIN        Core D6 candidate family
BINARY OBJECT 0011 + two policy-refinement bits
LAW           independent commuting binding-policy refinements
WITNESS       four-corner executable policy square
FALSIFIER     non-independence / non-commutativity / parent mismatch / collision
STATUS        hypothesis with executable witness
RELATION      Core-only
```

## Input from #2492

D4 `0011 DEFINE` and the shared-location core differ by two independently
observable policies:

```text
search scope:
  current
  nearest-existing

missing-binding policy:
  create
  fail
```

A one-bit D5 child is therefore rejected.

## Candidate two-bit family

The executable square is:

```text
00  current/create   = D4 DEFINE behavior
01  current/fail
10  nearest/create
11  nearest/fail     = shared-location core
```

The semantic refinements are:

```text
S: current -> nearest-existing
M: create  -> fail
```

and the witness proves:

```text
M(S(DEFINE)) = S(M(DEFINE)) = shared-location core
```

Both refinements are idempotent and commute.

That gives a clean product-generator **shape**.

## Exact-width consequence

Tentative D6 projection:

```text
001100  00/base corner
001101  one-axis corner
001110  one-axis corner
001111  both-axis corner
```

But the report deliberately distinguishes semantic generation from residency.

### 001100

This is observationally identical to exact-width parent `0011 DEFINE`.
It is therefore **not earned as a new resident** merely by zero-padding.

### 001101 / 001110

These are well-defined one-axis semantic policies. Whether they deserve
first-class public identities is a separate admission question.

Their labels swap if the two semantic axes are ordered oppositely.

### 001111

The both-refinements corner is invariant under axis-order swap and matches the
already-proven shared-location capability.

It is therefore the strongest D6 coordinate **candidate**, not a ratified
resident.

## Collision

The D6 selector law generates:

```text
101000..101111
110000..110111
```

All four `0011xx` candidate paths are disjoint from those 16 generated
selector descendants.

## Important boundary

This witness proves a product algebra over two policy deltas.

It does not prove:
- that every generated corner deserves a public identity;
- that the displayed axis order is canonical;
- that `001111` is owner-ratified;
- that Core-Math must use the same family.

## Principle

**A wider word is justified by independent semantic dimensions only when their
transformations compose cleanly; occupancy remains a separate admission
decision.**
