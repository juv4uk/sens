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

1. SENS не є «SENS-7». Канонічна модель — exact-width драбина D1…D8, де відповідні домени мають 1…8 бітів.
2. Кожен домен має власну бітність і власний закон. D7 = 7 біт — лише властивість D7, а не загальна бітність мови.
3. Bits<N> і DomainIdentity вже існують як точні носії ширини та доменної ідентичності. Не створювати паралельний semantic/type layer лише для зручності backend-а.
4. Не прирівнювати u8 до semantic width. Host storage, регістр, BRAM, байтова шина або enum — фізичні механізми; вони не змінюють exact domain identity.
5. Не робити u8-per-cell новою канонічною моделлю. Перш ніж оптимізувати physical representation, прочитати чинні exact-width carriers, domain laws і packing mechanisms.
6. #3185 — не benchmark усієї SENS. Він вимірює конкретний universal SENS wire AST decoder проти serde_json; результат не переноситься автоматично на D1…D8 або інші SENS paths.
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

## Live coordination context

A separate, parallel coordination effort (Codex as primary agent, OpenCode as reviewer) runs through `C:\Users\user\Documents\GitHub\docs` — read `docs/AGENT_MEMORY.md` there before assuming an area is untouched.

## Agent Guard

`lib/guard.lisp` + `knowledge/guard-reference.lisp` are the current executable/reference-bureau surfaces in this repo. Older M0 planning documents remain historical process evidence; do not let a dated “implementation not started” note override current Guard code/tests.

Guard decision semantics are Lisp-owned. The Rust boundary validates the exact `guard/1` protocol shape before a host trusts it. Host authorization (filesystem/TCP/process scopes) remains an embedding boundary and must not be self-grantable by the constrained Lisp program.

## NLP / Embeddings tooling (2026-08-22 snapshot)

For NLP tasks on the documented WSL setup, the historical prepared environment is `/home/agents/GitHub/FlagEmbedding/.venv/bin/python`; prepared indexes/config live under `/home/agents/GitHub/vault-semantic-mcp/`. Treat these absolute paths as environment-specific operational notes, not semantic authority; verify they still exist before depending on them.

Semantic classification / embeddings are hypothesis generators, not authority. Candidate clauses still pass through validation/advice/reasoning rather than being written directly into knowledge state.
