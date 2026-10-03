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
Hart MACRO          PARTIAL-PROTOCOL-ALIGNMENT / TIMING-DISTINCT
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

## Phase F — час macro expansion

Історичний Hart MACRO 1963 і поточний SENS transformer збігаються по трьох
відстежуваних form-protocol осях:

```text
raw/full syntax input       = так
explicit caller-env input   = ні
returned replacement form   = так
```

Але загалом це **не той самий протокол**, бо час expansion спостережуваний:

```text
Hart MACRO       = DEFINE / definition-time expansion
SENS TRANSFORMER = evaluation-time expansion
```

#2568/#2569 показує різницю через перевизначення macro: уже розгорнуте тіло у
моделі Hart зберігає OLD, тоді як поточний SENS бачить NEW під час виклику.
Timing — історичний/protocol факт, а не SENS-біт і не доказ ширини.

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

Phase F завершено:

```text
historical-ingest-complete = yes
structural-discovery-may-start = yes
placement-search-may-start = no
```

Останній рядок навмисно лишається `no`: завершення історичного набору дозволяє
структурне дослідження, але не автоматичне заселення вільних D5/D6 координат.

## Принцип

**Спершу збираємо історію. Потім знаходимо структурні закони. Лише потім виводимо native SENS coordinates.**
