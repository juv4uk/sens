# #2175 — D5 selector subtree і residue

Статус: лише research.

Цей witness фіксує тільки ті точні 5-бітні selector-нащадки, які вже випливають
із доведеного CAR/CDR generator.

## Generator-owned D5

```text
10100 CAAAR
10101 CAADR
10110 CADAR
10111 CADDR

11000 CDAAR
11001 CDADR
11010 CDDAR
11011 CDDDR
```

Вони продовжують той самий локальний закон D4:

```text
дописати 0 -> compose CAR
дописати 1 -> compose CDR
```

Приклади:

```text
1010 CAAR
  +0 -> 10100 CAAAR
  +1 -> 10101 CAADR

1101 CDDR
  +0 -> 11010 CDDAR
  +1 -> 11011 CDDDR
```

## Місткість

Exact width=5 має:

```text
32 слова загалом
8 generator-owned selector words
24 residue words
```

Ці 24 residue-слоти **не розподілені**. Вони не є "вільними функціями" і цей
звіт не надає їм значення.

## Важлива межа

Selector suffix-law локальний:

```text
selector family:
  0 = compose CAR
  1 = compose CDR
```

Його не можна переносити на весь D5 без нового доказу.

Так само:

```text
prefix relation != semantic parenthood
```

Майбутня macro/staging-здібність із #2173/#2174 може отримати D5-identity лише
після доведення ролі та placement-аудиту #2175.

## Відтворення

```sh
python3 scripts/research-2175-d5-selector-residue.py
```

Очікуваний заголовок:

```text
D5 selector/residue witness: PASS
width=5
capacity=32
generator-owned=8
residue=24
```

## Принцип

**Доведені генератором комірки зайняті доказом; residue лишається порожнім,
доки адреса не заслужена evidence.**
