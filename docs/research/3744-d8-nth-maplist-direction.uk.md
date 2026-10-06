# D8: NTH/MAPLIST × напрям обходу — #3744

Статус: **RESEARCH / UNRATIFIED**.

Перевіряємо, чи поточна D6-сім'я

```text
NTH | MAPLIST
```

має незалежну вісь `left | right`, яка виводиться з уже чинного D5 `REVERSE`.

## Закон напрямку

Для NTH:

```text
NTH-RIGHT(i,xs) = NTH(i, REVERSE(xs))
```

Для MAPLIST недостатньо лише перевернути вхід. Треба кон'югувати також кожен view, який одержує callback:

```text
MAPLIST-RIGHT(xs,f)
  = MAPLIST(REVERSE(xs),
            lambda tail: f(REVERSE(tail)))
```

Тому права версія бачить:

```text
[xs,
 drop-right-1(xs),
 drop-right-2(xs),
 ...]
```

так само, як звичайний MAPLIST зліва бачить послідовні хвости.

## Типізований квадрат

```text
                    left              right
indexed             NTH               NTH-RIGHT
all views           MAPLIST           MAPLIST-RIGHT
```

## Структурний witness

Нехай:

```text
LEFT-VIEWS(xs)  = [xs, cdr(xs), cdr²(xs), ...]
RIGHT-VIEWS(xs) = map(REVERSE, LEFT-VIEWS(REVERSE(xs)))
```

Тоді для кожного валідного індексу:

```text
NTH(i,xs)       = first(LEFT-VIEWS(xs)[i])
NTH-RIGHT(i,xs) = last(RIGHT-VIEWS(xs)[i])
```

Перевірка identity-view є структурним доказом геометрії до застосування довільного callback: якщо самі view рівні, будь-яка однакова чиста функція над ними збереже рівність.

## Скінченний корпус

Усі бітові списки над `{0,1}` довжини 0..6:

```text
127 списків
126 непорожніх
642 валідні (i,xs) спостереження
```

Очікувана спостережуваність:
- NTH left/right відрізняються у 300 indexed-випадках;
- MAPLIST view-напрям відрізняється на 114 списках.

## Негативний контроль

Хибний скорочений варіант:

```text
MAPLIST(REVERSE(xs), f)
```

перевертає лише вхід, але не callback-view. Він має розійтися з RIGHT-VIEWS на 114 з 126 непорожніх списків; 12 дегенератних рівностей зберігаємо явно.

## Координати

Поточна влада:

```text
D6 NTH     = 000100
D6 MAPLIST = 000101
D5 REVERSE = 10100
```

D8-footprint:

```text
00010000
00010001
00010010
00010011
```

`00` — нижчодоменний дубль NTH.  
`11` — інваріантний породжений кандидат MAPLIST-RIGHT.  
Середні координати — gauge-orbit із MAPLIST та NTH-RIGHT; абсолютний порядок не вигадується.

## Відтворення

```sh
python3 benchmarks/d8-nth-maplist-direction/run.py \
  --out /tmp/d8-nth-maplist-direction
```

Очікуваний статус: `PRODUCT-CANDIDATE-TYPED`.

Це не ратифікація D8 і не створення нового примітива.
