# #2568 — Hart DEFINE-time проти current SENS evaluation-time expansion

Статус: **HISTORICAL-INGEST / protocol falsifier**. Жодної binary coordinate не виділяємо.

## Первинна історична premise

Timothy P. Hart, *MACRO Definitions for LISP*, MIT AI Memo 57, October 1963
(AIM-057; MIT DSpace handle `1721.1/6111`).

Hart пропонує MACRO instruction expander у `DEFINE`. Macro definition містить
функцію, яка отримує macro-call form, а повернена нею форма заміняє початкову
форму у function definitions.

Отже історичний expansion locus у цьому witness:

```text
Hart MACRO:
  expansion locus = DEFINE / до пізнішого виконання функції
```

Це історичний факт-source premise, а не висновок Python-моделі.

## Current SENS control

Поточний `apply_macro`:

```text
raw Expr operands
 -> transformer body
 -> Value
 -> Expr
 -> TailCall(expansion, calling_environment)
```

Live integration test фіксує trace:

```text
define transformer -> OLD expansion
define ordinary function із transformer call
redefine той самий transformer -> NEW expansion
call уже визначеної функції
```

Current SENS повертає:

```text
NEW
```

Отже transformer call лишався живим до evaluation time.

## Мінімальний countermodel

Для того самого trace:

```text
Hart DEFINE-time model -> OLD
SENS evaluation-time   -> NEW
```

Результат різний, хоча transformer algorithm не міняється. Міняється лише
expansion locus.

Тому для bounded observation:

```text
EXPANSION-TIMING=INDEPENDENT-AXIS
```

## Уточнені Phase-F axes

FEXPR/macro comparison тепер потребує щонайменше:

```text
A operand representation
B direct caller-environment input
C result protocol
D expansion locus / semantic time
```

Current evidence:

```text
FEXPR/FSUBR:
  A raw
  B explicit caller env
  C direct value
  D evaluation-time special call

Hart MACRO (1963):
  A whole/raw source form
  B no direct runtime caller-env input in proposed macro-function protocol
  C replacement source form
  D DEFINE/pre-compilation expansion

current SENS TRANSFORMER:
  A raw source operands
  B no direct caller-env transformer parameter
  C returned form re-evaluated
  D evaluation-time expansion
```

## Не-висновки

Це не доводить:
- 4-бітний SENS domain;
- D5/D6 coordinate;
- що Hart MACRO і current SENS TRANSFORMER мусять бути різними primitives;
- що один protocol "сильніший".

Доведено лише, що timing/locus спостережувано відрізняється у bounded
redefinition trace.

## Відтворення

```sh
cargo test -p sens --test post_d4_macro_timing -- --nocapture
python3 scripts/research-2568-macro-timing.py
```

## Принцип

**Повернути syntax — одна вісь; визначити, коли ця syntax замінює програму —
інша.**
