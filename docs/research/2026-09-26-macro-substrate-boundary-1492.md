# #1492 — межа macro substrate без 257-ї функції

**Дата:** 2026-09-26  
**Статус:** research-only; production semantics unchanged  
**База:** current `sens` після #1468 / #1487 / #1460

## Питання

`defmacro` уже має точну функціональну ідентичність СЕНС:

```text
00001010
```

але поточний bootstrap досі використовує словесний callable `make-macro`, який **не має SENS**.

Треба відділити дві речі:

1. закон мови: макрос отримує raw forms і розгортається до оцінки аргументів;
2. runtime-механіку: зберегти closure так, щоб evaluator знав, що її треба викликати через macro path.

Друга річ необхідна реалізації. З цього не випливає, що їй дозволено ставати окремою словесною функцією мови.

## Факти current main

### 1. Macro — окремий runtime tag

У `Value` існують окремі:

```text
Value::Closure(Rc<Closure>)
Value::Macro(Rc<Closure>)
```

Evaluator розрізняє їх до оцінки аргументів:

```text
Value::Macro
    ↓
apply_macro(raw Expr arguments)
```

`apply_macro` навмисно quote-ить raw arguments замість їх оцінки.

Отже macro-tag зараз має реальне operational значення.

### 2. Macro tag не є звичайними Lisp-даними

`value_to_expr` відмовляється перетворювати `Value::Closure` або `Value::Macro` назад у executable source datum.

Тому поточна pure-Lisp частина не має вже наявного substrate-neutral data constructor, з якого можна самостійно відновити runtime macro tag.

### 3. `make-macro` — ordinary callable word

`macro_substrate::install` робить:

```text
environment.define("make-macro", Value::Builtin(...))
```

Наявні tests уже доводять, що цей binding:

- first-class;
- aliasable;
- ordinary-shadowable;
- callable зі source.

Тобто це не просто внутрішнє ім'я Rust helper-а.

### 4. Loader-only repair недостатній

У `lib/macro.lisp` є **два** leakage-рівні.

Перший — outer bootstrap:

```lisp
(make-macro <closure>)
```

Другий — важливіший: `defmacro` будує expansion, що містить quoted symbol `make-macro`, аби майбутнє визначення користувацького макроса виконало приблизно:

```lisp
(define name
  (make-macro
    (lambda (...) ...)))
```

Отже якщо loader просто сам перетворить початковий Closure -> Macro, user `defmacro` усе одно відновить словесний callable пізніше.

**Loader-only removal route: falsified.**

## Що вже доведено exact 00001010

Після #1487/#1460:

```lisp
(00001010 first-form (a b) a)
(first-form (00000001 ok) never-defined)
```

повертає `ok`: невикористаний argument не обчислюється.

Тобто exact 00001010 уже має правильний macro-call path. Проблема #1492 не в raw dispatch, а в тому, як створюється runtime Macro value для нових користувацьких macro bindings.

## Порівняння кандидатів

### A. Просто сховати `make-macro` у loader

**Результат:** недостатньо.

Причина: generated `defmacro` expansion продовжує потребувати constructor пізніше.

Класифікація: **route-falsified**.

### B. Автоматично призначити `make-macro` новий SENS

**Результат:** технічно можливо лише після окремої ратифікації мови.

Цей research не має права створювати нову функцію або займати слот. Автоматичне призначення лише для зручності Rust було б новою semantic authority.

Класифікація: **not-admitted / owner decision required**.

### C. Зробити macro-tag ordinary source datum

Поточний runtime не підтримує це: Closure/Macro не мають source reification через `value_to_expr`.

Реалізація такої моделі означала б новий substrate-neutral value/syntax contract, а не механічне прибирання helper-а.

Класифікація: **possible redesign, not a cleanup**.

### D. Exact `00001010` як єдиний language-visible вхід, host materialization як внутрішній mechanism

Це найвужча перспективна межа:

```text
source
  ↓
exact 00001010
  ↓
language-owned defmacro law
  ↓
host-only Closure -> Macro materialization
  ↓
Macro binding
```

У такій моделі host operation:

- не має surface name;
- не лежить в ordinary Environment;
- не може бути alias/shadow/call зі source;
- не отримує окремого SENS;
- існує лише як mechanism уже існуючої exact-функції 00001010.

Але current `lib/macro.lisp` law виражений як AST expansion через `make-macro`. Тому перед implementation треба окремо довести, як перенести саме **materialization boundary** під 00001010, не переписавши macro-definition meaning у Rust.

Класифікація: **preferred next experiment, semantics proof still required**.

## Рекомендована наступна фаза

Не робити production patch у #1492.

Створити окремий test-only prototype для кандидата D:

1. exact `00001010` лишається єдиним source entry;
2. arbitrary source не може отримати internal materializer;
3. user macro definition працює без lexical `make-macro`;
4. raw-argument / short-circuit witness лишається GREEN;
5. Ukrainian/other peer surfaces, якщо використовуються, лише маршрутизуються до того самого 00001010;
6. exact-code shadowing invariant #1468 не порушується;
7. host не містить SENS->name->meaning round trip.

Лише після такого witness можна вирішувати, чи candidate D справді mechanism-only, чи приховано переносить закон `defmacro` у host.

## RED-first evidence у цьому PR

`macro_substrate_boundary_1492.rs` містить:

- GREEN control: exact `00001010` уже зберігає raw arguments;
- ignored RED: ordinary session не повинна мати `make-macro` binding;
- ignored RED: `lib/macro.lisp` не повинна ні прямо викликати `make-macro`, ні генерувати quoted `make-macro` для майбутніх визначень.

Ці RED-и навмисно не виправляються research PR-ом.

## Висновок

Проблема не зводиться до назви helper-а.

Поточна архітектура має необхідну runtime-відмінність `Closure`/ `Macro`, але матеріалізує її через ordinary callable word поза закритим 256-function space.

Найменша чесна ціль — **прибрати callable word, не прибираючи необхідний mechanism**, і прив'язати цей mechanism до вже існуючого exact `00001010` лише після окремого семантичного доказу.
