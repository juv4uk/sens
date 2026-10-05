# D8: TAKE/DROP × ліва/права сторона — #3622

Це research-only експеримент із законом D8. Він не ратифікує D8-резидент і
не додає runtime-механізм.

## Вхідні докази

Використовуються лише чинні семантичні опори:
- D6 TAKE/DROP — #3368;
- D5 REVERSE / REVERSE-ONTO — #3305 / #3293 / #3379;
- координатна влада D6 — #3393;
- D8 залишається research — #3281 / Contract 11.6.

D7 не використовується як предок. Старий D8 donor не використовується для
побудови гіпотези.

## Кандидатний закон

Дві незалежно спостережувані бінарні осі:

```text
mode = take | drop
edge = left | right
```

Праві форми визначаються через conjugation операцією REVERSE:

```text
take_right(n,xs) = reverse(take_left(n, reverse(xs)))
drop_right(n,xs) = reverse(drop_left(n, reverse(xs)))
```

Семантичний квадрат:

```text
                left          right
take            TAKE          take_right
drop            DROP          drop_right
```

## Exhaustive bounded witness

Перебираються всі списки над `{0,1}` довжини 0..5 та всі `n` від 0 до
`length+2`.

Разом **447 детермінованих випадків**.

Результат:

```text
REVERSE involution            447 / 447
ліва partition                447 / 447
права partition               447 / 447

edge observable при TAKE      144 випадки
edge observable при DROP      144 випадки
mode observable зліва         438 випадків
mode observable справа        438 випадків

чотири функції pairwise distinct   PASS
порядок двох осей комутує          PASS
```

Негативні контролі:

```text
без фінального REVERSE: partition падає   300 / 447
right-DROP помилково як suffix: падає     438 / 447
```

Отже вісь left/right не є просто перейменуванням.

## Координатний gauge

Research-anchor — чинний D6 TAKE:

```text
D6 TAKE = 110000
D6 DROP = 110001
```

Кандидатна D8-сім'я:

```text
11000000
11000001
11000010
11000011
```

Перетину з 64 selector-кандидатами #3615 немає.

Parent preservation фіксує:

```text
11000000 = TAKE-left
```

це lower-domain duplicate, тому новий D8 resident не заробляється.

Перестановка порядку двох осей міняє місцями лише середні кути:
`01/10`. Тому абсолютна координата `take_right` ще не визначена.

Але кут `11` інваріантний:

```text
11000011 = drop_right
```

Отже експеримент дає:
- один orientation-invariant novel coordinate candidate: `11000011`;
- одну нову семантику `take_right` з невирішеним middle-coordinate gauge;
- два lower-domain duplicates.

Статус: **PRODUCT-CANDIDATE**, не CURRENT.

## Відтворення

```sh
python3 benchmarks/d8-take-drop-edge/run.py \
  --out /tmp/d8-take-drop-edge
```

## Свіжість влади

Executable witness не довіряє hardcoded координатам D6 TAKE/DROP. Він читає
`knowledge/d6-ratified.json`, вимагає owner authority `#3393`, знаходить TAKE і
DROP у чинній 64-рядковій мапі та записує SHA-256 джерела в machine-readable
artifact. Якщо влада D6 колись зміниться, witness впаде або змінить provenance,
а не збереже мовчки застарілу координату.
