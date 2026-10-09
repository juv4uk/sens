# План реалізації одностороннього клапана скорочення Rust

> **Для агентів:** виконувати цей план покроково через відповідний workflow Superpowers. Не змішувати реалізацію клапана з міграцією конкретних Rust-сайтів.

**Мета:** примусово виконувати активне правило #299: у кожному PR Rust може тільки скорочуватися. Будь-який новий шлях `*.rs` або будь-який доданий рядок у `*.rs` має давати RED ще до звичайного CI.

**Архітектура:** GitHub Actions переносить лише факти diff у вигляді Lisp-даних. Lisp-програма формує іменований verdict, друга Lisp-програма fail-closed його виконує. Сам клапан не додає Rust і не залежить від семантичної класифікації. #304 окремо визначає, що треба зберегти перед видаленням Rust.

**Стек:** my-lisp `.lisp`, bash/GitHub Actions, метадані Git diff.

**Специфікація:** `docs/superpowers/specs/2026-09-17-host-semantic-one-way-valve-design.md`

## Глобальні обмеження

- Заборонений будь-який доданий рядок у `*.rs`.
- Заборонений будь-який новий шлях `*.rs`, навіть порожній файл.
- Чисте видалення Rust лишається допустимим кандидатом на GREEN.
- Реалізація #300 додає нуль рядків Rust і нуль нових `.rs` файлів.
- Shell лише переносить факти diff; allow/deny verdict належить Lisp.
- #115 лишається незалежним внутрішнім клапаном семантичної влади Rust-тестів.

## Завдання 1: RED-контракт і CI harness

Створити synthetic fixtures для: доданого Rust-рядка, нового `.rs`, replacement Rust і deletion-only Rust. Додати окремий PR-workflow, який збирає існуючий `my-lisp`, формує рядки `(rust-change "path" additions deletions status)` і викликає ще відсутні `scripts/rust-retirement-valve.lisp` та `scripts/rust-retirement-valve-enforce.lisp`.

RED має бути зафіксований саме через відсутність реалізації клапана. Під час переходу RED→GREEN не додається жоден Rust.

## Завдання 2: GREEN Lisp-owned verdict

Створити лише:

- `scripts/rust-retirement-valve.lisp`;
- `scripts/rust-retirement-valve-enforce.lisp`.

Політика:

```text
status = new                 -> violation
additions > 0                -> violation
additions = 0                -> продовжити перевірку
усі рядки пройдені           -> rust-retirement-ok
```

Verdict має бути іменованим:

```text
(rust-retirement-ok)
(rust-retirement-violation PATH ADDITIONS STATUS "diagnostic")
```

Enforcer має fail-closed завершувати CI для violation.

## Завдання 3: самоперевірка напрямків

Той самий Lisp-клапан повинен довести чотири напрямки:

- доданий рядок Rust відхиляється;
- новий `.rs` відхиляється навіть при нульовій кількості рядків;
- replacement Rust відхиляється, навіть якщо інший Rust одночасно видаляється;
- deletion-only Rust повертає `(rust-retirement-ok)`.

Для реального PR факти треба рахувати від `merge-base` до head, щоб новіші deletion-only коміти у `main` не виглядали як Rust additions у старішій гілці.

## Завдання 4: інтеграція і координація

- Перевірити всі відкриті PR зовнішнім клапаном.
- Rust-growing machine/backend PR зберегти, але заморозити для merge на час цього етапу.
- Дозволяти preservation-слайси типу #303/#308/#310 лише коли сумарний Rust diff має `additions = 0`.
- Локальний агент веде #304 inventory/reachability і deletion-only cleanup.
- Веб/інтеграційний агент веде #300, preservation-рішення для #301/#305 та exact-head merge readiness.

## Самоперевірка плану

- Зовнішній інваріант покритий.
- Безпечне збереження унікальних законів перед видаленням покрите.
- Реалізація не потребує нового Rust.
- Diagnostic verdict називає offending path та кількість additions.
- Семантична класифікація не може бути винятком із зовнішнього клапана.

**Керівне правило:** Lisp може рости. Необхідний старий Rust може тимчасово лишатися. Але на цьому етапі Rust тільки зменшується.
