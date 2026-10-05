# D8 research ledger — #3673

This ledger consolidates current D8 **research coverage**. It is not semantic
occupancy authority.

## Current accounting

```text
D8 capacity                              256
selector candidate coordinates            64
three product-family footprints           12
analyzed unique coordinate positions      76
untouched coordinate positions           180

fixed novel candidates, full protocol       2
fixed novel candidate, protocol-bounded      1
gauge-unresolved novel semantics             3
fixed lower-domain duplicate coordinates     3
gauge orbits                                 3
falsified second-axis hypotheses             5
```

The key distinction is:

```text
analyzed coordinate != D8 resident != primitive occupancy
```

## Selector family

#3646 contributes 64 exact selector research coordinates generated directly
from current D6 selectors × W2. D7 is excluded from ancestry.

## Positive product families

### TAKE/DROP × edge — #3667

Footprint:

```text
11000000 11000001 11000010 11000011
```

- `11000000`: lower-domain TAKE-left duplicate;
- middle `01/10`: DROP-left duplicate + generated TAKE-right, gauge unresolved;
- `11000011`: generated fixed candidate DROP-right.

### ANY/ALL × predicate polarity — #3668

Footprint:

```text
11110000 11110001 11110010 11110011
```

- `11110000`: lower-domain ANY(p) duplicate;
- middle `01/10`: ALL(p) duplicate + generated ANY(NOT p), gauge unresolved;
- `11110011`: generated fixed candidate ALL(NOT p).

### REDUCE/SCAN × direction — #3675

Footprint:

```text
10111000 10111001 10111010 10111011
```

- `10111000`: lower-domain REDUCE-left duplicate;
- middle `01/10`: SCAN-left duplicate + generated REDUCE-right, gauge unresolved;
- `10111011`: generated fixed candidate SCAN-right.

This family is still limited to the nonempty-list protocol because the
empty-list SCAN presentation is not independently pinned.

## Falsified axes

#3670 records five rejected hypotheses:

- LENGTH/LENGTH-ONTO × reverse;
- MIN-LIST/MAX-LIST × NEG conjugation;
- ADD1/SUB1 × NEG conjugation;
- INTEGERP/RATIONALP × NEG;
- REMAINDER/GCD × argument swap.

The rejection applies to the tested axis, not to the entire D6 family.

## Reproduce

```sh
python3 benchmarks/d8-research-ledger/run.py \
  --out /tmp/d8-research-ledger
```

The artifact contains all 64 selector candidate coordinates, all product
footprints, all 180 untouched coordinates, gauge metadata, and the current
falsifier list.
