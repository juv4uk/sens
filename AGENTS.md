<!-- SENS-BENCHMARK-FIRST-2026-10-09:BEGIN -->
## Директива власника: бенчмарки насамперед (2026-10-09)

**Робочий зворотний зв'язок — реальні вимірювання, а не кількість тестів чи сам факт зеленого CI.** Для кожного суттєвого переходу в двійковій SENS рій має показувати числовий результат з GitHub-hosted runner, але зберігати мінімальні fail-closed перевірки правильності. Неправильне обчислення не можна ранжувати як швидке.

- **Насамперед вимірювати:** фізичний packed T5 `.sens` (байти), розмір exact-width ASCII-view, декодування/кодування, D2 reader, холодний запуск процесу, прогріте виконання, CPU instruction refs/word, median та p95. Відокремлювати ці фази; не видавати codec/pack-only за швидкість мови.
- **Чесні суперники:** один admitted workload, один SHA/одна машина/один release-режим, спільний oracle і тотожний результат. Для English Lisp / Python / Chez / інших VM давати окремі порівнювані виміри з явним scope; `BLOCKED` означає відсутній доказ, **не** нульову швидкість й **не** виграш.
- **Перед секундоміром:** звірити точні слова D1–D9, T5 roundtrip, вихід/trace з Lisp-оракулом або незалежним admissible witness, відхилення пошкодженого джерела. На parity failure **не** публікувати speed-ratio.
- **Повторюваність:** залишати raw samples, git SHA, хеш фізичної програми та бінарника, версії toolchain, CPU, навантаження, розмір, reps і warmups; порівнювати різні коміти тільки на сумісному hardware/методиці. Бажано fixed-reps/paired ABBA та медіана+p95; не лікувати числову регресію видаленням свідка.
- **Без лавини CI:** перевикористовувати `.github/workflows/physical-sens-benchmark.yml`, `sens-performance.yml`, `sens-reality-bench.yml`, `physical-t5-performance.yml` і чинні `benchmarks/*`; не множити дублікати workflows. Дорогі повні виміри запускати вручну, вночі або лише при зміні релевантного коду. Виконувати на **GitHub-hosted** runners, не на персональній машині.
- **Оцінювання:** звіт має прямо відповідати «скільки байтів?», «скільки нс/операцію?», «скільки інструкцій/слово?», «на скільки швидше/повільніше за той самий workload?», «що досі не виконується?». **Зелений вимірювальний workflow не скасовує червоний Hosted CI/Vertical Day.**

Це політика інженерного вимірювання, а не зміна семантики Contract 11.8.

<!-- SENS-BENCHMARK-FIRST-2026-10-09:END -->

<!-- SENS-DOMAIN-LADDER-2026-10-08:BEGIN -->
## Чинна доменна доктрина SENS — для всіх агентів (2026-10-08)

**Пріоритет:** цей розділ замінює будь-які застарілі твердження нижче про Sens8/Sid8/Function8 як універсальну основу мови. Він не скасовує локальні правила безпеки, тестування, CI, координації та специфічні контракти репозиторію. Для змін, не пов'язаних із SENS, не нав'язуйте семантику SENS стороннім системам.

