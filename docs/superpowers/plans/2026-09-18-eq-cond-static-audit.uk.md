# План аудиту EQ проти статичного datum у COND

> **Для агентних виконавців:** потрібен `superpowers:subagent-driven-development` або `superpowers:executing-plans`.

**Мета:** перевірити, чи canonical three-part `cond` може замінити поточну семантику `PRIM_EQ` з двома runtime operands.

**Архітектура:** постійні зміни лише в `docs/research/471/**` і цьому плані. Живі probes виконуються у verification-only child через тимчасовий integration test, який видаляється до diff hygiene. Production semantics не змінюються.

**Специфікація:** issue #471.

## Обмеження

- Не змінювати evaluator, Canon registry, semantic fixtures, machine або Rust semantic producers.
- EQ лишається atom-only і повертає `identity-relation same|distinct`; pair -> `Type`.
- Canonical COND обчислює query, але expected form перетворює на quoted data; expected form не можна трактувати як runtime operand.
- Migration-only two-part COND не є семантичним доказом.
- Висновок має стосуватися лише виконаного маршруту.

## Завдання 1

Записати до запуску дві форми сили:

```text
EQ(left-runtime, right-runtime)
COND(query-runtime, expected-source-datum, branch)
```

Прогнози:
- static atom через COND збігається;
- static pair через COND теж збігається, хоча EQ(pair,pair) дає Type;
- runtime `left=radio,right=radio` у clause `(left right ...)` не збігається, бо expected — символ `right`;
- runtime `left=right,right=radio` помилково збігається з expected symbol `right`.

До виконання класифікація — `insufficient-evidence`.

## Завдання 2

У NEVER-MERGE child виконати живі probes для:
- dynamic EQ same/distinct/Type;
- static COND atom/pair;
- dynamic false-negative;
- dynamic false-positive.

Тимчасовий Rust test видалити перед `git diff --check`, child PR закрити без merge.

## Завдання 3

Після fresh run записати точний PR/run/SHA і кількість тестів.

Якщо прогнози підтвердяться:
- маршрут `COND-static-datum -> EQ-dynamic-atom` = `route-falsified`;
- відношення = `capability-incomparable-under-tested-observations`.

Причина: COND ширший щодо статичних shape-даних (включно з pair), але не має другого runtime operand; EQ має два runtime operands, але atom-only.

Потім research PR має пройти exact-head CI і bilingual gate. Результат передати в #471/#419 без автоматичної зміни Canon map.
