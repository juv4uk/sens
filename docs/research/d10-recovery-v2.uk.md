# D10 recovery v2 — SCHAR + macro expansion

**Статус:** research / unratified  
**Issue:** #4024  
**Foundation:** D1–D9 owner-ratified #4008 / Contract 11.8

Другий recovery-pass розв'язує дві старі D9 HOLD-позиції через сильніше semantic evidence.

## GENERATE-EXPANSION

Старий donor gloss:

```text
the macro's own one-step expansion function
```

Current D9 уже має:

```text
110001010 MACRO-FUNCTION
```

У Common Lisp macro-function повертає macro expansion function. Отже `GENERATE-EXPANSION` не потребує нового D10 slot:

```text
GENERATE-EXPANSION
-> current projection
-> D9 MACRO-FUNCTION
```

## SCHAR

Старий historical gloss був неправильний:

```text
the character denoted by a code, any type
```

ANSI Common Lisp визначає SCHAR як accessor:

```text
SCHAR(string, index) -> character
```

для simple string.

Це інше від:
- D8 CODE-CHAR;
- D8 CHAR-CODE;
- D9 STRING-FIRST;
- D9 STRING-SLICE.

Тому SCHAR входить у D10 semantic inventory як новий **UNPLACED** candidate.

## Стан D10

```text
before                  264/1024
+ SCHAR                    1
-----------------------------
selected                 265/1024
law-forced coordinates    256
unplaced                    9
remaining                 759
ratified                     0
```

## Після v2 лишаються HOLD

```text
BACKQUANTIZE
COUNT-LEADING-ZEROS
TABLESPACE
COLLECTION
INVOKE
```

Жодної D10 координати цей recovery-pass не призначає.