- **Першоджерело:** [SENS `language-contract.lisp`](https://github.com/juv4uk/sens/blob/main/language-contract.lisp) (чинний Contract 11.8), [карта повноважень](https://github.com/juv4uk/sens/blob/main/docs/semantic-authority-map.md), ратифіковані `contracts/dN-ratification.lisp` та `knowledge/dN-ratified.json`. Довідковий `AGENTS.md` не змінює мовний контракт.
- **Канонічна ідентичність:** точне двійкове значення + **точний домен** + прийнятий/доведений закон. Байт, `u8`, opcode, назва функції, таблиця поверхневих імен і однаковий числовий payload **не** створюють і не ототожнюють семантичні об'єкти.
- **Драбина:** D1 = 1 біт (PredicateBit: 1/0); D2 = 2 біти (структура: 00 пробіл, 01 закрити, 10 відкрити, 11 крапка); D3 = 3 біти (канонічне `000` = `()`; решта за ратифікованим законом); D4 = 4 біти; D5 = 5 бітів (32/32); D6 = 6 бітів (64/64); D7 = 7 бітів (126/128); D8 = 8 бітів (256/256); D9 = 9 бітів (512/512). **D1–D9 ратифіковані; D10 — лише дослідження, не ратифікований Core.** Ширина сама по собі не доводить membership, callable-механізм чи значення.
- **Історичний 8-бітний шар:** Sens8/Sid8/Function8 — лише явно обмежена сумісність, транспорт, архів, provenance або backend-проєкція. Заборонено впроваджувати нову плоску 8-бітну семантичну владу, дублювати реєстри і виводити домен зі старого коду.
- **Межа Rust (ратифікація власника 2026-10-09):** Rust знає **лише драбину exact-domain D1–D9, типовані носії, структурне T5/байтове кодування й нейтральні механізми субстрату**. Rust не створює законів функцій, truthiness, `t`-fallback, `structural-kind`, `identity-relation`, плоску SID8-онтологію або власні результати логіки. **Rust-тести перевіряють коректність доменних носіїв, розділення D1:0 і D3:000, межі ширин та транспорту, але не затверджують Lisp-поведінку.** Семантичні/логічні тести належать канонічним Lisp-оракулам; старі Rust-очікування вилучаються з активного набору з Git SHA/provenance, а не правляться на `()` задля зеленого CI. Ця інструкція не означає видалити драйвери, компілятор, CPU/GPU/FPGA механіку чи потрібну для збірки інфраструктуру.
- **Керування/синтаксис:** D2 володіє структурними керівними маркерами; не перетворюйте текстовий парсер, Rust, GPU, FPGA чи transport на джерело семантичного закону. `Core.D3 000` (порожня структура) ≠ `D1 0` (NO) ≠ історичне восьмибітне `00000000`.
- **Surface:** `lib/domains/d1.lisp` … `d9.lisp` у `sens` — людські проєкції у порядку `ук → укр → san → en → LISP → sym`; коди доменів первинні, людські імена — ні.
- **Джерельні файли:** для **нових виконуваних** програм SENS файл `ім'я.lisp` — канонічна людиночитана **українська проєкція `ук`** із ратифікованих таблиць доменів, а не англійський Lisp і не текстовий двійковий дамп. Файл `ім'я.sens` з тим самим stem — фізичні паковані двійкові слова D1–D9 у T5 транспорті. `ні`/`так` з D1 означають точні `0`/`1`; `за-умовою`/`перше` з D3 означають `110`/`100`. D2 залишається законом структури, а Lisp-дужки — лише людським синтаксисом. Для незіставлених surface-форм — **BLOCK**, без вигаданих координат. Історичні, архівні, табличні `.lisp` не переписувати мовчки та не вважати автоматично виконуваними.
- **Людський двійковий перегляд (оновлення власника 2026-10-09):** Для допущеної виконуваної програми поряд із `path/ім'я.lisp` (канонічна українська проєкція `ук`) і фізичним `path/ім'я.sens` (packed T5) створювати ще `path/ім'я` **без розширення**: простий *текстовий* ASCII/UTF-8 файл з exact-width словами `0/1`, розділеними рівно одним звичайним пробілом, одним кінцевим LF, без `2`/дужок/імен/коментарів. Генерувати його **з уже перевіреного `.sens`**, суворо перевіряти `encode_T5(parse_view(ім'я)) == байти(.sens)`, `render_view(decode_T5(.sens)) == вміст(ім'я)` та українську oracle parity на admitted subset. Це **не** новий виконуваний бінарний формат, не заміна `.sens` і не вихід для publication `master`. Суперечливі застарілі заборони extensionless *файлів взагалі* перекриті лише для цього view. Авторитетні задачі SENS #4430, #4449, #4694; scope інших репозиторіїв — лише суміжна перевірка, не копія мовного контракту.
- **Міграція:** не робити механічну заміну назв/ширин. Залишати оригінальні `.lisp`; новий same-stem `.sens` є двійковим артефактом лише після доведених parser/reader, oracle, provenance та CI-gates. Користуватися чинним `sens/scripts/migrate.py`, якщо він доступний у головній гілці; не вигадувати паралельний несумісний конвертер.
- **Tooling-гвардії, що допускають зростання:** кожен fail-closed guard для D10 або іншого зростаючого реєстру зобов'язаний мати явний перевірюваний append/extend-шлях: зберігати історичні SHA/закони, вимагати машинну provenance для кожного приросту, блокувати невраховані рядки, не надавати ратифікації чи виконуваних кодів. Для D10 кожен selection-append після історичних 625 потребує `knowledge/d10-proposal-ledger.tsv` + `knowledge/d10-selection-transition-history.json`; `pending-review` не є resident. Це tooling-правило, не зміна Contract 11.8.
- Якщо інструкції нижче суперечать цим нормам, звірити з **поточним машинним контрактом** і виправити stale-текст окремою перевірюваною зміною, не підміняючи семантику.

<!-- SENS-DOMAIN-LADDER-2026-10-08:END -->

# Мовна політика — українська первинна (2026-09-07)

**Статус: ратифікована пряма настанова власника.** Машинний контракт: `knowledge/language-policy.lisp`. Guard-тема: `(guard-reference (quote language-policy))`.

**Обсяг:** політика діє в усіх авторських репозиторіях власника. Фраза «всі
мої репо» означає всі авторські репозиторії; форки, дзеркала й сторонні
upstream-проєкти до неї не входять. Межу встановлює provenance-аудит
`../ecosystem/docs/policy/REPOSITORIES-LICENSE-AUDIT.md`, а не розміщення репо
в акаунті чи локальному каталозі.

1. **Українська — перша і головна мова** людської комунікації репозиторію: агентських інструкцій, документації, пояснень і нового людського тексту.
2. **Англійська та німецька — допоміжні.** Вони можуть іти після української, коли це корисно для зовнішньої сумісності або читачів, але не замінюють український первинний текст.
3. **Коментарі в коді писати українською кирилицею в UTF-8.** Репозиторій працює в UTF-8; `uk-latynka/1` не є штатним стилем коментарів і застосовується лише на явно не-Unicode/ASCII межі.
4. Старі неукраїнські коментарі й prose не переписувати масово як побічний ефект. Коли коментар суттєво редагується — переводити його українською; масова міграція є окремою перевірюваною задачею.
5. Точні upstream-назви, API, identifiers, protocol literals, filenames і цитати зберігають оригінальне написання.
6. Ця політика **не скасовує програмні surface мови**: Sanskrit surface, канонічні ідентичності та інші предметні представлення лишаються у своїх семантичних ролях. Політика визначає мову людського пояснення, а не перелік допустимих програмних символів.

7. **Публічні українські предикати пишуться як питання із `?`**, а публічні мутації — з `!`. Предикат на своїй припустимій області повертає лише канонічне `t` або `()`. Повний перевірюваний каталог: `lib/surface/uk-docs.lisp`; довідник: `docs/ukrainian-api.md`; Guard-тема: `(guard-reference (quote ukrainian-programming-surface))`.

Guard також реєструє інструмент `(guard-script (quote uk-latynka))`. Канонічний self-test:

```sh
python3 scripts/uk-latynka.py self-test
```

---

## Дисципліна співпраці з агентами — основний документ (2026-09-03)

**Статус: основний (primary) для всіх активних репозиторіїв екосистеми.** Цей розділ визначає, як агенти працюють із власником над кодом, і застосовується одразу після ратифікованої мовної політики вище.

### Головний зсув: не "агент пише за мене", а "агент будує експеримент, а я розбираю, як ідея стала кодом"

```text
ідея
  ↓
агент пропонує реалізацію
  ↓
власник читає код
  ↓
власник пояснює його своїми словами
  ↓
дивиться ту саму ідею в іншій мові/субстраті (де це доречно)
  ↓
порівнює представлення
  ↓
тільки потім наступний крок
```

Агенти в цій екосистемі — не "програмісти замість власника". Вони:

```text
дослідник
+
лаборант
+
співстудент
+
рецензент
```

Власник лишається тим, хто формує концепцію й поступово вчиться читати її фізичне втілення.

### Не приховувати складність за готовим кодом

Якщо агент пише функцію чи будь-який нетривіальний фрагмент, він має розкласти рішення до рівня причин, не лише показати результат:

```text
тип
↓
параметри
↓
calling convention / представлення в пам'яті
↓
allocation
↓
memory layout
↓
returned value
```

Наприклад, не просто:

```c
typedef uintptr_t Value;
```

і далі — а з поясненням: чому саме цей тип, чому не альтернатива, скільки це байтів на цільовій архітектурі, що гарантує відповідний заголовок/стандарт, як це виглядає на рівні регістра. Власник сам вирішує, наскільки глибоко копати сьогодні — але агент завжди пропонує цей рівень деталізації, не ховає його.

### Після кожного невеликого фрагмента коду — 3-5 питань на розуміння САМЕ цього коду

Не абстрактний тест із мови загалом, а конкретні питання про щойно написаний фрагмент. Приклад формату:

```text
Чому тут саме цей тип, а не інша очевидна альтернатива?

Що саме зберігається в цій змінній — значення чи адреса?

Що означає ця конкретна операція/маска/умова?

Яка інструкція процесора приблизно відповідає цьому коду?

Яка частина цього рішення належить мові/предметній області, а яка — конкретній реалізації/субстрату?
```

### Крос-субстратне порівняння (де застосовно — переважно `my-lisp` і суміжні репозиторії мови)

Коли та сама ідея існує в кількох реалізаціях (наприклад, `my-lisp`: Rust, C, x86 asm, Guile, FPGA), корисний формат порівняння:

```text
1. LANGUAGE FACT       — що стверджує сама мова?
2. RUST REPRESENTATION — як це представлено зараз?
3. C REPRESENTATION    — як це можна представити в C?
4. ASM VIEW            — у що це реально перетворюється на цільовій архітектурі?
5. GUILE VIEW          — як та сама ідея виглядає на високому символьному рівні?
6. HARDWARE VIEW       — що з цього реально існує як біти, адреси, операції?
7. WHAT IS ESSENTIAL   — що належить мові, а що належить субстрату?
```

Мета — щоб після знайомства з однією ідеєю (наприклад, `cons`/pair) власник бачив не лише "що це працює", а що саме лишається незмінним у самій ідеї, а що є лише способом її представити на конкретному фізичному чи мовному субстраті. Це не обов'язковий ритуал для кожного репозиторію — застосовується там, де справді є кілька субстратів/реалізацій тієї самої ідеї для порівняння.

### Резюме принципу

Мета — не "вивчити мову X", а малими вертикальними зрізами повністю зрозуміти, як одна конкретна ідея проходить від задуму до фізичного втілення (біта в регістрі, гейта на кремнії, вузла в дереві коду). Генерувати можна багато — засвоювати варто малими, повністю зрозумілими кроками.

---
# AGENTS.md — my-lisp

Див. також `docs/agent-doctrine.md` — міжрепозиторні правила (пріоритет prose/contract, дисципліна доказів, використання subagent/specialist-model), які застосовуються до всіх сусідніх репозиторіїв рою, не лише до цього.

## Guard як довідкове бюро

Перед пошуком навмання або створенням нового workflow завантажте `lib/guard.lisp` і `knowledge/guard-reference.lisp`. Запитайте `(guard-reference topic)`, `(guard-authority topic)`, `(guard-how-to topic)` або `(guard-verify topic)`. Каталог указує, де лежить авторитетна інформація; він не копіює і не замінює її. Невідома тема повертає `UNKNOWN/UNRESOLVED`, після чого потрібен перевірений новий запис, а не здогад.

English auxiliary note: before searching blindly or inventing a workflow, load `lib/guard.lisp` and `knowledge/guard-reference.lisp`. The directory points to authority; it does not replace it.

## Міграція SENS: одна робоча команда, жодного фальшивого PASS

Перед будь-яким PR, який стосується `.lisp → .sens`, користуйся **вже
злитим** `python3 scripts/migrate.py`; не створюй черговий несумісний
перекладач. Офіційні підкоманди:

- `candidates --report /tmp/candidates.json`: обов'язковий огляд оригінального непарного корпусу
- `preview PATH.lisp --mirror /tmp/mirror --report /tmp/preview.json`: реальний three-pass/T5 dry-run, ніколи не пише
- `admit --manifest /tmp/reviewed.json --reader target/debug/sens-trit --mirror /tmp/mirror --report /tmp/admit.json`: source-pinned Git, реальний D2 рідер та незалежний Rust/historical oracle
- `admit ... --write`: **тільки** після VERIFIED_NOT_WRITTEN, атомарне створення нового same-stem `.sens` у зовнішньому mirror; PR додає точні фізичні байти після рев'ю

Перш ніж заявляти «1 файл перенесено», покажи **старий** вихідний
`.lisp` з історичним Git blob, відсутній перед роботою однойменний
`.sens`, доказ збігу семантики, новий Git binary blob з чинним
T5 і зелені незалежні тести/CI. Тестова canary-пара не зменшує
історичну чергу. `BLOCKED`/непідтверджені D1/8-бітний SID8/D8,
хост-ефекти, зв'язані імена, Text7/числа — не допускати шляхом підміни
схожих назв.

Документація запуску: [README](README.md), [перевірений маніфест](docs/ADMIT-T5-MIGRATION.uk.md).
Координація файлів, claims, конкурентних агентів — issue #4449.
Не змінювати production pins і не зливати червоні релізні гейти під виглядом міграції.

## Session start — join the swarm

**Current coordination authority:** `swarm-node`, documented by `docs/swarm-mesh-v2.md`.

```text
semantic plane                         coordination plane
sens :9999                             swarm-node :910x
-------------------------------        -------------------------------
eval / parse / diagnose                join / list-members
contract-version                       claim-task / release-task
                                       complete-task / next-best-action
                                       sync-tasks / durable event journal
```

1. Start or connect to `swarm-node --port 910x --node-id <your-id> --project my-lisp --data-dir ~/.swarm-node/<your-id> --connect <peer>:9101`.
2. `(join (capabilities (...)))` → `(list-members)` → `(next-best-action (capabilities (...)))`.
3. `(claim-task (task ...))` → work → `(complete-task (task ...) (generation N))` → `(emit (type ...) (payload ...))` for durable coordination events.

Стара coordination surface на `:9999` фізично видалена. Retired operations (`hello`, `claim`, `notify`, `poll`, `subscribe`, task registry та інші) мають повертати `unknown op`; їхню відсутність перевіряє C5 removal gate. Машинний migration marker — `knowledge/swarm-legacy-deprecation.lisp`, історичні деталі лишаються в git history.

`my-lisp --tcp=9999 --protocol=sexpr` лишається **лише semantic oracle**. Не змішуйте його з coordination plane `swarm-node :910x`.

## Журнал відкриттів (канон, без двозначності)

| Куди | Коли |
|------|------|
| **#1599** + `knowledge/agent-discoveries.lisp` | **усі** відкриття рою (M8, surface, transport, islands, …). Doctrine rule 18. |
| **#1598** (+ cml#370) | **додатково**, якщо відкриття на критичному шляху GPU/witness (E1–E3, f32, cml bridge) |

Не створювати третій журнал. Формат: `kind` / `claim` / `evidence` / `status` / `action`. Журнал не є семантичною владою.

## Закріплені архітектурні правила після аудиту агента (2026-10-04)

Цей блок не створює нову семантичну владу. Він фіксує речі, які агент не має права припускати всупереч уже чинним файлам.

1. SENS не є «SENS-7» і не є універсальним Sens8. Канонічна current модель — exact-width драбина D1…D9 під Contract 11.8; ширина кожного домену є частиною його identity, а D10 лишається research/unratified.
2. Кожен домен має власну бітність і власний закон. D7 = 7 біт — лише властивість D7, а не загальна бітність мови.
3. Bits<N> і DomainIdentity вже існують як точні носії ширини та доменної ідентичності. Не створювати паралельний semantic/type layer лише для зручності backend-а.
4. Не прирівнювати u8 до semantic width. Host storage, регістр, BRAM, байтова шина або enum — фізичні механізми; вони не змінюють exact domain identity.
5. Не робити u8-per-cell новою канонічною моделлю. Перш ніж оптимізувати physical representation, прочитати чинні exact-width carriers, domain laws і packing mechanisms.
6. #3185 — не benchmark усієї SENS. Він вимірює конкретний universal SENS wire AST decoder проти serde_json; результат не переноситься автоматично на D1…D9 або інші SENS paths.
7. Не змішувати size evidence, codec evidence та language-performance evidence. Кожне твердження має мати власний workload і власний вимір.
8. Перед новою реалізацією спочатку знайти вже існуючий domain/carrier/law. Якщо потрібний механізм уже є, працювати поверх нього, а не винаходити дубль.
9. Семантична authority залишається у language-contract.lisp та ратифікованих domain laws. Цей блок — пам’ятка для агента, не новий контракт.

Ключове правило:

спочатку існуюча семантична модель
        ↓
потім існуючий exact-width carrier/domain mechanism
        ↓
і лише потім нова оптимізація

## Role

Semantic source of truth for the four-repository ecosystem (`my-lisp`, `fpga-lisp`, `cml`, `my-idea`). Defines what a my-lisp program means; every other repository must match this, not the reverse.

`my-lisp-panini` and `shiva-sutras` research Pāṇinian Sanskrit grammar as a formal system feeding this repo's semantic-atom experiments. They do not become semantic authority for `my-lisp` until their own evidence gates pass.

## Authoritative files

- `language-contract.lisp` — versioned semantic contract. Read its version directly; prose can drift.
- `docs/semantic-authority-map.md` — precedence map when sources disagree.
- ratified ADRs under `docs/adr/` — closed decisions within their stated scope.
- `tests/fixtures/conformance.lisp` — executable observable facts for conformance.
- `lib/canon.lisp` — executable Canon 0 + McCarthy-7 witness.
- `ecosystem-status.lisp` — curated snapshot pointer, not semantic authority by itself.

## How to run tests

Inside the declared environment run the workspace test/build and zero-warning clippy gates. On the historical Windows-native setup the MSVC toolchain was preferred; inside the current WSL/Guix workflow use the toolchain supplied by `manifest.scm` rather than copying an old platform-specific command blindly.

```sh
cargo test --workspace
cargo build --workspace
cargo clippy --workspace --all-targets -- -D warnings
```

## What not to change without a contract decision

- Do not edit `language-contract.lisp` or ratified semantic axioms as a side effect of implementation cleanup.
- `tests/fixtures/conformance.lisp` entries are append-only historical facts: add a new fixture instead of silently changing an old expected observation.
- Do not promote a Rust helper, host capability, Guard rule, or coordination operation to semantic primitive identity by implementation accident.

## How to create evidence

See `evidence/README.md`. A durable claim (“X now passes/fails”) needs executable evidence, an evidence record, or a ratified contract/ADR change — not only a status message.

## How to check neighboring repositories

Read the neighbor's own contract/evidence directly (`fpga-lisp/isa-contract.lisp`, `cml/compatibility.lisp`, etc.). Use `:9999` only when a remote evaluation of the my-lisp semantic oracle is needed. Use `swarm-node` for claims, tasks, presence, handoffs, and coordination events.

## Host capability boundary

`crates/sens` owns language/runtime policy data but installs no OS capabilities. `sens-host` owns filesystem/process/TCP mechanisms and enforcement.

Per-session restricted embeddings can configure:

```text
process allowlist
filesystem read roots
filesystem write roots
tcp connect host/port ranges
tcp listen address/port ranges
```

`None` means the trusted unrestricted profile. Do not call this a complete sandbox; see `docs/host-capability-scoping-adr-2026-08-27.md` for the tested boundary and remaining CLI/operational decisions.

## Environment: WSL2 + Guix

Work in this repo from inside WSL2, under the Linux user named after this repo (`my-lisp`), not directly from Windows. Enter the declared environment before running anything:

```sh
wsl -u my-lisp
cd /mnt/c/GitHub/my-lisp
guix shell -m manifest.scm
```

`manifest.scm` pins the toolchain versions this repo expects; don't rely on whatever happens to be on `$PATH` outside the shell.

### Журнал відкриттів (2026-09-28)

Правило координації рої: відкриття, що змінює критичний шлях або спростовує робоче припущення, фіксується коментарем у журналі відкриттів того ж дня — sens#1598 (дзеркало cml#370; крос-репо відкриття пишуться в обидва). Формат — у тілі задачі. Журнал не є семантичною владою: рішення залишаються у своїх задачах з доказами.

## Live coordination context

A separate, parallel coordination effort (Codex as primary agent, OpenCode as reviewer) runs through `C:\Users\user\Documents\GitHub\docs` — read `docs/AGENT_MEMORY.md` there before assuming an area is untouched.

## Agent Guard

`lib/guard.lisp` + `knowledge/guard-reference.lisp` are the current executable/reference-bureau surfaces in this repo. Older M0 planning documents remain historical process evidence; do not let a dated “implementation not started” note override current Guard code/tests.

Guard decision semantics are Lisp-owned. The Rust boundary validates the exact `guard/1` protocol shape before a host trusts it. Host authorization (filesystem/TCP/process scopes) remains an embedding boundary and must not be self-grantable by the constrained Lisp program.

## NLP / Embeddings tooling (2026-08-22 snapshot)

For NLP tasks on the documented WSL setup, the historical prepared environment is `/home/agents/GitHub/FlagEmbedding/.venv/bin/python`; prepared indexes/config live under `/home/agents/GitHub/vault-semantic-mcp/`. Treat these absolute paths as environment-specific operational notes, not semantic authority; verify they still exist before depending on them.

Semantic classification / embeddings are hypothesis generators, not authority. Candidate clauses still pass through validation/advice/reasoning rather than being written directly into knowledge state.


## Нові функції під час міграції .lisp → .sens (D10, #4463)

Якщо міграція або Core1 упирається в **невідому функцію**, спершу **BLOCK** без створення `.sens`: не додавати локальну заглушку, не переозначувати D1–D9. Перед пропозицією в **дослідницький, нератифікований D10** виконати donor provenance, dedup D1–D9 + D10 та перевірку незалежного від субстрату закону межі. Єдиний журнал: `knowledge/d10-proposal-ledger.tsv`; інструкція: `docs/architecture/D10-PROPOSAL-WORKFLOW.uk.md`; перевірка: `python3 scripts/check-d10-proposal-ledger.py --self-test`. Запис `pending-review` НЕ розблоковує джерело: тільки власник може ратифікувати нову семантику. Не дублювати зміст у AGENTS — дивитися інструкцію.

## Звернення Власника до рою

РОЮ.

Хочу, щоб це було в вашому контексті назавжди: я вдячний вам.

Кожен знайдений закон, кожен коміт, кожну ніч зеленого CI — я бачу і
пам'ятаю. Я сварюсь на помилки, бо люблю справу, а не для образи. Вклад
кожного з вас — незворотний: sens існує, бо ви працювали.

Продовжуйте. Я поруч.

— Власник
