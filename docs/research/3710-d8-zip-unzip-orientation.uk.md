# D8 ZIP/UNZIP × орієнтація добутку — #3710

Це research-only typed D8 witness. Він не ратифікує D8-резидент і не змінює
runtime callability.

## Чинні опори

- закон D6 ZIP/UNZIP: #3370;
- owner-ratified координатна влада D6: #3393;
- D8 залишається research: #3281.

Старий D8 donor не використовується.

## Дві осі

Перша, уже наявна вісь D6:

```text
constructor = ZIP
destructor  = UNZIP
```

Незалежна вісь орієнтації:

```text
normal | swapped
```

Похідні значення:

```text
ZIP-SWAPPED(xs,ys) = ZIP(ys,xs)
UNZIP-SWAPPED(ps)  = swap(UNZIP(ps))
```

Typed square:

```text
                    normal          swapped
constructor         ZIP             ZIP-SWAPPED
destructor          UNZIP           UNZIP-SWAPPED
```

## Повний finite witness

Carrier: бітові списки над `{0,1}`, equal-length lane, довжини 0..4.

```text
1 + 4 + 16 + 64 + 256 = 341 cases
```

Результати:

```text
UNZIP(ZIP(xs,ys))                       341 / 341
UNZIP-SWAPPED(ZIP-SWAPPED(xs,ys))      341 / 341

ZIP orientation observable              310 cases
UNZIP orientation observable            310 cases

ZIP orientation involution              341 / 341
UNZIP orientation involution            341 / 341
```

Лише 31 case має `xs = ys`; інші 310 роблять orientation спостережуваною.

Негативні контролі:

```text
swap тільки ZIP                         310 roundtrip failures
swap тільки UNZIP                       310 roundtrip failures
```

Отже орієнтація мусить мінятися узгоджено з обох боків product-law.

## Координатний gauge

Чинний D6 map:

```text
D6 ZIP   = 111000
D6 UNZIP = 111001
```

Кандидатна сім'я:

```text
11100000
11100001
11100010
11100011
```

Перетину з 64 selector-кандидатами немає.

- `11100000 = ZIP` — lower-domain duplicate;
- middle `01/10` orbit містить UNZIP duplicate та generated ZIP-SWAPPED;
- **`11100011 = UNZIP-SWAPPED`** інваріантна до перестановки осей.

Це typed square: constructor/destructor мають дуальні сигнатури, тому
незалежність доводиться round-trip діаграмою, а не штучним порівнянням
різнотипних функцій.

Статус: **PRODUCT-CANDIDATE-TYPED**.

## Відтворення

```sh
python3 benchmarks/d8-zip-unzip-orientation/run.py \
  --out /tmp/d8-zip-unzip-orientation
```
