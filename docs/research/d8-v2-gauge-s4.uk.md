# D8 v2 — S4 canonical gauge candidate

**Статус:** research / unratified.

Після повного 256/256 semantic inventory та S2-геометрії лишилась недовизначена координатна свобода. Як і в D6 S4, вибирається один відтворюваний представник без удавання, що tie-break є семантичним законом.

## Основа

```text
LAW-FORCED       64
PRODUCT-FIXED      8
GAUGE-ORIENTED     7
GAUGE-FIXED      177
--------------------
TOTAL            256
```

## Canonical tie-break

1. 72 theorem/fixed assignments не рухаються.
2. Для 7 двокоординатних orbit вибирається лексикографічно менша координата.
3. Після цього лишається 177 meanings і 177 coordinates.
4. Historical stable IDs спочатку робляться coordinate-independent opaque hashes semantic descriptor.
5. Stable IDs і вільні координати сортуються окремо та з'єднуються `zip`.

## Чого S4 НЕ використовує

- legacy Sens8/Function8;
- старі #2934 coordinates;
- migration distance;
- runtime addresses;
- історичну adjacency як theorem.

Особливо важливо: перша чернетка S4 була відкинута ще до PR, бо historical stable IDs містили donor coordinate. Після виправлення gauge map перегенеровано з coordinate-independent IDs.

## Межа authority

`knowledge/d8-v2-gauge-fixed-candidate.json` — це повна candidate map, але **не ратифікований D8**. Future stronger law може змінити GAUGE-* рядки до owner ratification.
