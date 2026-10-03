# #2713 — live-witness типізованої exact-Q арифметики

Статус: лише research/integration.

Цей witness з'єднує вже доведений Core-Math factor-law з наявним точним
раціональним механізмом виконання SENS, **не стверджуючи спільної бітової
identity**.

## Типізоване розділення

```text
Core-Math.QGroupFactor:
  0   additive family
  1   multiplicative family
  10  multiplicative inverse role (RECIP)

Core execution bridge:
  00001100  наявне exact ADD виконання
  00001110  наявне exact MUL виконання
  00001111  наявне exact division виконання; unary форма дає reciprocal
```

Ці дві колонки належать **різним доменам**. Bridge явний і типізований.

## Мінімальний basis

Witness має лише три bridge entries:

```text
ADD
MUL
RECIP
```

Похідні поведінки будуються, а не читаються з таблиці:

```text
NEG(x)   = MUL(-1, x)
SUB(x,y) = ADD(x, NEG(y))
DIV(x,y) = MUL(x, RECIP(y))
```

Для NEG/SUB/DIV окремих bridge rows немає.

## Exact corpus

```text
2 + 3       = 5
1/2 + 1/3   = 5/6
(-2) * 3    = -6
recip(2)    = 1/2
5 - 8       = -3
6 / 4       = 3/2
recip(0)    = UNDEFINED-MATHEMATICALLY
```

Executable source використовує точні binary Core execution identities у
function position замість `+`, `-`, `*`, `/` чи англійських назв.

## Domain firewall

Witness доводить лише complementarity:

```text
Core-Math operation law
  -> typed bridge
  -> existing Core exact arithmetic mechanism
  -> exact rational value
```

Він не доводить:
- спільну Core/Core-Math binary identity;
- D5/D6 residency для арифметики;
- тотожність із історичною арифметикою LISP 1.5;
- таблицю шести незалежних операцій.

Історичний LISP 1.5 fixed-point RECIP лишається negative control: для
fixed-point аргументу reciprocal історично дорівнює нулю, тоді як exact-Q
reciprocal має інший закон.

## Принцип

**Використовуй три доведені арифметичні здібності й породжуй звичні
зручності; не витрачай Core-координати на дублювання словника.**
