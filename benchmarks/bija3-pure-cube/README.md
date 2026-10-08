# bīja3 pure cube — #3194

This witness derives a D3 candidate from **only eight residents**:

`(), QUOTE, ATOM, CAR, CDR, EQ, COND, CONS`.

It deliberately does **not** read D4–D8, historical code tables, current placement, or migration cost.

## Intrinsic families

```text
structure  () / CONS
selector   CAR / CDR
predicate  ATOM / EQ
control    QUOTE / COND
```

Named cross-family relations used by the witness:

```text
structure ↔ selector
structure ↔ predicate
predicate ↔ control
```

No weighted beauty score is used.

## Lexicographic law-first objective

1. All four family pairs should share one XOR sibling transform.
2. Among equally explanatory transforms, prefer the smallest Hamming weight.
3. After quotienting by a one-bit member axis, require the named family relations to be one-bit moves.
4. Report cube-axis symmetries instead of inventing a winner from arbitrary axis names.

## Exhaustive result

With `000 = ()` fixed, all `7! = 5040` placements are searched:

```text
5040 total
 336 one uniform XOR law for all four pairs
 144 uniform one-bit sibling axis
  48 also place all three named family relations on one-bit edges
   2 after fixing LSB as member axis and natural pair orientation
```

The final two differ only by swapping the two family axes.

## Antipodal candidate

The proposed mapping

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

is **not random**. It satisfies the exact law

```text
sibling = code XOR 111
```

for all four semantic pairs. That is genuine structure.

Its cost is that the sibling transform flips all three bits and family identity is not a direct projection.

## Minimal factorized representative

```text
000  ()
001  CONS

010  CAR
011  CDR

100  ATOM
101  EQ

110  QUOTE
111  COND
```

This gives:

```text
family = first two bits
member = last bit

00 structure
01 selector
10 predicate
11 control
```

and one common sibling law:

```text
sibling = code XOR 001
```

The axis-swapped solution is mathematically equivalent:

```text
000 ()
001 CONS
010 ATOM
011 EQ
100 CAR
101 CDR
110 QUOTE
111 COND
```

The witness therefore does **not** claim that the names of the two family axes are intrinsically ordered.

## Interpretation

The antipodal layout is elegant, but under this explicit law-first objective the factorized layout is strictly simpler at criterion 2: the same four pairs are explained by toggling one bit instead of three, while the remaining two bits expose family identity directly.

**Research only.** This witness does not mutate the production D3 map.
