# D8 research ledger — #3673

Цей ledger об'єднує поточне **research-покриття D8**. Це не влада occupancy.

## Поточний облік

```text
місткість D8                             256
selector candidate coordinates            64
footprint п'яти product-family              20
проаналізовано унікальних координат        84
untouched coordinates                    172

fixed novel candidates, full protocol       3
fixed novel candidate, protocol-bounded      1
fixed novel candidate, typed                 1
gauge-unresolved novel semantics             5
fixed lower-domain duplicate coordinates     5
gauge orbits                                 5
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

### REDUCE/SCAN × direction — #3704

```text
10111000 10111001 10111010 10111011
```

- `10111000`: lower-domain REDUCE-left duplicate;
- `01/10`: SCAN-left duplicate + generated REDUCE-right, gauge unresolved;
- `10111011`: generated fixed candidate SCAN-right.

Ця сім'я поки обмежена nonempty-list protocol, бо empty-list presentation
для SCAN ще не має незалежної влади.

### ZIP/UNZIP × orientation — #3712

```text
11100000 11100001 11100010 11100011
```

- `11100000`: lower-domain ZIP-normal duplicate;
- `01/10`: UNZIP-normal duplicate + generated ZIP-SWAPPED, gauge unresolved;
- `11100011`: generated fixed candidate UNZIP-SWAPPED.

Це typed product witness для equal-length ZIP/UNZIP lane.
#3712 уже merged у main; ця сім'я є merged research evidence, а не D8 occupancy authority.

### DO/WHILE × condition/projection — #3779

```text
11001100 11001101 11001110 11001111
```

- `11001100`: lower-domain WHILE duplicate;
- `01/10`: DO duplicate + generated `continue-while-true + apply-result`, gauge unresolved;
- `11001111`: generated fixed candidate `stop-when-true + return-state`.

Bounded witness на трьох станах перевіряє 5832 схеми: 972 завершуються в усіх чотирьох кутах, а 432 мають чотири попарно різні глобальні semantic tables. #3779 уже merged як research evidence і не допускає жодної D8 coordinate.

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

Artifact містить 64 selector candidates, п'ять product footprints, усі 172
untouched coordinates, gauge metadata, evidence merge state і список falsified axes.
