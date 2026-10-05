# D8 research ledger — #3673

This ledger consolidates current D8 **research coverage**. It is not semantic
occupancy authority.

## Current accounting

```text
D8 capacity                              256
selector candidate coordinates            64
four product-family footprints            16
analyzed unique coordinate positions      80
untouched coordinate positions           176

fixed novel candidates, full protocol       2
fixed novel candidate, protocol-bounded      1
fixed novel candidate, typed                 1
gauge-unresolved novel semantics             4
fixed lower-domain duplicate coordinates     4
gauge orbits                                 4
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

### REDUCE/SCAN × direction — #3704

Footprint:

```text
10111000 10111001 10111010 10111011
```

- `10111000`: lower-domain REDUCE-left duplicate;
- middle `01/10`: SCAN-left duplicate + generated REDUCE-right, gauge unresolved;
- `10111011`: generated fixed candidate SCAN-right.

This family is still limited to the nonempty-list protocol because the
empty-list SCAN presentation is not independently pinned.

### ZIP/UNZIP × orientation — #3712

Footprint:

```text
11100000 11100001 11100010 11100011
```

- `11100000`: lower-domain ZIP-normal duplicate;
- middle `01/10`: UNZIP-normal duplicate + generated ZIP-SWAPPED, gauge unresolved;
- `11100011`: generated fixed candidate UNZIP-SWAPPED.

This is a typed product witness over the equal-length ZIP/UNZIP lane.
#3712 is merged into main; this family is merged research evidence, not D8 occupancy authority.

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

The artifact contains all 64 selector candidate coordinates, four product
footprints, all 176 untouched coordinates, gauge metadata, evidence merge
state, and the current falsifier list.
