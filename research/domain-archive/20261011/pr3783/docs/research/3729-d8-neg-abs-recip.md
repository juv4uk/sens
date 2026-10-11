# D8 NEG/ABS × reciprocal — #3729

Status: **RESEARCH / UNRATIFIED**.

This experiment tests whether current D6 `NEG | ABS` supports an independent second binary axis on the nonzero exact-rational lane:

```text
reciprocal = identity | RECIP
```

The four semantic functionals are:

```text
NEG(x)
ABS(x)
NEG(RECIP(x))
ABS(RECIP(x))
```

## Finite exhaustive carrier

Every distinct reduced rational `n/d` with:

- `n ∈ [-8,8] \ {0}`;
- `d ∈ [1,8]`.

After exact reduction/deduplication this is **86** nonzero rationals.

## Required laws

For every witness value:

```text
RECIP(RECIP(x)) = x
NEG(RECIP(x)) = RECIP(NEG(x))
ABS(RECIP(x)) = RECIP(ABS(x))
```

Both axes must be observable and all four global function tables must be pairwise distinct.

## Strong negative control

Replace RECIP with input sign-negation. Then:

```text
ABS(NEG(x)) = ABS(x)
```

so one corner collapses and only three global function tables remain. This must be reported as `PARTIAL-COLLAPSE`.

## Coordinate/gauge rule

Current D6 authority #3393 fixes:

```text
NEG   = D6:010010
ABS   = D6:010011
RECIP = D6:010110
```

The D8 family footprint is therefore the four coordinates under the NEG parent prefix:

```text
01001000 01001001 01001010 01001011
```

The base `00` corner is the lower-domain NEG duplicate. The `11` corner is invariant under axis-order exchange and is the generated `ABS∘RECIP` candidate. The two middle coordinates remain a gauge orbit containing the lower-domain ABS duplicate and generated `NEG∘RECIP`; no absolute middle orientation is inferred.

## Reproduce

```sh
python3 benchmarks/d8-neg-abs-recip/run.py \
  --out /tmp/d8-neg-abs-recip
```

Expected research status:

```text
PRODUCT-CANDIDATE-NONZERO-Q
```

No D8 resident, primitive, or callability follows from this witness. Zero remains outside the protocol.
