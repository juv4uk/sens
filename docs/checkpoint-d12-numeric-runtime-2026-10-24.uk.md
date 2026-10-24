# Чекпоінт SENS — D12: від семантичного закону до фізичного виконання

**Відповідальний аватар:** Sūtradhāra (सूत्रधार) — з'єднує точні семантичні контракти з перевірюваними механізмами, не прирівнюючи наявність координати до викличності.

**Зріз:** 2026-10-24  
**Гілка:** `main` (без нових гілок)  
**Поточний кодовий зріз перед цим checkpoint-оновленням:** [0035f273ecc5f933c1f17906206da7c540feedf2](https://github.com/juv4uk/sens/commit/0035f273ecc5f933c1f17906206da7c540feedf2) (точний `main` HEAD перед checkpoint-комітом; повторно звірити SHA перед тестами).
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

**Статус доказу на момент checkpoint:** [Actions run 40095010070](https://github.com/juv4uk/sens/actions/runs/40095010070) для SHA `0035f273ecc5f933c1f17906206da7c540feedf2` має стан `queued`; це **NOT_VERIFIED**, не PASS. Rust `E0509` із D12 assertions виправлено у [a33b3dd](https://github.com/juv4uk/sens/commit/a33b3dd160bbd43caa4fcdf3713ea3640a763631) та [554336a](https://github.com/juv4uk/sens/commit/554336adc507d7cfc359ead6197c789f7462e17c); для SHA `e95a8e…` hosted Rust-крок уже пройшов, але повний CI не завершився. У старому run [40093997962](https://github.com/juv4uk/sens/actions/runs/40093997962) зміни D11 частот падали в парному шляху через невідомі `Text7` bindings: не передавалися `lib/d11-clojure-group-by.lisp` і `lib/d11-clojure-frequencies-unary.lisp`. Коміт [9663918](https://github.com/juv4uk/sens/commit/9663918ddcf52592a536977ab9bdcbc481e17589) передав залежності й Core4-профіль; [dc2ced7](https://github.com/juv4uk/sens/commit/dc2ced7af0cb93ebf238f1fe1e914a64af08c766) додав self-contained standalone T5M bundle з позитивним/мутантним очікуванням D1. Ці два зміни ще чекають повного CI на точному SHA. Окремий D11 list-equality позитив виправлено у [e95a8e1](https://github.com/juv4uk/sens/commit/e95a8e1611dbde8b98496d89bdbd15888a91a78b), але його фізичний повторний запуск також має бути підтверджено.

## Конкретні RED, які вже мають вузьку правку

Завершений старий CI [40091430393](https://github.com/juv4uk/sens/actions/runs/40091430393) не є фінальним свідченням про поточний HEAD. Rust-крок упав на `E0509` у трьох pattern-match у `crates/sens/src/eval/arithmetic.rs` (рядки старого SHA 319, 329, 338) і одному в `crates/sens/src/source_projection.rs` (рядок 406): з `Value`, що має `Drop`, намагалися перемістити `BinaryNumber`. У поточній лінії ці assertion-и змінені на borrowing (`ref`), перевірити результат у свіжому CI.

У тому самому старому run 4 із 162 SENS фізичних законів залишилися RED: `d10-empty-queue-positive`, `d10-empty-queue-mutant`, `d6-compose-flip-positive`, `d6-compose-flip-order-mutant`. Парний evaluator відхиляв D10 `0011000010` і D6 `001011`, оскільки явний Core4-профіль не передавався до фізичної гілки. Коміт [468b677](https://github.com/juv4uk/sens/commit/468b677302a21308c6cce95eea998ece28c2d2da) додає Core4 profile лише для цих конкретних позитивних/мутантних свідків; не трактувати це як загальну callability.

Наступний доказовий розрив виявлено у `scripts/execute_changed_lisp_t5m.sh`: два нові negative witnesses `tests/semantic/d11-srfi1-span-improper-suffix-negative.lisp` і `tests/semantic/d11-srfi1-break-improper-suffix-negative.lisp` не були включені до `negative_type_diagnostic`. Вони навмисно мусять закінчуватись Type `car expects a non-empty list`; без класифікатора runner обробляє очікувану помилку як звичайний успішний закон і дає RED. Додано точне відображення обох шляхів на чинний Type-діагноз у [коміті 20665aba](https://github.com/juv4uk/sens/commit/20665aba9766a79676a48db8d7780d95314a7ae2). Семантику SENS, expected error та перевірки не послаблено. CI run [40094934801](https://github.com/juv4uk/sens/actions/runs/40094934801) для цього коміту ще виконується; причину вважати остаточно закритою можна лише після його завершення без RED.

## Окремо підтверджені зміни після попереднього checkpoint

Коміти [a33b3dd](https://github.com/juv4uk/sens/commit/a33b3dd160bbd43caa4fcdf3713ea3640a763631) та [554336a](https://github.com/juv4uk/sens/commit/554336adc507d7cfc359ead6197c789f7462e17c) виправили D12 Rust assertions: `BinaryNumber` позичається через `ref` замість move з `Value` з `Drop`. Hosted Rust-крок для наступного знімка `e95a8e…` уже завершився `success` у run 40094605513.

Коміт [e95a8e1](https://github.com/juv4uk/sens/commit/e95a8e1611dbde8b98496d89bdbd15888a91a78b) усунув RED `d11-srfi1-list-equality-positive`: test data тепер формуються D4 `СПИСОК`, а improper tail — точним D1 `ні`, без припущення, що QUOTE над W7-текстом створює D3 пари. Mutant-свідок і алгоритм бібліотеки не змінювалися. Повний фізичний результат для цього коміту ще не підтверджений.

Новий D11 `знайти-перший-із-наявністю` і D11 SRFI-1 list-equality — окремі SENS-бібліотечні композиції. Вони не призначають жодних нових доменних координат і не доводять callability усіх D11-селекторів.

## Фізична інтеграція D11 частот у зміненому Lisp-раннері

Попередній CI повідомив `unknown Text7 binding` для `tests/semantic/d11-frequencies-key-order-law.lisp` і його мутанта, бо змінений-файловий раннер не завантажував справжні SENS залежності. Тепер `scripts/execute_changed_lisp_t5m.sh` явно передає `lib/d11-clojure-group-by.lisp` та `lib/d11-clojure-frequencies-unary.lisp` у paired mint/evaluator, використовує профіль `--core4-runtime` для парного й автономного маршруту та будує self-contained standalone `.sens` із тих самих визначень + закон/мутант. Позитив очікує D1 `1`; мутант — D1 `0`. Змінено тільки orchestration/фізичну комплектацію — бізнес-логіка залишається в SENS. Hosted PASS для цього точного HEAD ще не відомий.

## Картка доменів: не змішувати значення, резидентність і виконання

- **D1:** точний предикат — лише 0/1.
- **D2:** точна структура.
- **D3/D4:** ратифіковані базові механізми; їхні імена є проєкціями точних координат.
- **D5–D10:** доменні каталоги й окремі закони; повна резидентність сама по собі не доводить викличність кожного запису.
- **D11:** законно похідні селектори від допустимих D10-батьків; 512 математично виведених форм не означають 512 незалежних opcode.
- **D12+:** числова, а не функціональна драбина: D12, D24, D48, D96, D192, … . D12 має signed двійковий доповняльний код і діапазон −2048…2047. Його ратифікація не створює D12-каталог функцій і не доводить фізичного допуску T5M.

## Додатковий аудит D1–D11 на цю дату

Коміт [62ddd1bbf558f8ca6943758214b073f89c571b54](https://github.com/juv4uk/sens/commit/62ddd1bbf558f8ca6943758214b073f89c571b54) додає незалежну карту для 2 558 поверхонь `lib/domains/d1..d11.lisp`: 1 219 живуть під власним ім'ям, 22 — як примітиви, 1 — під іншим ім'ям, 520 віднесено до виконання композицією/селектором, 364 — навмисно відкладено, 432 — невизначені, 0 — доведено відсутні. Це класифікація поверхонь, а не 2 558 runtime-позитивів; старі CSV-кандидати в середовищі були відсутні, тому цей перерахунок не підтверджує точний склад попередніх кандидатів «заглушок».

Нове D11 визначення `знайти-перший-із-наявністю` у `lib/d11-srfi1-find-presence.lisp` повертає `(так значення)` або `(ні ())`, розрізняє знайдений D1 `ні` від відсутності та від структурного `()`, і використовує коротке замикання на правильному скінченному списку; це бібліотечна композиція, не новий opcode. Коміт [841d6fa](https://github.com/juv4uk/sens/commit/841d6fa1201329be3fca321ce4ae8f94df3d1861) та D11 пошкодженого хвоста свідки [0b16ee9](https://github.com/juv4uk/sens/commit/0b16ee9658239a96fa74c6eff743dfb63e9ea04c) / [d8475e3](https://github.com/juv4uk/sens/commit/d8475e3d09a2ceaa05efc3c8d724fefc4cfeaa8d) є новими програмами й fixtures; їхнє hosted виконання ще не підтверджено.

Парні фізичні перевірки потребують явного runtime-профілю: коміт [468b677302a21308c6cce95eea998ece28c2d2da](https://github.com/juv4uk/sens/commit/468b677302a21308c6cce95eea998ece28c2d2da) додав `--core4-runtime` для окремих D10 `черга-порожня?` і D6 `compose/flip` позитивних та мутантних програм. Це виправляє невідповідність профілю для конкретних фізичних свідків, а не надає загальну callability всьому D6/D10. Коміти [0b16ee9658239a96fa74c6eff743dfb63e9ea04c](https://github.com/juv4uk/sens/commit/0b16ee9658239a96fa74c6eff743dfb63e9ea04c) і [d8475e3d09a2ceaa05efc3c8d724fefc4cfeaa8d](https://github.com/juv4uk/sens/commit/d8475e3d09a2ceaa05efc3c8d724fefc4cfeaa8d) додають негативні свідки пошкодженого хвоста списку для гілок вибору та вилучення у D11 group-by; їхній hosted запуск ще треба підтвердити.

## Невирішений наскрізний ланцюг

1. **General source default — `crates/sens/src/source_projection.rs`:** загальна проєкція за замовчуванням лишається з мінімумом D24 для Core4 сумісності. Потрібне окреме рішення про переведення звичайного CLI/REPL на D12 і міграція числових коренів та Core4, без змішування D12/D24.
2. **Core and physical route:** D12 є допустимим у `BinaryNumber`, арифметичному Core, перевірених D6 ADD1/SUB1/NEG/INTEGERP та явному `sens-math-t5m` профілі. Codecs transport-ує точні D12 слова; paired test перевіряє source → exact word → Zig/T5M round-trip → SENS evaluator. Результат тесту ще має бути підтверджений на точному SHA. Типізований Zig `numeric_domains.zig` wide-carrier профіль лишається D24/D48/D96/D192 і не є тим самим шляхом, що загальний bit-granular T5M word transport.
3. **Hosted verification:** перевірити зелений результат саме для комітів/HEAD, які містять `e85e002`, `3be35be`, `e41700e` та D12 Core arithmetic. Якщо тест червоний — відтворити ID/expected/actual і виправляти першопричину; не оголошувати PASS тільки через наявність тесту або коміту.
4. **Semantic SENS coverage:** перевірити, що нові D12 закони відповідають owner-ratified контракту й не наділяють D11/D12 довільними callable opcode. Доменна ідентичність, нативне виконання та physical round-trip — три різні свідчення.

## Пріоритет наступного агента

Пріоритет 1 — довести до завершення [run 40094934801](https://github.com/juv4uk/sens/actions/runs/40094934801) для коміту `20665aba` і перевірити, що обидва нові improper-suffix свідки проходять як очікувана Type-відмова direct/paired/standalone, а не маскуються. Пріоритет 2 — перевірити [run 40094953967](https://github.com/juv4uk/sens/actions/runs/40094953967) на HEAD `b632395b`, включно з новими D11 list= та F11 presence свідками. Якщо будь-який крок RED — отримати журнал, зафіксувати ID/expected/actual і виправити першопричину. Лише потім переходити до D12 shared source/REPL floor та D1–D11 resident audit; успішний Rust-крок не є загальним PASS.

**Поточний статус:** D12 exact-domain/source-profile/bit-granular Zig-T5M path, D6 boundary tests, D10/D6 explicit Core4 paired profile і D11 SENS-композиції/свідки закомічені до `main`. Відомі root-cause fixes для Rust E0509, D11 list-equality test data та D11 frequencies dependencies/standalone carrier додані; їхній повний hosted статус для SHA `0035f273ecc5f933c1f17906206da7c540feedf2` — **NOT_VERIFIED**. CLI/REPL лишається D24-first; D6 ledger має 60/64 резиденти без механічного доказу; глобальна мета виконуваності всього D1–D12+ не закрита, release GO не оголошується.
