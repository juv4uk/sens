# D8 NEG/ABS × reciprocal involution — #3729

Це research-only D8 product witness. Він не ратифікує D8-резидент і не
змінює runtime callability.

## Чинні опори

- D6 family NEG/ABS: #3334 / #3366 / #3393;
- закон D6 RECIP: #3356 / #3393;
- D8 залишається research: #3281;
- поточний consolidated research accounting: #3726.

Старий D8 donor не використовується.

## Дві осі

Перша вісь:

```text
operation = NEG | ABS
```

Друга вісь на ненульових exact rationals:

```text
reciprocal = identity | RECIP
```

Квадрат:

```text
                 x                  RECIP(x)
NEG              NEG(x)             NEG(RECIP(x))
ABS              ABS(x)             ABS(RECIP(x))
```

RECIP узгоджено комутує з обома операціями:

```text
NEG(RECIP(x)) = RECIP(NEG(x))
ABS(RECIP(x)) = RECIP(ABS(x))
```

для exact rational x != 0.

## Повний finite witness

Беруться всі різні reduced n/d:
- n від -8 до 8, крім 0;
- d від 1 до 8.

Після exact Fraction deduplication маємо **86 різних ненульових rationals**.

```text
RECIP(RECIP(x)) = x            86 / 86
NEG/RECIP commute              86 / 86
ABS/RECIP commute              86 / 86
```

Обидві осі незалежно спостережувані; усі чотири function tables різні.

Zero навмисно не входить у protocol, бо RECIP(0) не визначений.

## Негативний контроль

Якщо другою віссю спробувати зробити input NEG:

```text
ABS(NEG(x)) = ABS(x)           86 / 86
унікальних semantic corners     3, не 4
```

Отже не кожна красива involution дає новий D8 bit.

## Coordinate/gauge

Чинний D6 map:

```text
D6 NEG   = 010010
D6 ABS   = 010011
D6 RECIP = 010110
```

Candidate footprint:

```text
01001000
01001001
01001010
01001011
```

Перетину з 64 selector research coordinates немає.

- `01001000 = NEG` — lower-domain duplicate;
- middle `01/10` містить ABS duplicate та generated NEG∘RECIP;
- **`01001011 = ABS∘RECIP`** — invariant 11-corner.

Статус: **PRODUCT-CANDIDATE-NONZERO-Q**.

Це generated semantics, не primitive admissions.

## Відтворення

```sh
python3 benchmarks/d8-neg-abs-recip/run.py \
  --out /tmp/d8-neg-abs-recip
```
