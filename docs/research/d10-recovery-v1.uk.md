# D10 recovery v1 — surviving D9 HOLD rows

**Статус:** research / unratified  
**Issue:** #4016  
**Foundation:** #4008 / Contract 11.8 / D1–D9

Після ратифікації D9 повторно перевірено 19 рядків, які в D9 лишилися HOLD.

## Результат

```text
SELECT-D10-CANDIDATE                  8
LOWER/SURFACE/MECHANISM PROJECTION    4
HOLD-SEMANTIC-REVIEW                  7
---------------------------------------
TOTAL                                19

D10 selected total                  264/1024
law-forced coordinates              256
unplaced selected                     8
remaining                           760
ratified D10                           0
```

## SELECT

```text
COMPILE-FILE
LDB
MASK-FIELD
BOOLE
MONO-NS
UNIX-TIME-NOW
NTP-QUERY-RAW
TIMEZONE-DECLARATIONS-RAW
```

Чотири raw world-observation operations доповнюють D9 wrappers: MONO-MS, UTC-NOW, INTERNET-TIME-SYNC, TIMEZONE-DETECT. Тобто D10 зберігає сирий факт, а D9 — його інтерпретовану форму.

## Не займають D10 slot

- THE — compile-time declaration metadata without independent runtime meaning;
- defmacro — surface packaging over D5 MACRO + D4 DEFINE;
- codepoint->string — projection to D8 CODE-CHAR;
- string->codepoint — projection to D8 CHAR-CODE.

## HOLD

GENERATE-EXPANSION, BACKQUANTIZE, COUNT-LEADING-ZEROS, SCHAR, TABLESPACE, COLLECTION, INVOKE.

Жоден із 8 нових meanings не отримав координату. Meaning selection і placement лишаються окремими задачами.
