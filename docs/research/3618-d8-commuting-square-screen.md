# D8 commuting-square evidence screen — #3618

This lane tests whether the **current** D6 semantic evidence already contains
enough structure to justify any non-selector D8 two-bit product family.

A D8 product square needs two independently observable binary refinements:

```text
        B=0      B=1
A=0      00       01
A=1      10       11
```

The square is acceptable only when both axes are independently meaningful and
the derivations commute.

## Current input

The machine-readable D6 family corpus
`knowledge/d6-v2-binary-law-families.json` contains 16 executable relation
families covering 32 current D6 residents.

Every family currently contains:

- exactly two semantic members;
- exactly one documented binary relation;
- evidence for that relation.

That is enough for **one bit of semantic distinction**. It is not enough for a
D8 2×2 product, which requires **two independent bits**.

The executable screen therefore reports:

```text
families screened                 16
members screened                  32
families with one documented axis 16
families ready for D8 product       0
```

This is not a theorem that a second axis cannot exist. It is a theorem about
the present evidence corpus: a second axis is not yet documented and must not
be fabricated from coordinate symmetry.

## Controls

The script includes two bounded method controls.

Positive control: the two-policy shape from #2506. Independent `scope` and
`missing-binding policy` refinements commute and therefore demonstrate what a
real two-axis product witness looks like.

Negative control: deliberately order-dependent transforms do not commute and
are rejected.

The screen also reconstructs the 64 current D8 selector research coordinates
from current D6 selector prefixes solely as a collision-control set. It does
not admit those coordinates or use the historical D8 donor.

## Reproduce

```sh
python3 scripts/research-3618-d8-commuting-square-screen.py \
  --out /tmp/d8-commuting-square-screen
```

## Advancement rule

A D6 family may move from `INSUFFICIENT-CURRENT-EVIDENCE` to
`PRODUCT-CANDIDATE` only after new evidence supplies:

1. a second independently observable binary semantic axis;
2. an executable commutativity witness;
3. parent preservation;
4. well-defined intermediate corners;
5. a reproducible target corner;
6. collision freedom against the selector candidate set.

No Function8/Sens8 row and no historical D8 name can supply the missing axis.
