# D9 overflow review v1

**Статус:** research / unratified  
**Parent:** #3964  
**Inventory task:** #3965  
**Foundation:** #3960 / Contract 11.7

Після 128 selector-law кандидатів переглянуто всі 34 рядки, які не ввійшли у щільний D8.

## Результат

```text
SELECT-D9-CANDIDATE             20
HOLD-SEMANTIC-REVIEW           11
REJECT-EXACT-LOWER-DUPLICATE    3
---------------------------------
TOTAL                           34

D9 selected total             148/512
remaining                     364
ratified residents              0
```

## Точні lower duplicates

```text
APPLY    -> D4:0000
COMPOSE  -> D6:001011
REDUCE   -> D6:101110
```

Ці рядки не отримують D9 identity.

## Важливий negative control

OPEN і CLOSE уже існують як назви в D2, але там вони означають structural syntax. Overflow-рядки означають stream open/close. Отже однакове людське імʼя не є доказом semantic duplication.

## SELECT

Відібрано 20 чітко відмінних language-visible semantics, але поки без D9 coordinates:

```text
OPEN CLOSE WITH-OPEN-FILE DRIBBLE
FFI-CALL
ARGLIST &WHOLE
MACRO-FUNCTION COMPILER-MACRO SYMBOL-MACRO
DEFINE-SYMBOL-MACRO DEFINE-COMPILER-MACRO
DEFSTRUCT DEFTYPE DEFINE-CONDITION
ERROR-IF-NOT-ERROR DEHANDLER
ROW-MAJOR-AREF
NUNION NRECONC
```

NUNION/NRECONC знову допустимі до розгляду, бо D8 уже ратифікував observable mutation через RPLACA/RPLACD.

## HOLD

11 рядків не викинуті. Вони чекають точнішого закону або boundary decision: compiler/tooling, typed-word/Core-Math, macro-expansion overlap, system-specific semantics або недостатньо точний historical description.

Machine-readable artifact: `knowledge/d9-overflow-review-v1.json`.
