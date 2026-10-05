# D8 NEG/ABS × reciprocal involution — #3729

This is a research-only D8 product witness. It does not admit a D8 resident or
change runtime callability.

## Current inputs

- D6 NEG/ABS family: #3334 / #3366 / #3393;
- D6 RECIP law: #3356 / #3393;
- D8 remains research: #3281;
- current consolidated research accounting: #3726.

No historical D8 donor is used.

## Two axes

Current D6 family:

```text
operation = NEG | ABS
```

Independent candidate axis on nonzero exact rationals:

```text
reciprocal = identity | RECIP
```

Square:

```text
                 x                  RECIP(x)
NEG              NEG(x)             NEG(RECIP(x))
ABS              ABS(x)             ABS(RECIP(x))
```

The reciprocal axis is coherent both before and after the D6 family operation:

```text
NEG(RECIP(x)) = RECIP(NEG(x))
ABS(RECIP(x)) = RECIP(ABS(x))
```

for exact rational x != 0.

## Finite exhaustive witness

The carrier contains every distinct reduced fraction n/d with:
- n in -8..8, excluding 0;
- d in 1..8.

After exact Fraction deduplication this is **86 distinct nonzero rationals**.

Results:

```text
RECIP(RECIP(x)) = x            86 / 86
NEG/RECIP commute              86 / 86
ABS/RECIP commute              86 / 86
```

Both axes are independently observable and all four function tables are
pairwise distinct.

Pairwise truth-table distances:

```text
NEG vs ABS                     43 / 86
NEG vs NEG∘RECIP               84 / 86
NEG vs ABS∘RECIP               85 / 86
ABS vs NEG∘RECIP               85 / 86
ABS vs ABS∘RECIP               84 / 86
NEG∘RECIP vs ABS∘RECIP         43 / 86
```

Zero is explicitly outside the protocol because RECIP is undefined there.

## Negative control

Using input negation itself as the proposed second axis fails:

```text
ABS(NEG(x)) = ABS(x)           86 / 86
unique semantic corner tables   3, not 4
```

So a superficially symmetric involution does not automatically earn a D8 bit.

## Coordinate/gauge result

Current D6 authority:

```text
D6 NEG   = 010010
D6 ABS   = 010011
D6 RECIP = 010110
```

Candidate D8 footprint:

```text
01001000
01001001
01001010
01001011
```

It has zero collision with the 64 selector research coordinates.

With base/base anchored at NEG:

- `01001000 = NEG` is a lower-domain duplicate;
- middle `01/10` contains lower-domain ABS and generated NEG∘RECIP, with
  absolute orientation unresolved;
- **`01001011 = ABS∘RECIP`** is invariant under swapping axis order.

Status: **PRODUCT-CANDIDATE-NONZERO-Q**.

Generated semantics are not primitive admissions.

## Reproduce

```sh
python3 benchmarks/d8-neg-abs-recip/run.py \
  --out /tmp/d8-neg-abs-recip
```
