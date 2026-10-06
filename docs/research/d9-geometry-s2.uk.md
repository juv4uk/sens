# D9 geometry S2 — 128 fixed / 384 free

**Статус:** research / unratified  
**Issue:** #3999  
**Semantic inventory:** 512/512 complete

## Поточна геометрія

```text
selected meanings        512
fixed selector coords    128
free coordinates         384
fully unplaced meanings  384
ratified D9 residents      0
```

## Що зафіксовано

Тільки selector family:

```text
D8 selector p
 -> D9 p0 : append A / compose CAR
 -> D9 p1 : append D / compose CDR
```

Це theorem-backed placement.

## Що НЕ робиться

Для решти 384 meanings немає глобального правила:

```text
D8 p -> D9 p0/p1
```

Ширина дає місткість, а не значення.

Тому:
- старі registry/Sens8/Sid8/Function8 codes не використовуються;
- source code position не використовується;
- family resemblance не стає coordinate law без witness;
- 384 meanings лишаються UNPLACED.

## Наступний етап

Шукати локальні executable laws серед 384:

- encode/decode та structure/text inverses;
- constructor/predicate/projection families;
- persistent collection algebra;
- result-status family;
- world/history families;
- TMS/JTMS semantics;
- UTF-8;
- understand/narrate.

Кожна сімʼя має дати окремий висновок:

```text
FIXED
ORBIT
NONE
```

Лише після вичерпання сильних законів можна вимірювати residual gauge.
