# D8 research ledger — #3673

Цей ledger об'єднує поточне **research-покриття D8**. Це не влада occupancy.

## Поточний облік

```text
місткість D8                             256
selector candidate coordinates            64
footprint трьох product-family            12
проаналізовано унікальних координат        76
untouched coordinates                    180

fixed novel candidates, full protocol       2
fixed novel candidate, protocol-bounded      1
gauge-unresolved novel semantics             3
fixed lower-domain duplicate coordinates     3
gauge orbits                                 3
falsified second-axis hypotheses             5
```

Головне розділення:

```text
analyzed coordinate != D8 resident != primitive occupancy
```

## Selector family

#3646 дає 64 точні selector research coordinates як current D6 selectors × W2.
D7 не є їхнім предком.

## Позитивні product-family

### TAKE/DROP × edge — #3667

```text
11000000 11000001 11000010 11000011
```

- `11000000`: lower-domain TAKE-left duplicate;
- `01/10`: DROP-left duplicate + generated TAKE-right, gauge unresolved;
- `11000011`: generated fixed candidate DROP-right.

### ANY/ALL × predicate polarity — #3668

```text
11110000 11110001 11110010 11110011
```

- `11110000`: lower-domain ANY(p) duplicate;
- `01/10`: ALL(p) duplicate + generated ANY(NOT p), gauge unresolved;
- `11110011`: generated fixed candidate ALL(NOT p).

### REDUCE/SCAN × direction — #3675

```text
10111000 10111001 10111010 10111011
```

- `10111000`: lower-domain REDUCE-left duplicate;
- `01/10`: SCAN-left duplicate + generated REDUCE-right, gauge unresolved;
- `10111011`: generated fixed candidate SCAN-right.

Ця сім'я поки обмежена nonempty-list protocol, бо empty-list presentation
для SCAN ще не має незалежної влади.

## Відкинуті осі

#3670 відкидає п'ять конкретних гіпотез:

- LENGTH/LENGTH-ONTO × reverse;
- MIN-LIST/MAX-LIST × NEG conjugation;
- ADD1/SUB1 × NEG conjugation;
- INTEGERP/RATIONALP × NEG;
- REMAINDER/GCD × argument swap.

Відкидається конкретна друга вісь, а не все D6-сімейство.

## Відтворення

```sh
python3 benchmarks/d8-research-ledger/run.py \
  --out /tmp/d8-research-ledger
```

Artifact містить 64 selector candidates, три product footprints, усі 180
untouched coordinates, gauge metadata і список falsified axes.
