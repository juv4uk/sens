# D9 registry tail v1 — останні 39 names

**Статус:** research / unratified  
**Issue:** #3985  
**Foundation:** #3960 / Contract 11.7

Цим проходом закрито весь залишок англійських names із `lib/surface/semantic-registry.lisp`, які не були покриті:
- D1–D8 current residents,
- public-signature harvest,
- D9 library harvest,
- вже вибраними D9 meanings.

## Результат

```text
SELECT-D9-CANDIDATE                  22
LOWER-DOMAIN-OR-SURFACE-PROJECTION   12
INTERNAL-HELPER                       4
HOLD-MECHANISM                        1
---------------------------------------
TOTAL                                39

D9 selected total                   248/512
law-forced coordinates              128
unplaced selected                   120
remaining                           264
ratified D9                            0
```

## 22 нові meanings

```text
ISQRT
SYMBOL?
FIFTH
NUMBER->STRING
IDENTITY
GENSYM
THREAD-FIRST
THREAD-LAST
PROCESS-RUN
TCP-READ
TCP-WRITE
TCP-LISTEN
READ-FILE
WRITE-FILE
BINARY
DIVMOD
ANSWER-NOT
ANSWER-AND
ANSWER-OR
ANSWER-WEAKEN
ANSWER-ATOM
ANSWER-EQ
```

Усі 22 залишаються **UNPLACED**.

## FIFTH — важливе recovery

Драбина має:

```text
D4 CADR    = second
D5 CADDR   = third
D6 CADDDR  = fourth
D7         = Text/Sound
```

Старе selector-compression дослідження прямо записує:

```text
fifth = CADDDDR
```

але current D1–D8 не має resident із цією семантикою.

Тому FIFTH — не alias, а реальний пропуск, який верхній домен повинен повернути.

## 12 lower / projections

```text
lessp?         -> D5 LESSP
greaterp?      -> D5 GREATERP
equalp?        -> D8 EQUAL
not-greaterp?  -> D6 LEQ
not-lessp?     -> D6 GEQ
not?           -> D4 NOT
equal?         -> D8 EQUAL
member?        -> D5 MEMBER
second         -> D4 CADR
third          -> D5 CADDR
fourth         -> D6 CADDDR
null?          -> D4 NULL
```

## 4 internal helpers

За `uk-inventory.lisp` не стають residents:

```text
largest-chunk
nondecreasing-from?
nonincreasing-from?
digit->string
```

Вони лишаються implementation helpers.

## HOLD

`invoke` лишається mechanism boundary. У цьому tranche немає окремого доведеного Core meaning, який треба було б зробити D9 resident.

## Host wrappers

`PROCESS-RUN`, TCP та file I/O відібрані саме як Lisp-owned public semantics поверх raw substrate mechanisms. Raw host functions не переносяться в D9.

## Координати

Старі registry 8-bit addresses не переносяться.

```text
semantic selected != coordinate proved
```

D9 після цього проходу має 248 meanings, але лише 128 selector-law координат.
