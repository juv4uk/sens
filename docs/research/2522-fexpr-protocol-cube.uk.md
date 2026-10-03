# #2522 — protocol cube для FEXPR/FSUBR

Статус: лише research.

## Historical control

Appendix B *LISP 1.5 Programmer's Manual* явно розділяє call paths.

Ordinary EXPR/SUBR спершу обчислюють operands через `evlis`.

FEXPR отримує разом:

```text
cdr(form)   ; сирі operand forms
a           ; current a-list / caller context
```

Структурно interpreter описує це як:

```text
apply(fexpr, list(cdr(form), a), a)
```

FSUBR аналогічно отримує raw tail у AC і current a-list у `$ALIST`.

Джерело: *LISP 1.5 Programmer's Manual*, Appendix B, друковані стор. 70–71.

## Три незалежні protocol-осі

Executable witness розкладає:

```text
A operand mode
  0 eager values
  1 raw forms

B caller-context input
  0 немає як прямого semantic input
  1 explicit caller environment/a-list

C result protocol
  0 повернений object є value виклику
  1 повернений object є code і re-evaluate у caller context
```

Усі вісім кутів мають різні signatures під трьома ізольованими probes.

### A — raw operand

Невикористаний undefined другий operand:

```text
eager -> error до body
raw   -> body може його не чіпати
```

### B — caller context

Body просить caller-only binding, який не передано operand:

```text
no direct env -> unavailable
caller env    -> visible
```

### C — result protocol

Body повертає symbol/form `x`, caller має `x=42`:

```text
direct value -> x
form re-eval -> 42
```

Кожна axis змінюється незалежно від двох інших.

## Historical FEXPR/FSUBR

Protocol-level:

```text
operand = raw
env     = explicit caller context
result  = direct value
```

Raw preservation і caller-context access незалежно observable, тому
попередня Phase-E класифікація:

```text
FEXPR-FSUBR=RAW+ENV-TWO-CAPABILITIES
```

Це не означає дві public primitive names чи два binary residents. Це означає
дві незалежні semantic distinctions у historical call protocol.

## Relation to current TRANSFORMER

Witness також перевіряє live `apply_macro`:

```text
raw Expr operands
 -> quote as data
 -> transformer closure frame
 -> transformer body returns Value
 -> Value -> Expr
 -> tail-evaluate in calling_environment
```

Caller environment не bind-иться як прямий transformer parameter.

Отже:

```text
historical FEXPR:
  raw + explicit caller-env + direct-value

current TRANSFORMER:
  raw + no direct caller-env input + form-re-eval
```

Вони ділять raw-call axis, але різняться context exposure та result protocol:

```text
TRANSFORMER-RELATION=ORTHOGONAL
```

Це classification protocol, а не ranking expressiveness.

## Non-conclusions

D5/D6 width із cube не випливає.

Coordinate не призначається.

Historical property-list tags FEXPR/FSUBR — provenance mechanism, а не binary
semantic authority.

Archived `00101 TRANSFORMER` лишається archived.

## Принцип

**Special-call semantics треба розкладати на observable dimensions; спільних
raw operands недостатньо, щоб злити два protocols в одну identity.**
