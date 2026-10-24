# Чекпоінт SENS — D12: від семантичного закону до фізичного виконання

**Відповідальний аватар:** Sūtradhāra (सूत्रधार) — з'єднує точні семантичні контракти з перевірюваними механізмами, не прирівнюючи наявність координати до викличності.

**Зріз:** 2026-10-24  
**Гілка:** `main` (без нових гілок)  
**Поточний кодовий зріз:** [9c38e0430a945965070f97ba46860ca889519ca7](https://github.com/juv4uk/sens/commit/9c38e0430a945965070f97ba46860ca889519ca7) (прямі коміти до `main`; latest observed by the checkpoint update)  
**Нормативне джерело:** `contracts/numeric-domains-ratification.lisp`, схема `numeric-d12-start-extension-1`  
**Робочий корінь:** [#6016](https://github.com/juv4uk/sens/issues/6016)

## Що реально змінилося

У `crates/sens/src/binary_number.rs` правило допустимої ширини змінено на ратифіковану родину D(12 × 2ⁿ). Точні 12-бітні слова тепер несуть власну ідентичність; однакові payload у D12 і D24 залишаються різними значеннями домену. Перехід та обмеження змішаних доменів перевіряє unit-test `d12_is_the_first_signed_numeric_domain_and_preserves_exact_boundaries`.

У `crates/sens/src/source_projection.rs` додано явний API `project_ukr_decimal_integer_literals_with_minimum_width(..., 12)`. Загальний wrapper і звичайний REPL/source шлях зберігають мінімум D24 для сумісності з Core4. Водночас спеціальна парна поверхня `crates/sens-cli/src/bin/sens-math-t5m.rs` тепер явно викликає цей API з мінімумом D12; вона не виводить домен із carrier ширини. Тести `explicit_d12_projection_keeps_signed_boundaries_and_widens_exactly` і `explicit_d12_projection_runs_same_domain_arithmetic_and_carries_without_wrap` покривають межі та точне зростання.

У `crates/sens/src/eval/arithmetic.rs` тест `core_runtime_d12_signed_arithmetic_and_ratio_are_exact` перевіряє Core-runtime: 2047 + 0 лишається D12; 2047 + 1 і −2048 − 1 розширюються до D24 без обгортання; 1/3 лишається точною D12-композицією; D12/D24 не змішуються; ділення на нуль відхиляється.

Наскрізну тестову ланку додано до `crates/sens-cli/src/bin/sens-math-t5m.rs`: `d12_edges_roundtrip_and_grow_through_zig_t5m_and_sens_math` перевіряє exact D12 → Zig/T5M round-trip → SENS evaluator; окремо є D12 sum/subtract/multiply, signed comparisons, exact ratios, divide-by-zero negative witness, змішана ширина й payload-mutant. У `research/zig-codecs/t5m.zig` є round-trip D12 меж і D12/D24 з однаковою величиною. Це стосується bit-granular T5M transport; `research/zig-codecs/numeric_domains.zig` лишається byte-aligned D24/D48/D96/D192 carrier і навмисно не є доказом D12 byte-carrier підтримки.

Для цього існуючого CI додано команду `cargo test --locked -p sens-cli --bin sens-math-t5m -- --nocapture` у `.github/workflows/ci.yml` (коміт [e85e002](https://github.com/juv4uk/sens/commit/e85e00242df5fc8a80f0893a390f730eec2c07ac)). Це доповнення чинного workflow, не новий workflow.

**Статус доказу:** свідки закомічені, а їхній запуск зареєстрований у наявному CI; GitHub connector повернув порожні `statuses`/`workflow_runs` і не дав логу тестового виконання. Це **NOT_VERIFIED**, не PASS. Локальний clone/build не вдалося запустити в цій сесії через недоступний DNS до `github.com`.

## Картка доменів: не змішувати значення, резидентність і виконання

- **D1:** точний предикат — лише 0/1.
- **D2:** точна структура.
- **D3/D4:** ратифіковані базові механізми; їхні імена є проєкціями точних координат.
- **D5–D10:** доменні каталоги й окремі закони; повна резидентність сама по собі не доводить викличність кожного запису.
- **D11:** законно похідні селектори від допустимих D10-батьків; 512 математично виведених форм не означають 512 незалежних opcode.
- **D12+:** числова, а не функціональна драбина: D12, D24, D48, D96, D192, … . D12 має signed двійковий доповняльний код і діапазон −2048…2047. Його ратифікація не створює D12-каталог функцій і не доводить фізичного допуску T5M.

## Невирішений наскрізний ланцюг

1. **General source default — `crates/sens/src/source_projection.rs`:** загальна проєкція за замовчуванням лишається з мінімумом D24 для Core4 сумісності. Потрібне окреме рішення про переведення звичайного CLI/REPL на D12 і міграція числових коренів та Core4, без змішування D12/D24.
2. **Core and physical route:** D12 є допустимим у `BinaryNumber`, арифметичному Core та явному `sens-math-t5m` профілі. Кодеки переносить точні D12 слова, а paired test перевіряє фізичний шлях, проте його результат ще має бути підтверджений запуском на точному SHA. Загальний Zig `numeric_domains.zig` wide-carrier список залишається D24/D48/D96/D192; не ототожнювати його із загальним T5M word transport.
3. **Hosted verification:** перевірити зелений результат саме для комітів/HEAD, які містять `e85e002`, `3be35be`, `e41700e` та D12 Core arithmetic. Якщо тест червоний — відтворити ID/expected/actual і виправляти першопричину; не оголошувати PASS тільки через наявність тесту або коміту.
4. **Semantic SENS coverage:** перевірити, що нові D12 закони відповідають owner-ratified контракту й не наділяють D11/D12 довільними callable opcode. Доменна ідентичність, нативне виконання та physical round-trip — три різні свідчення.

## Пріоритет наступного агента

Пріоритет 1 — отримати реальний результат поточного CI для `9c38e043…` (включає `cargo test --locked -p sens-cli --bin sens-math-t5m -- --nocapture`) і, якщо RED, виправити точний корінь. Локальні відтворення: `cargo test --locked -p sens --lib d12_signed_domain_preserves_identity_and_widens_without_wrap -- --nocapture`; `cargo test --locked -p sens --lib core_runtime_d12_signed_arithmetic_and_ratio_are_exact -- --nocapture`; `cargo test --locked -p sens-cli --bin sens-math-t5m -- --nocapture`; Zig-перевірка через чинну `zig test -lc research/zig-codecs/tests.zig` CI-команду. Пріоритет 2 — вирішити окрему міграцію звичайного CLI/REPL з D24 floor на D12, оновивши Core4/numeric roots і свідків без неявної коерції. Пріоритет 3 — продовжити окремий аудит D1–D11 resident-level callable laws, включно з позитивними й негативними SENS-свідками; D12 як число не є D12 функціональним кодбуком. Не додавати нових opcode, не змінювати D11 без його власного закону, не вводити decimal/host-number як семантичного посередника й не послаблювати чинні негативні свідки.

**Поточний статус:** exact D12 Core/source-profile/bit-granular Zig-T5M paired path і негативні свідки закомічені до `main`; test command додана в чинний CI. Runtime test result — **NOT_VERIFIED**. Звичайний shared source projection/REPL лишається D24-first; загальна мета «всі функції D1–D12+ доведені та придатні до release» НЕ виконана цим checkpoint, і release GO не оголошується.
