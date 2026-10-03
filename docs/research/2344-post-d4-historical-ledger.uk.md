# #2344 — Історичний ledger раннього Lisp

Статус: **HISTORICAL-INGEST**. Це облік evidence, а не мовна семантична authority.

Machine source:

```text
docs/research/2344-post-d4-historical-ledger.json
```

Validator:

```text
scripts/research-2344-historical-ledger.py
```

## Поточна хронологія

Завершено:

```text
LABEL            DERIVED-D1-D4
FUNCTION/FUNARG  HISTORICAL-MECHANISM
EVALQUOTE        DERIVED-D1-D4

APPEND            DERIVED-D1-D4
PAIR/PAIRLIS      DERIVED-D1-D4
ASSOC              DERIVED-D1-D4
SUBST/SUBLIS      DERIVED-D1-D4
MAPLIST            DERIVED-D1-D4

SET/SETQ           NEW-OBSERVABLE-CAPABILITY
GO                 DERIVED-D1-D4
RETURN             NEW-OBSERVABLE-CAPABILITY

FEXPR/FSUBR        RAW+ENV-TWO-CAPABILITIES
```

Активно:

```text
TRANSFORMER / later macro staging -> #2557
```

## Важлива межа Phase D

Whole-program compilation не стирає source capability.

```text
SET/SETQ shared-location update
  = NEW-OBSERVABLE-CAPABILITY
  + COMPILABLE-TO-D4-GLOBAL

GO
  = DERIVED-D1-D4 локально

RETURN
  = NEW-OBSERVABLE-CAPABILITY
  + COMPILABLE-TO-D4-GLOBAL
```

Це відповідає derivation law #2468.

## Phase E protocol

Історичний FEXPR/FSUBR:

```text
raw operands        = 1
explicit caller env = 1
result re-eval      = 0
```

Порівняння з поточним SENS transformer:

```text
raw operands        = 1
explicit caller env = 0
result re-eval      = 1
```

Спільна raw-operand вісь не робить ці протоколи однією capability.

## Placement boundary

Кожен ряд цього ingest ledger лишає:

```text
binary_object = unplaced
```

навіть якщо пізніший SENS-аналіз уже довів derivability або нову capability.

Generated D5 selector subtree — окремий baseline fact:

```text
10100 10101 10110 10111
11000 11001 11010 11011
```

Він не завершує історичний inventory.

## Gate

Поки #2557 активний:

```text
historical-ingest-complete = no
structural-discovery-may-start = no
placement-search-may-start = no
```

## Принцип

**Спершу збираємо історію. Потім знаходимо структурні закони. Лише потім виводимо native SENS coordinates.**
