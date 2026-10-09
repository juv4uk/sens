# D6 v2 clean-room shadow — #3280

Чинна нижня authority: D5 #3305 / Contract 11.3. D6 лишається нератифікованим за #3278.

## Що допускаємо в цьому shadow

Тільки 16 selector descendants, геометрія яких примусово випливає із selector composition law:

```text
011000 CDAAAR   011001 CDAADR
011010 CDADAR   011011 CDADDR
011100 CDDAAR   011101 CDDADR
011110 CDDDAR   011111 CDDDDR

100000 CAAAAR   100001 CAAADR
100010 CAADAR   100011 CAADDR
100100 CADAAR   100101 CADADR
100110 CADDAR   100111 CADDDR
```

Усі інші координати нового D6 починають як UNKNOWN.

## Аудит донорів

Старий D6 дає корисні семантичні донори, але не дає coordinate authority.

П'ять історичних residents явно виключаємо з clean Core candidate, доки мутацію не буде окремо допущено:

```text
RPLACA
RPLACD
SETF
NCONC
NREVERSE
```

Вони вимагають destructive/generalized mutation, якої чинний SENS навмисно не експонує.

Решта non-selector функцій залишаються UNPLACED candidates. Окремо зберігаємо вже доведені закони: parity, LET/LET* binding order, macro expansion closure, numeric order lattice, set lattice та selectors.

## Метрики

```text
capacity                  64
generated selectors       16
UNKNOWN coordinates       48
unplaced donor candidates 43
mutation donors excluded  5
lower-domain duplicates    0
```

Це не повний D6 і не ратифікація. Це чистий baseline, від якого D6 має заробити кожного resident.
