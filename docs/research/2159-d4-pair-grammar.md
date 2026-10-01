# #2159 — D4 pair-grammar first exhaustive witness

Status: research-only. No D4 allocation is ratified by this report.

## Candidate A

```text
0000 APPLY
0001 EVAL

0010 LAMBDA
0011 DEFINE

0100 NOT
0101 <unallocated>

0110 EVCON
0111 EVLIS

1000 LIST
1001 <unallocated>

1010 CAAR
1011 CADR

1100 CDAR
1101 CDDR

1110 LOOKUP
1111 BIND
```

The four selector addresses are fixed by prior generator evidence.

## Why this candidate is structurally interesting

It gives every D3 prefix a local D4 lane:

```text
000x meta execution
001x abstraction / definition
010x predicate refinement
011x evaluator traversal
100x construction
101x CAR composition
110x CDR composition
111x environment identity
```

Only the selector lanes currently have a proven prefix-generator theorem. The
other labels are placement hypotheses / family affinities and must not be
promoted to semantic parenthood without separate evidence.

Two slots remain intentionally empty:

```text
0101
1001
```

No function is invented merely to fill D4.

## Search space

The executable witness fixes:

```text
1010 CAAR
1011 CADR
1100 CDAR
1101 CDDR
```

and requires these four bootstrap sibling pairs to remain siblings:

```text
APPLY / EVAL
LAMBDA / DEFINE
EVCON / EVLIS
LOOKUP / BIND
```

`LIST`, `NOT`, and two unallocated cells occupy the remaining four cells.

This produces exactly:

```text
69,120 placements
```

## Independent objectives

No single weighted beauty score is used.

### 1. Bootstrap relation adjacency

The witness counts one-bit adjacency only for an explicit relation set derived
from current bootstrap/evaluator structure. Geometry receives credit only after
the relation is named independently.

### 2. D3-prefix family affinity

A separate score asks whether roles land beneath D3 roots with a direct current
family rationale:

- LAMBDA/DEFINE near QUOTE;
- NOT near ATOM or COND;
- EVCON/EVLIS near COND;
- LIST near CONS;
- LOOKUP near EQ;
- BIND near EQ or CONS.

No parent-affinity point is awarded for putting APPLY/EVAL under `000`; that
remains a meta/bootstrap allocation hypothesis rather than a ground-family
theorem.

## Result

```text
Candidate A:
  relation adjacency = 10
  parent affinity     = 8

Global maxima:
  relation adjacency = 13
  parent affinity     = 8

Best relation adjacency among every placement with parent affinity 8:
  10
```

Therefore Candidate A reaches **maximum parent affinity** and also reaches the
**best relation-adjacency score possible without sacrificing that maximum**.

The two-objective Pareto frontier is:

```text
(relation adjacency, parent affinity)

(10, 8)
(12, 6)
(13, 5)
```

Candidate A lies on the frontier.

There are 16 orientation variants sharing the same `(10,8)` objective pair.
So the family layout is much more strongly constrained than the final 0/1
orientation inside several pairs.

## Particularly useful one-bit neighbors in Candidate A

```text
APPLY  <-> EVAL
APPLY  <-> LAMBDA
EVAL   <-> DEFINE
LAMBDA <-> DEFINE

EVCON  <-> EVLIS
EVCON  <-> LOOKUP
EVLIS  <-> BIND

LOOKUP <-> BIND
LOOKUP <-> CAAR
LOOKUP <-> CDAR
BIND   <-> CADR
BIND   <-> CDDR

LIST   <-> CAAR
LIST   <-> CDAR
```

The LOOKUP orientation is especially interesting against current Core1:
environment lookup obtains the key with CAAR-like traversal and the value with
CDAR-like traversal. This is evidence worth testing explicitly, not yet a law.

## What remains unresolved

The exhaustive result does **not** yet justify a universal meaning for the final
bit.

For selectors the suffix theorem is real:

```text
...0 = compose CAR
...1 = compose CDR
```

For other sibling pairs, the last bit is currently only a local pair index.
Do not generalize one selector law to LAMBDA/DEFINE or APPLY/EVAL by analogy.

The 16 tied `(10,8)` variants show that orientation needs a separate criterion:
execution direction, introduction/elimination duality, migration cost,
self-description cost, or hardware decode evidence.

## Reproduce

```sh
python3 scripts/research-2159-d4-pair-grammar.py
```

Expected headline:

```text
placements=69120
candidate-a relation-adjacency=10
candidate-a parent-affinity=8
max relation-adjacency=13
max parent-affinity=8
best relation-adjacency at max parent-affinity=10
pareto=(10,8),(12,6),(13,5)
```

## Principle

**First derive the relations; then let the 4-bit cube compress them.**
