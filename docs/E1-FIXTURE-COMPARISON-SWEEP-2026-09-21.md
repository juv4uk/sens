# E1-FIXTURE-COMPARISON-SWEEP-2026-09-21

Статус: E1 (розблокувати main) — повний grep-sweep two-part comparison гейтів у
`tests/fixtures/*.lisp` **та в lib-сайтах, які ланка witnessing реально виконує**
(машиновий підклас). Обов'язковий артефакт до коміту E1 (власна настанова:
«репродукція знайшла одного свідка — гарантії, що він один, нема»).

## Метод

`grep -nE '\(\([<>]=?|\(\(=[^?]' tests/fixtures/*.lisp`
(виключено: `conformance.lisp`/`oracle-results.lisp`/`inventory.lisp` — дані,
не виконувані гейти; `=?` — семантична рівність, не числовий клас).

## Результат (всі сайти)

| Файл:рядок | Гейт | Стан | Дія |
|---|---|---|---|
| `persistent-vector-balance-witness.lisp:13` | `((< n 0) acc)` two-part | **LIVE, ламав main-CI** (0 truthy → порожній acc → `cdr` error) | **FIXED у E1** (тричастинна форма, expected 1/0) |
| `properties-helpers.lisp:18` | `((< n 2) n)` two-part (fib) | LIVE (завантажується `mccarthy.rs:978`); property `properties.lisp:29` `(>= n (+ (fib (+ h 2)) -1))` викликає `fib` з аргументом ≥2 | **DEFER → (Б)**: фікс змінює `fib` на справжні числа Фібоначчі → посилює межу AVL property → потребує окремої верифікації, поза мінімальним E1 |
| `postcore-peer-materialization-witness.lisp` (47,49,176,180,196,198,218,220,255,257,350,360) | тричастинні (expected 1/0) | OK | без змін (клас (L) для (Б)) |
| `linter.lisp:42` | рядок-дані (lint input sample) | DATA | без змін |

## Машиновий підклас: lib-сайти, що ланка реально виконує (знайдені при відновленні ланки)

Після фіксу vector-balance ланка розкрила дальші (Б)-клас-регресії в `lib/machine` —
ті самі 0-truthy пастки, яких, за аналогією з witness, не торкнулась міграція #613.

| Файл:рядок | Гейт | Прояв | Дія |
|---|---|---|---|
| `lib/machine/encoding/x86-64.lisp:563` (`x86-encode-setcc-r8`) | two-part `((> code 3) REX-гілка) (t …)` | exact-Q: `(> 0 3)`→0→truthy → **REX 0x40 емітувався для КОЖНОГО регістра** → обидва машинові witnesses fail `(expected (15 148 192)) (actual (64 15 148 192))` | **FIXED у E1** (тричастинна, expected 1/0; було безпечно в епоху t/()) |
| `lib/machine/admission/x86-64.lisp:239` (`x86-admission-disp8?`) | `(and (>= v -128) (<= v 127))` — результати comparison споживаються як truthiness | 0 truthy → **переповнення disp8 адмітувалося** (lea-overflow → `t` замість `()`) | **FIXED у E1** (helper `x86-admission-within-inclusive-integer-range?`, явні domains) |
| `…admission…:246` (`imm32?`), `:253` (`uimm8?`), `:260` (`rel32?`) | ті ж `and`-над-`>=/<=` | всі чотири range-гейти мали ту саму діру | **FIXED у E1** (спільний helper, 4 сайти) |
| `lib/machine/dispatch/native-first-coverage.lisp:40-44` (ledger рядок 2) | дані, не гейт | `(car (cons -1 3))` класифіковано `fallback-required` (`current-native-island-requires-u64-literals`), але planner тепер дає `native-plan` (imm64 підтримує негативні) → witness чесно падав | **FIXED у E1** (дані ledger приведені до спостереженого: class `car-cons-outside-native-literal-domain`, representative `(car (cons "native-limits" 3))`, reason `current-native-island-holds-all-exact-integers`) |

Підсумок: **два** (Б)-клас-регресії у живих lib-сайтах (setcc REX; 4 admission range-гейти) + **налedger** (data-drift). Примітка: `x86-admission-disp8?` та ін. мали явний коментар «fail closed» — тож це були живі баги, а не зміна наміру; (Б)-Правка 2 з `< =`-слота поверне цим сайтам початку форму `and` без правки коду.

## Фактичний доказ (before/after)

```
BEFORE: cargo run … persistent-vector-balance-witness.lisp
  → Error: cdr expects a non-empty list (на main, до фіксу)
AFTER:  cargo run … persistent-vector-balance-witness.lisp
  → (persistent-vector-balance-witness (status pass))
```

```
AFTER (всі фікси, локальний запуск): bash scripts/test-current-semantic-slice.sh
  → exit 0: 16/16 Lisp witnesses pass, 16/16 Rust test модулів ok
  (x86-64-instruction-set, machine-register-width, native-first-coverage-ledger
   — знову pass після машинових фіксів)
```

## Відповідальність за червоний main

Корінь — `b0917a45` (#613): прибрав 0.0⇒false hack (0 знову truthy, conformance
181/240), мігрував lib-сайти на 3-part, **пропустив witness-сайти** — рівно
помилка «список з пам'яті замість grep». Наслідок: main-CI червоний з `3f5f1b01`
(«Current Lisp-owned semantic witnesses»). Це ж підтвердження системності сім'ї
truthiness-пасток (witness, lib, генератори — три ланки, один корінь).