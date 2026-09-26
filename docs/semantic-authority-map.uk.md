# Карта семантичної влади sens (СЕНС)

Український супровід до `semantic-authority-map.md`. Це стислий current-only виклад; історичні моделі та старі назви зберігаються у своїх історичних документах і не стають чинною специфікацією.

## Одне правило

> Мова володіє функціональною ідентичністю та семантикою; runtime-и володіють механізмами й доводять відповідність.

Жоден Rust-файл, surface-написання, generated table, README, нотатка агента, benchmark або історичний план не може мовчки переважити ратифікований контракт СЕНС.

## Порядок влади

1. **`language-contract.lisp`** — Contract 9.0 і наступні ратифіковані версії. Повний простір функцій — рівно `00000000..11111111`.
2. **Ратифіковані contract/ADR-рішення у власній явно вказаній області.** Історичний ADR не переважає новіший контракт.
3. **Виконувані SENS-owned закони та conformance evidence.**
4. **Reference implementation — `crates/sens` і чинні `sens-*` consumers.** Rust є доказом реалізації та механізмом, а не власником значення.
5. **Незалежні субстрати та execution kernels** — FPGA, C/WASM, GraalVM, Common Lisp, Prolog, Datalog, CLIPS тощо. Вони можуть володіти native-механізмами й спостереженнями, але не значенням функцій СЕНС.
6. **Generated projections/reference** — похідні таблиці та документація, що не створюють нових identity або законів.
7. **Пояснювальна проза** — README, `docs/language-core.md`, tutorial-и.
8. **Історичні та процесні матеріали** — архівні плани, старі аудити й попередні назви реалізації.

Якщо нижчий рівень суперечить вищому — нижчий застарів до узгодження.

## Єдина функціональна ідентичність

У чинній мові є один функціональний простір:

```text
00000000
...
11111111
```

Функція — це самі рівно вісім бітів (`Sens8`). Слово, рядок, символ, enum-label, історичне ім’я примітива, opcode або backend selector не є другою function identity.

`lib/surface/semantic-registry.lisp` може містити необов’язкові людські/source написання, які механічно маршрутизуються до вже існуючого exact `Sens8`. Surface не володіє значенням і не може перетворитися на `name -> meaning -> SENS` або `SENS -> named identity -> law`.

Структурне значення `()` лежить поза простором 256 функцій.

## Core-профілі

Core1, Core2, Core3 і Core4 — це профілі законів над тим самим набором 256 SENS identities. Профіль може змінити закон, домен результату або допустимий механізм конкретної функції, але не її вісім бітів.

McCarthy/Lisp лишається важливою історичною та Core1-провенансною основою, але не є глобальною чинною function ontology.

## Bootstrap та evaluator-механізми

Не змішувати identity з mechanism.

Evaluator може мати локальні класи механізмів або тимчасові implementation labels для виконання вже вибраного exact `Sens8`. Такі labels не є функціями мови й не визначають значення. Залишковий named-mechanism debt на кшталт `NecessaryFormIdentity` явно відстежується у #1328 і не повинен описуватися як чинна semantic identity.

`crates/sens/src/eval/canon.rs`, generated dispatch, IR roles та host registries — механізми/проєкції, а не друга семантична влада.

## Назва проєкту й розширення

Чинна назва проєкту та репозиторію — **`sens` (СЕНС)**. `my-lisp` може лишатися в історичних документах і compatibility evidence, але не є current product identity.

Канонічне розширення джерела — **`.lisp`**. Підтримувані **`.sens`** і **`.сенс`** є лише source/UI зручностями й не несуть семантики.

## Терміни

```text
semantic authority       = ратифікований SENS contract + SENS-owned executable laws
function identity        = тільки exact Sens8
surface                  = необов’язкове source/UI routing metadata
mechanism                = спосіб виконання вже вибраного Sens8
reference implementation = crates/sens та чинні sens-* consumers
independent executor     = інший substrate/kernel із bounded conformance proof
```

## Межа host/kernel

Host або execution island може давати effects, observations, lifecycle та native computation. Сам факт реєстрації/наявності не надає йому семантичної влади.

Правильний напрямок:

```text
exact Sens8
    ↓
selected Core law / admitted mechanism
    ↓
executor або host mechanism
    ↓
producer-native observation
```

Host registration — це availability, не ordinary SENS admission. Назва kernel-а або opcode лишається mechanism data, а не функцією СЕНС.

## Правило документації

Чинний документ, що повторює contract-level факт, має посилатися на авторитетне джерело, а не створювати паралельну істину. Історичні документи можуть зберігати старі назви та старі моделі, якщо вони явно історичні.

Для входу в поточну архітектуру спочатку читати `CURRENT.md`. `docs/archive/**` є ненормативним за визначенням.
