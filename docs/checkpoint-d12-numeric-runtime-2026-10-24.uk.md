# Чекпоінт SENS — D12: від семантичного закону до фізичного виконання

**Відповідальний аватар:** Sūtradhāra (सूत्रधार) — з'єднує точні семантичні контракти з перевірюваними механізмами, не прирівнюючи наявність координати до викличності.

**Зріз:** 2026-10-24  
**Гілка:** `main` (без нових гілок)  
**Поточний кодовий зріз перед цим checkpoint-оновленням:** [d8475e3d09a2ceaa05efc3c8d724fefc4cfeaa8d](https://github.com/juv4uk/sens/commit/d8475e3d09a2ceaa05efc3c8d724fefc4cfeaa8d) (точний HEAD перед цим checkpoint-комітом; перевірити HEAD повторно перед виконанням).  
**Нормативне джерело:** `contracts/numeric-domains-ratification.lisp`, схема `numeric-d12-start-extension-1`  
**Робочий корінь:** [#6016](https://github.com/juv4uk/sens/issues/6016)

## Що реально змінилося

У `crates/sens/src/binary_number.rs` правило допустимої ширини змінено на ратифіковану родину D(12 × 2ⁿ). Точні 12-бітні слова тепер несуть власну ідентичність; однакові payload у D12 і D24 залишаються різними значеннями домену. Перехід та обмеження змішаних доменів перевіряє unit-test `d12_is_the_first_signed_numeric_domain_and_preserves_exact_boundaries`.

У `crates/sens/src/source_projection.rs` додано явний API `project_ukr_decimal_integer_literals_with_minimum_width(..., 12)`. Загальний wrapper і звичайний REPL/source шлях зберігають мінімум D24 для сумісності з Core4. Водночас спеціальна парна поверхня `crates/sens-cli/src/bin/sens-math-t5m.rs` тепер явно викликає цей API з мінімумом D12; вона не виводить домен із carrier ширини. Тести `explicit_d12_projection_keeps_signed_boundaries_and_widens_exactly` і `explicit_d12_projection_runs_same_domain_arithmetic_and_carries_without_wrap` покривають межі та точне зростання.

У `crates/sens/src/eval/arithmetic.rs` тест `core_runtime_d12_signed_arithmetic_and_ratio_are_exact` перевіряє Core-runtime: 2047 + 0 лишається D12; 2047 + 1 і −2048 − 1 розширюються до D24 без обгортання; 1/3 лишається точною D12-композицією; D12/D24 не змішуються; ділення на нуль відхиляється.

У `crates/sens/src/eval/d6_arithmetic.rs` вирівняно D6 ADD1/SUB1/NEG/INTEGERP із числовою межею D12+. Тест `d6_unit_arithmetic_admits_d12_and_promotes_signed_boundaries` покриває `D12(7) ± 1`, `2047 + 1 → D24(2048)`, `−2048 − 1 → D24(−2049)`, `NEG(−2048) → D24(2048)`, точний D12-дріб та `INTEGERP`. Це доказ лише для чотирьох конкретних D6-резидентів; решта D6 каталогу не оголошується callable.

Похідні D6 механізми `ADD1/SUB1/NEG/INTEGERP` тепер теж мають D12-свідок у `crates/sens/src/eval/d6.rs`: D12 `7±1`, обидві знакові межі й розширення D12→D24, а також точне дробове значення і `INTEGERP`. `scripts/check-numeric-domain-ratification.py` узгоджено з D12+ Core admission. Це додаткові цільові свідки, не доказ повного покриття D6/D10 або всієї драбини.

Наскрізну тестову ланку додано до `crates/sens-cli/src/bin/sens-math-t5m.rs`: `d12_edges_roundtrip_and_grow_through_zig_t5m_and_sens_math` перевіряє exact D12 → Zig/T5M round-trip → SENS evaluator; окремо є D12 sum/subtract/multiply, signed comparisons, exact ratios, divide-by-zero negative witness, змішана ширина й payload-mutant. У `research/zig-codecs/t5m.zig` є round-trip D12 меж і D12/D24 з однаковою величиною. Це стосується bit-granular T5M transport; `research/zig-codecs/numeric_domains.zig` лишається byte-aligned D24/D48/D96/D192 carrier і навмисно не є доказом D12 byte-carrier підтримки.

Для цього існуючого CI додано команду `cargo test --locked -p sens-cli --bin sens-math-t5m -- --nocapture` у `.github/workflows/ci.yml` (коміт [e85e002](https://github.com/juv4uk/sens/commit/e85e00242df5fc8a80f0893a390f730eec2c07ac)). Це доповнення чинного workflow, не новий workflow.

**Статус доказу на момент checkpoint:** combined commit `statuses` порожній. Actions API показує [run 40091984813](https://github.com/juv4uk/sens/actions/runs/40091984813) для SHA `d8475e3d09a2ceaa05efc3c8d724fefc4cfeaa8d` у стані `queued`; це **NOT_VERIFIED**, не PASS. Старіший [run 40091430393](https://github.com/juv4uk/sens/actions/runs/40091430393) на SHA `cc39a6f6afa6dab73dc0afe467959b7ebd7f8d48` мав failure на кроці Rust, але run лишався in-progress, а API логів повернув 404, тому коренева причина цього старого failure тут не підтверджена. Локальний clone/build не вдалося виконати в цій сесії через недоступний DNS до `github.com`.

## Картка доменів: не змішувати значення, резидентність і виконання

- **D1:** точний предикат — лише 0/1.
- **D2:** точна структура.
- **D3/D4:** ратифіковані базові механізми; їхні імена є проєкціями точних координат.
- **D5–D10:** доменні каталоги й окремі закони; повна резидентність сама по собі не доводить викличність кожного запису.
- **D11:** законно похідні селектори від допустимих D10-батьків; 512 математично виведених форм не означають 512 незалежних opcode.
- **D12+:** числова, а не функціональна драбина: D12, D24, D48, D96, D192, … . D12 має signed двійковий доповняльний код і діапазон −2048…2047. Його ратифікація не створює D12-каталог функцій і не доводить фізичного допуску T5M.

## Додатковий аудит D1–D11 на цю дату

Коміт [62ddd1bbf558f8ca6943758214b073f89c571b54](https://github.com/juv4uk/sens/commit/62ddd1bbf558f8ca6943758214b073f89c571b54) додає незалежну карту для 2 558 поверхонь `lib/domains/d1..d11.lisp`: 1 219 живуть під власним ім'ям, 22 — як примітиви, 1 — під іншим ім'ям, 520 віднесено до виконання композицією/селектором, 364 — навмисно відкладено, 432 — невизначені, 0 — доведено відсутні. Це класифікація поверхонь, а не 2 558 runtime-позитивів; старі CSV-кандидати в середовищі були відсутні, тому цей перерахунок не підтверджує точний склад попередніх кандидатів «заглушок».

Парні фізичні перевірки потребують явного runtime-профілю: коміт [468b677302a21308c6cce95eea998ece28c2d2da](https://github.com/juv4uk/sens/commit/468b677302a21308c6cce95eea998ece28c2d2da) додав `--core4-runtime` для окремих D10 `черга-порожня?` і D6 `compose/flip` позитивних та мутантних програм. Це виправляє невідповідність профілю для конкретних фізичних свідків, а не надає загальну callability всьому D6/D10. Коміти [0b16ee9658239a96fa74c6eff743dfb63e9ea04c](https://github.com/juv4uk/sens/commit/0b16ee9658239a96fa74c6eff743dfb63e9ea04c) і [d8475e3d09a2ceaa05efc3c8d724fefc4cfeaa8d](https://github.com/juv4uk/sens/commit/d8475e3d09a2ceaa05efc3c8d724fefc4cfeaa8d) додають негативні свідки пошкодженого хвоста списку для гілок вибору та вилучення у D11 group-by; їхній hosted запуск ще треба підтвердити.

## Невирішений наскрізний ланцюг

1. **General source default — `crates/sens/src/source_projection.rs`:** загальна проєкція за замовчуванням лишається з мінімумом D24 для Core4 сумісності. Потрібне окреме рішення про переведення звичайного CLI/REPL на D12 і міграція числових коренів та Core4, без змішування D12/D24.
2. **Core and physical route:** D12 є допустимим у `BinaryNumber`, арифметичному Core, перевірених D6 ADD1/SUB1/NEG/INTEGERP та явному `sens-math-t5m` профілі. Codecs transport-ує точні D12 слова; paired test перевіряє source → exact word → Zig/T5M round-trip → SENS evaluator. Результат тесту ще має бути підтверджений на точному SHA. Типізований Zig `numeric_domains.zig` wide-carrier профіль лишається D24/D48/D96/D192 і не є тим самим шляхом, що загальний bit-granular T5M word transport.
3. **Hosted verification:** перевірити зелений результат саме для комітів/HEAD, які містять `e85e002`, `3be35be`, `e41700e` та D12 Core arithmetic. Якщо тест червоний — відтворити ID/expected/actual і виправляти першопричину; не оголошувати PASS тільки через наявність тесту або коміту.
4. **Semantic SENS coverage:** перевірити, що нові D12 закони відповідають owner-ratified контракту й не наділяють D11/D12 довільними callable opcode. Доменна ідентичність, нативне виконання та physical round-trip — три різні свідчення.

## Пріоритет наступного агента

Пріоритет 1 — перевірити [Actions run 40091984813](https://github.com/juv4uk/sens/actions/runs/40091984813) для точного SHA `d8475e3d09a2ceaa05efc3c8d724fefc4cfeaa8d`; на момент checkpoint його стан — `queued`, тому немає підтвердженого PASS/FAIL. Для наступного коду/після checkpoint пуша дивитися новий run, прив'язаний до точного HEAD. Якщо RED, зафіксувати ID/expected/actual і виправити корінь. Локальні відтворення: `cargo test --locked -p sens --lib d12_signed_domain_preserves_identity_and_widens_without_wrap -- --nocapture`; `cargo test --locked -p sens --lib core_runtime_d12_signed_arithmetic_and_ratio_are_exact -- --nocapture`; `cargo test --locked -p sens-cli --bin sens-math-t5m -- --nocapture`; Zig-перевірка через чинну `zig test -lc research/zig-codecs/tests.zig` CI-команду. Пріоритет 2 — вирішити окрему міграцію звичайного CLI/REPL з D24 floor на D12, оновивши Core4/numeric roots і свідків без неявної коерції. Пріоритет 3 — розібрати 432 невизначені й 364 навмисно відкладені рядки surface-аудиту по доказах `file+line`; окремо просунути D6 ledger, де підтверджено тільки 4/64 резиденти (1 DIRECT_LAW +3 LOWER_DOMAIN_COMPOSITION; 60 лишаються MISSING), а також перевірити D10/D11 групування парними позитивними та мутантними SENS-свідками; D12 як число не є D12 функціональним кодбуком. Не додавати нових opcode, не змінювати D11 без його власного закону, не вводити decimal/host-number як семантичного посередника й не послаблювати чинні негативні свідки.

**Поточний статус:** exact D12 Core/source-profile/bit-granular Zig-T5M paired path, D6 boundary tests, D10/D6 explicit Core4 physical profiles та D11 proper-tail negative fixtures закомічені до `main`; тестові команди додаються до наявного CI. Runtime test result для точного HEAD `d8475e3d09a2ceaa05efc3c8d724fefc4cfeaa8d` — **NOT_VERIFIED**. Звичайний shared source projection/REPL лишається D24-first; повна мета «усі функціональні резиденти D1–D12+ доведені та придатні до release» НЕ виконана цим checkpoint, і release GO не оголошується. Звичайний shared source projection/REPL лишається D24-first; загальна мета «всі функції D1–D12+ доведені та придатні до release» НЕ виконана цим checkpoint, і release GO не оголошується.
