# External Oracle Task 2 — корекція плану

**Статус:** обов'язкове уточнення до `2026-09-12-external-oracle-telemetry.md`; для Task 2 ця нотатка має перевагу над суперечливими прикладами старого implementation plan. Архітектурна специфікація `docs/superpowers/specs/2026-09-12-external-oracle-telemetry-design.md` лишається authority.

## Причина

Під час pre-implementation review знайдено дві суперечності в Task 2 старого плану:

1. Специфікація ратифікує semantic ID `0104` як `Total[{…}]`, тоді як старий implementation sketch використовує `Plus[…]`.
2. Тест для `(/ (/ 5 6) (/ 8 7))` очікує `Divide[Fold[Divide, {5, 6}], Fold[Divide, {8, 7}]]`, хоча той самий sketch для двох аргументів генерує `Divide[left,right]`. Це не може бути одночасно правдою.

Незалежна Wolfram-перевірка 2026-09-13 підтвердила:

```text
Fold[Divide, {5, 6, 8, 7}] = 5/336
Fold[Divide, {Fold[Divide, {5, 6}], Fold[Divide, {8, 7}]}] = 35/48
Total[{}] = 0
Times[] = 1
```

## Канонічна проєкція Task 2

Adapter hardcode-ить лише скінченну semantic-ID → Wolfram projection:

| Semantic ID | Операція | Wolfram Language |
|---|---|---|
| `0104` | сума | `Total[{args}]` |
| `1001` | віднімання/заперечення | unary `Minus[x]`; для 2+ аргументів `Fold[Subtract,{args}]` |
| `1002` | добуток | `Times[args]` |
| `1003` | ділення/обернене | unary `Divide[1,x]`; для 2+ аргументів `Fold[Divide,{args}]` |

Нульова арність: `+ → Total[{}] → 0`, `* → Times[] → 1`; `-` і `/` з нульовою арністю — `unsupported`/arity error відповідно до мовного контракту.

## RED тести перед production-кодом

Перший test-only commit повинен вимагати щонайменше:

```rust
assert_eq!(
    translate_source("(/ 5 6 8 7)").unwrap(),
    "Fold[Divide, {5, 6, 8, 7}]"
);
assert_eq!(
    translate_source("(/ (/ 5 6) (/ 8 7))").unwrap(),
    "Fold[Divide, {Fold[Divide, {5, 6}], Fold[Divide, {8, 7}]}]"
);
assert_eq!(
    translate_source("(+ 1 2 3)").unwrap(),
    "Total[{1, 2, 3}]"
);
assert_eq!(translate_source("(+)").unwrap(), "Total[{}]");
assert_eq!(translate_source("(*)").unwrap(), "Times[]");
```

Також обов'язкові identity-тести: усі admitted surfaces semantic IDs `0104`, `1001`, `1002`, `1003` мають перекладатися однаково незалежно від spelling.

## Fail-closed межа

Перша версія translator допускає лише один top-level exact arithmetic AST. Inexact numbers, strings, numeric buffers, improper pairs, bare symbols, effects і semantic IDs поза таблицею повертають стабільний `Unsupported.code`; вони ніколи не апроксимуються й не стають `pass`.

## TDD порядок

1. Дочекатися повного GREEN Task 1.
2. Створити test-only RED для правил вище; production translator ще відсутній або `unimplemented!()`.
3. Підтвердити RED у GitHub Actions саме через відсутню реалізацію translator.
4. Реалізувати мінімальний recursive AST projection.
5. Підтвердити GREEN окремого xtask тесту і всього workspace CI.
6. Лише після цього переходити до `external-oracle export`.
