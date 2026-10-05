# D8 REDUCE/SCAN × напрям fold — #3674

Це research-only D8 product witness для **непорожніх списків**.

Він не ратифікує D8-резидент і не змінює runtime callability.

## Чинні опори

- закон D6 REDUCE/SCAN: #3370;
- owner-ratified координатна влада D6: #3393;
- REVERSE D5: #3305;
- FLIP D6: #3393 / #3384;
- D8 залишається research: #3281.

Старий D8 donor не використовується.

## Дві осі

Перша вісь D6:

```text
exposure = REDUCE | SCAN
```

Кандидат другої осі:

```text
fold direction = left | right
```

На непорожніх списках:

```text
REDUCE-right(f,z,xs)
  = REDUCE-left(FLIP(f), z, REVERSE(xs))

SCAN-right(f,z,xs)
  = SCAN-left(FLIP(f), z, REVERSE(xs))
```

Правий SCAN подається в порядку обчислення, щоб зберігався чинний закон:

```text
last(SCAN-right) = REDUCE-right
```

## Повний finite carrier

На carrier `{0,1}` існує рівно **16** бінарних функцій.
Перебираються всі 16, обидва initial accumulator bits і всі 30 непорожніх
списків довжини 1..4.

```text
16 × 2 × 30 = 960 cases
```

Результат:

```text
left  last(SCAN)=REDUCE       960 / 960
right last(SCAN)=REDUCE       960 / 960

direction observable REDUCE   264 cases
direction observable SCAN     600 cases
multi-step SCAN history       896 cases
```

Негативні контролі:

```text
reverse готового right-SCAN:
  terminal law падає          296 cases

reverse input без FLIP:
  не дорівнює right fold      216 cases
```

Отже left/right — справжня семантична вісь.

## Координатний gauge

Чинний D6 map:

```text
D6 REDUCE = 101110
D6 SCAN   = 101111
```

Кандидатна D8-сім'я:

```text
10111000
10111001
10111010
10111011
```

Перетину із 64 selector-кандидатами немає.

- `10111000 = REDUCE-left` — lower-domain duplicate;
- middle `01/10` orbit містить SCAN-left duplicate і generated REDUCE-right;
- **`10111011 = SCAN-right`** інваріантна до перестановки осей.

## Чесна межа

#3370 фіксує `last(SCAN)=REDUCE`, але не повністю визначає empty-list
presentation для SCAN.

Тому статус лише:

```text
PRODUCT-CANDIDATE-NONEMPTY
```

Ми не вигадуємо empty-list semantics мовчки.

## Відтворення

```sh
python3 benchmarks/d8-reduce-scan-direction/run.py \
  --out /tmp/d8-reduce-scan-direction
```
