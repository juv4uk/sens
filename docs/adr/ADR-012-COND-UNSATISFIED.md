# ADR-012 — Канонічний COND завершується named failure при відсутності збігу

**Статус:** Прийнято  
**Дата:** 2026-09-20  
**Рішення:** власник проєкту ратифікував зміну одразу в `main`.

## Контекст

Після #217 канонічний `COND` my-lisp має клаузи `(query expected-result expression)`. Ця форма вже відмовилась від generic truthiness: обчислюється `query`, `expected-result` лишається даними, а тіло першої точної відповідності виконується вибірково.

До цього ADR вичерпання всіх канонічних клауз повертало `()`. Це змішувало дві різні спостережувані події: **дані Canon 0** і **відсутність відповідної гілки керування**.

Історичне свідчення узгоджується з розділенням. McCarthy 1960 визначав вичерпаний conditional expression як undefined; [LISP I Programmer's Manual, 1 March 1960](https://softwarepreservation.computerhistory.org/LISP/book/LISP%20I%20Programmers%20Manual.pdf) мав named error `A3 CONDITIONAL UNSATISFIED -EVCON-`. Це історичне обґрунтування, не джерело сучасної семантики my-lisp.

## Рішення

1. Канонічна клауза `COND` має рівно три поля: `(query expected-result expression)`.
2. Queries перевіряються зліва направо.
3. `expected-result` — дані й не обчислюється як код.
4. Виконується лише `expression` першої клаузи, де observed query result структурно дорівнює expected datum.
5. Якщо жодна канонічна клауза не збіглася, включно з порожнім `(cond)`, evaluator повертає `ErrorKind::UnsatisfiedConditional`.
6. Це **не** `InvalidForm`: форма синтаксично коректна, але не визначила значення для цього спостереження.
7. Якщо форма містить хоч одну історичну двочленну `(test expression)` клаузу, вона лишається migration-only compatibility path і тимчасово зберігає попередню truthiness/no-match-`()` поведінку. Новий код не повинен спиратися на цей bridge.
8. my-lisp expected-result matching є власним розширенням і не приписується Маккарті.

## Наслідки

- Contract піднімається до **8.0**, бо раніше коректна канонічна форма могла спостерігати `()`, а тепер спостерігає named failure.
- `()` лишається Canon 0; воно може бути явно зіставлене як expected datum і більше не використовується канонічним `COND` як неявний sentinel вичерпання.
- Native evaluator і `lib/meta-eval.lisp` мають однаково розрізняти `InvalidForm` та `UnsatisfiedConditional`.
- Старий двочленний шлях не стає семантичною владою; це лише обмежений міграційний адаптер.

## Докази

- John McCarthy, *Recursive Functions of Symbolic Expressions and Their Computation by Machine, Part I* (1960): https://www-formal.stanford.edu/jmc/recursive.pdf
- *LISP I Programmer's Manual*, March 1, 1960: https://softwarepreservation.computerhistory.org/LISP/book/LISP%20I%20Programmers%20Manual.pdf
- John McCarthy, *History of Lisp* (1978): https://www-formal.stanford.edu/jmc/history/lisp/lisp.html
- Executable witnesses: `tests/fixtures/control-dispatch-v1.lisp`, `tests/fixtures/conformance.lisp`, `crates/my-lisp/tests/meta_eval_errors.rs`.

## English summary

Canonical three-part `COND` is ordered explicit-result dispatch. Exhaustion is now the named `UnsatisfiedConditional` failure, not NIL. Malformed clauses remain `InvalidForm`; the historical two-part truthiness path is compatibility-only.
