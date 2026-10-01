# #2181 — D5 transformer boundary witness

Статус: лише research.

## Поточний розклад

Живий macro-path уже використовує звичайні мовні здібності для більшості роботи:

```text
DEFINE
LAMBDA
побудова форм
EVAL
```

Особлива поведінка зосереджена у двох host-mechanism точках.

### 1. Матеріалізація transformer

`macro_substrate.rs` робить:

```text
Closure -> Macro
```

Це тимчасовий `make-macro` substrate, прямо описаний у `lib/macro.lisp`.

### 2. Raw-form режим виклику

Evaluator бачить `Value::Macro` до звичайного обчислення аргументів.
`apply_macro` далі робить:

```text
сирі Expr operands
 -> quote як data
 -> bind до параметрів transformer
 -> evaluate body transformer
 -> Value назад у Expr
 -> tail-evaluate expansion у caller environment
```

Існуючий conformance уже доводить, що різниця спостережувана: невикористаний
macro operand може містити undefined symbol і не повинен обчислюватися.

## Мінімальна D5-інтерпретація для фальсифікації

Ці дві host-точки можуть бути двома механіками **однієї semantic capability**:

> closure зі staged/raw-form режимом виклику.

Це підтримує кандидата:

```text
0010  LAMBDA       ordinary closure
00101 TRANSFORMER  staged/raw closure candidate
```

Якщо гіпотеза виживе, `DEFMACRO` лишається похідним:

```text
DEFINE name (TRANSFORMER params body...)
```

і окремі D5 identity для `make-macro`, `defmacro`, `apply-raw` чи
`macroexpand` не потрібні лише через історичний API.

## Чого witness не доводить

Він не доводить, що materialization та raw invocation семантично одна операція.
#2181 ще має порівняти one-capability і two-capability моделі.

Він не ратифікує `00101`.

## Відтворення

```sh
python3 scripts/research-2181-d5-transformer-boundary.py
```

## Принцип

**Стискай host mechanics тільки після доказу, що це одна мовна здібність.**
