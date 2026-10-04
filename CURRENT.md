# CURRENT — where the truth actually lives

Це єдина точка входу для питання «що зараз чинне». Owner reset **#3327** скасовує всі semantic ratification вище D2.

## Current authority

```text
D1  RATIFIED / CURRENT
    PredicateBit: 0 = NO, 1 = YES

D2  RATIFIED / CURRENT
    racanā2: 00 separator, 01 close, 10 open, 11 dot

D3  UNRATIFIED / RESEARCH
D4  UNRATIFIED / RESEARCH
D5  UNRATIFIED / RESEARCH
D6  UNRATIFIED / RESEARCH
D7  UNRATIFIED / RESEARCH
D8  UNRATIFIED / RESEARCH
```

Current contract: **Contract 11.4** in `language-contract.lisp`.

## Meaning of #3327

- #1699 D1 and #1702 D2 remain current authority.
- #3202 D3, #3272 D4, #3305 D5, #2415 D7, and every other D3-D8 occupancy/placement ratification are revoked.
- Old D3-D8 maps, proofs, tests, benchmarks and implementation work remain evidence/provenance only.
- W1-W8 exact-width carriers remain mechanical objects. Parsing, packing or serialization does not imply semantic admission.
- D3-D8 callable/Core-operation admission fails closed until a new explicit owner ratification.

## Rebuild order

```text
D1 + D2
   ↓
derive D3
   ↓
derive D4 from accepted D3
   ↓
derive D5 from accepted D3→D4 tree
   ↓
continue upward
```

A higher-domain result cannot be used as a premise before the lower-domain chain supporting it is current again.

## Authority order

1. `language-contract.lisp` + owner reset #3327.
2. D1/D2 ratified decisions.
3. Executable witnesses that do not claim revoked D3-D8 semantic authority.
4. Research maps / old ratifications as evidence only.
5. Historical Sens8/Sid8/Function8 as compatibility/provenance only.

## Current identity discipline

```text
semantic object
=
exact binary object
+ exact domain
+ CURRENT admitted/proved law
```

For D3-D8 today the final term is absent. Those widths are research carriers, not current semantic residents.

## For agents

Do not implement or infer D3-D8 placement from old ratification files. Start from D1/D2 and re-derive. Preserve old evidence; do not treat it as authority.
