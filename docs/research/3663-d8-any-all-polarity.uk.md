# D8 ANY/ALL × полярність предиката — #3663

Це research-only witness для D8 product-law. Він не ратифікує D8-резидент і
не змінює runtime callability.

## Чинні опори

- закон D6 ANY/ALL: #3370;
- owner-ratified координатна влада D6: #3393;
- D8 залишається research: #3281 / Contract 11.6;
- чистий product-screen parent: #3651.

Старий D8 donor не використовується для побудови закону.

## Дві семантичні осі

Перша вісь уже є в D6:

```text
quantifier = ANY | ALL
```

Закон De Morgan дає незалежного кандидата на другу вісь:

```text
predicate polarity = p | NOT∘p
```

Квадрат:

```text
                 p              NOT∘p
ANY              ANY            ANY-NOT
ALL              ALL            ALL-NOT
```

## Повний finite witness

Для вибраного малого carrier простір перебирається повністю:

- алфавіт `{0,1}`;
- **усі 4 можливі предикати** над ним;
- усі 63 списки довжини 0..5.

Разом **252 випадки**.

Результат:

```text
ALL(NOT p) = NOT ANY(p)       252 / 252
ANY(NOT p) = NOT ALL(p)       252 / 252

ANY vs ALL при p               108 різних випадків
ANY vs ALL при NOT p           108
p vs NOT p під ANY             144
p vs NOT p під ALL             144
```

Усі чотири функціонали pairwise distinct.

## Унікальність другої осі

Для чотирьох predicate truth tables існує лише `4! = 24` перестановки.

Witness перебирає всі 24 і перевіряє обидва закони De Morgan на всіх 252
випадках.

```text
перевірено transforms           24
пройшли обидва закони            1
```

Єдиний survivor — побітове заперечення предиката.

Тому друга вісь не домальована з бітової симетрії: вона унікально
визначається семантичним законом у цьому finite universe.

## Координатний gauge

Чинний D6 map дає:

```text
D6 ANY = 111100
D6 ALL = 111101
```

Кандидатна сім'я D8:

```text
11110000
11110001
11110010
11110011
```

Перетину з 64 selector-кандидатами немає.

Base/base фіксує:

```text
11110000 = ANY(p)
```

як lower-domain duplicate.

Перестановка порядку осей міняє місцями лише `01/10`. Тому:

- `ALL(p)` — lower-domain duplicate у middle orbit;
- `ANY(NOT p)` — нова породжена семантика, але її абсолютна координата
  ще gauge-unfixed;
- **`11110011 = ALL(NOT p)`** інваріантна до перестановки осей.

Це generated semantic candidates, а не автоматичні primitive residents D8.

## Відтворення

```sh
python3 benchmarks/d8-any-all-polarity/run.py \
  --out /tmp/d8-any-all-polarity
```
