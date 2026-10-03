# #2580 — форма входу macro call

Статус: лише research; historical/protocol witness.

## Історична преміса

У Hart AIM-057 MACRO-функція отримує один аргумент: форму, що починається з
імені macro.

Тобто історичний протокол бачить повний виклик:

```text
(macro-name arg1 arg2 ...)
```

Голова виклику є частиною вхідної форми.

## Поточний SENS

Поточний evaluator відділяє голову до `apply_macro`:

```text
items[0]    -> head dispatch
items[1..]  -> arguments -> apply_macro
```

`apply_macro` отримує closure, raw operand `Expr`, calling environment і
span. Окремого параметра з головою виклику немає.

## Alias-фальсифікатор

Один transformer під двома головами:

```text
(macro-a payload)
(macro-b payload)
```

Whole-call модель Hart бачить різні входи, бо head входить у форму.

Current operand-only SENS передає однаковий payload:

```text
[payload]
[payload]
```

Із двох однакових payload неможливо детерміновано відновити різні голови без
нового явного semantic channel.

## Результат

```text
CALL-PACKAGING=INDEPENDENT-AXIS
HART-INPUT-SHAPE=WHOLE-CALL
SENS-INPUT-SHAPE=OPERANDS-ONLY
BINARY-OBJECT=UNPLACED
EXACT-WIDTH=UNRESOLVED
```

Старі грубі осі raw/env/result можуть помилково злити два різні протоколи.

## Не випливає

Жоден новий SENS-біт, width чи coordinate з цього не випливає. Це історичне
спостереження, яке треба зберегти до structural discovery.
