# D1 -> D2 -> bija3 recursive cube — #3196

This witness extends the pure-D3 search from #3194 by admitting only D1 and D2 below it.

It still ignores D4-D8, historical/current opcode tables and migration cost.

## Given lower domains

```text
D1
0  NO
1  YES

D2
00  separator
01  close
10  open
11  dot
```

The experiment does not say that a bit inside D3 literally has D1 semantic identity. Domains remain distinct. The question is narrower:

> can the geometry of D3 be a recursive one-bit extension of D2 while also compressing intrinsic D3 semantic duals?

## D2-prefix fibre hypothesis

```text
D2 prefix   D3 fibre                 operational reading

00          ()     / QUOTE           base / literal
01          ATOM   / CDR             termination / traversal
10          CAR    / EQ              head inspection / comparison
11          COND   / CONS            branch / construction
```

So every D2 coordinate becomes a two-point D3 fibre by appending one new binary coordinate.

This is exactly what the user's original candidate does:

```text
000  ()
001  QUOTE
010  ATOM
011  CDR
100  CAR
101  EQ
110  COND
111  CONS
```

## Independent D3 semantic duals

```text
()    <-> CONS      structure
QUOTE <-> COND      evaluation control
ATOM  <-> EQ        predicates
CDR   <-> CAR       selectors
```

In the proposed layout every pair obeys `dual = code XOR 111`.

## Recursive complement hypothesis

```text
D1 complement: XOR 1
D2 complement: XOR 11
D3 complement: XOR 111
```

For D2 this gives `00<->11` and `01<->10`. If semantic duality grows recursively with cube dimension, D3 predicts XOR 111. The user's candidate satisfies that prediction exactly.

## Exhaustive search

Fix only `000 = ()` and inspect all `7! = 5040` placements:

```text
5040  total placements
   8  preserve all four exact D2-prefix fibres as D2 || one bit
   4  also give all four D3 semantic duals one common XOR transform
   2  also satisfy the recursive complement law XOR 111
   1  if the optional zero-slice spine orientation is additionally required
```

## Why #3194 and #3196 differ

The pure-D3 factorized candidate scores `0/4` against the D2-prefix bridge.
The user's original candidate scores `4/4` plus one global D3 duality law XOR 111.

Therefore the lower domains supply new evidence and legitimately change the recommendation.

## Remaining twofold ambiguity

Recursive-complement laws alone leave two orientations.

### A — user's orientation

```text
000 ()
001 QUOTE
010 ATOM
011 CDR
100 CAR
101 EQ
110 COND
111 CONS
```

### B — middle fibres reversed

```text
000 ()
001 QUOTE
010 CDR
011 ATOM
100 EQ
101 CAR
110 COND
111 CONS
```

Both preserve D2-prefix fibres and XOR-111 semantic duality.

To prefer A uniquely we need one additional law, not taste.

A plausible hypothesis is a D1-like zero-side recursive/control spine:

```text
suffix 0: (), ATOM, CAR, COND
suffix 1: QUOTE, CDR, EQ, CONS
```

Under that hypothesis A is unique. This orientation is intentionally reported as a hypothesis, not yet part of the constitution.

## Current recommendation

If SENS is intended as a recursively grown exact-width domain ladder, candidate A is now stronger than the pure-D3 factorized map because it simultaneously compresses D2->D3 prefix inheritance, a one-bit extension axis, four operational fibres, four semantic-family duals, and recursive complement geometry D1 `1` -> D2 `11` -> D3 `111`.

No production D3 map is changed by this research witness.
