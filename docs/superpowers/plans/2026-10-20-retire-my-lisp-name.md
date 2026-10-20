# Повне виведення старої назви — план реалізації

> **Для агентних виконавців:** обов'язковий підпроцес: `superpowers:executing-plans`. Виконуй завдання послідовно; кожне завершується власною перевіркою й окремим вузьким комітом.

**Мета:** зробити SENS єдиною чинною ідентичністю продукту й прибрати старі `my-lisp` CLI, активні машинні імена та виклики, не переписуючи історію.

**Архітектура:** зберегти package `sens-cli` і єдиний CLI target `sens`; послідовно перейменувати локальні публічні інтерфейси та їхні споживачі без compatibility alias. Міжрепозиторний експорт CML змінювати лише разом із його підтвердженим consumer-контрактом; не чіпати невідомі/незбережені зміни CML.

**Стек:** Rust/C ABI, Cargo, CMake, Guix, YAML/JSON manifests, SENS `.lisp` генератори.

**Специфікація:** [2026-10-20-retire-my-lisp-name-design.md](../specs/2026-10-20-retire-my-lisp-name-design.md)

## Глобальні обмеження

- `sens` — єдиний CLI target та єдине встановлюване ім'я програми.
- Підтримуваного старого alias, перенаправлення чи fallback не залишається.
- Git history, датовані свідчення, provenance та сторонні назви не переписуються.
- Перейменування не змінює семантику SENS, доменну identity, допуск до виклику, бітові коди чи T5M.
- Не виконувати remote deployment, зміну systemd-служб чи зовнішніх облікових записів.
- Не включати наявні зміни REPL/T5M до комітів цієї міграції.

## Фокус review

1. **Старий CLI зникає, але всі режими лишаються доступні.** Зафіксувати наявними чорними тестами `--help`, `--version`, oracle, файл, stdin і REPL через `sens` (Завдання 1).
2. **C ABI — публічна несумісна зміна.** Зафіксувати нову версію ABI та побудову реального C-consumer (Завдання 2).
3. **Старий islands manifest не проходить непомітно.** Позитивний тест нового протоколу й негативний тест старого (Завдання 3).
4. **CML pinned digest/consumer може відставати.** Звірити producer, контракт і тест у репозиторії CML до перейменування generated export (Завдання 4).
5. **Робочі/тимчасові workflow-и відрізняються від історичних згадок.** Перевірити реальні команди й наявність target/path, не робити глобальної механічної заміни (Завдання 6).

---

## Карта змінюваних вузлів

- `crates/sens-cli/Cargo.toml`, `crates/sens-cli/src/bin/my-lisp.rs`, `crates/sens-cli/tests/cli.rs`, `guix.scm`: прибрати дубльований CLI target та його встановлення.
- `crates/sens-embed/{src/lib.rs,include/my_lisp_embed.h,README.md,tests/static-consumer/*}`: перейти на `sens_embed_*`, SENS-типи/header і нову версію C ABI.
- `crates/sens-cli/src/islands.rs`, `crates/sens-cli/tests/{islands_cli.rs,islands_release_asset.rs}`, `packaging/islands-manifest-v1.json`, `tests/fixtures/islands-manifest-v1.json`: SENS-іменований wire protocol; файлова схема/поведінка не змінюється поза ідентичністю.
- `crates/sens-cli/src/bin/cml-export.rs`, generated `sens-cml-export.{lisp,wsm}`, `crates/sens-cli/tests/*`, `scripts/check_ukr_callsite_migration.py` та `cml` consumer: узгоджене перейменування semantic export і digest.
- `scripts/build-constitution.lisp`, `scripts/check_axiom_coverage.py`, `scripts/semantic-authority-guard.lisp`, `crates/sens-cli/tests/constitution_projection.rs`, generated `sens-constitution.lisp`.
- `scripts/check-current-authority-docs.sh`, `scripts/verify-repo.lisp`, поточні docs/tasks, активні `.github/workflows/*`, локальні CLI scripts: чинна назва та відсутність старих команд/target-ів.

### Task 1: прибрати дубльований CLI target

**Файли:**
- Modify: `crates/sens-cli/Cargo.toml`
- Delete: `crates/sens-cli/src/bin/my-lisp.rs`
- Modify: `crates/sens-cli/tests/cli.rs`
- Modify: `scripts/verify-repo.lisp`
- Modify: `guix.scm`
- Test: `crates/sens-cli/tests/cli.rs`

**Інтерфейси:** зберегти існуючу поведінку CLI у `sens`; прибрати лише старе ім'я виконуваного target.

- [ ] **Крок 1: розширити наявний repo guard** `cargo-workspace-has-no-my-lisp-package-prefix`, щоб він також відхиляв старий `[[bin]]` target у `crates/sens-cli/Cargo.toml`.
- [ ] **Крок 2: підтвердити червоний стан.** Запустити `target/debug/sens scripts/verify-repo.lisp`; після додавання нової умови вона має виявити наявний target `my-lisp`.
- [ ] **Крок 3: видалити alias.** Прибрати `[[bin]] my-lisp` і wrapper; у `cli.rs` замінити `legacy_bin()` на запуск `sens`, прибрати тест parity двох імен.
- [ ] **Крок 4: залишити behavior coverage на канонічному CLI.** Переконатися, що version/help/oracle/file/stdin/REPL тести запускають `CARGO_BIN_EXE_sens`.
- [ ] **Крок 5: перевести Guix.** Прибрати `--bin my-lisp`, його встановлення та опис compatibility CLI з `guix.scm`.
- [ ] **Крок 6: перевірити зріз.** `cargo test --locked -p sens-cli --test cli`; `target/debug/sens scripts/verify-repo.lisp`; `cargo metadata --no-deps --format-version 1` не показує старого target.
- [ ] **Крок 7: комітити лише цей зріз.** `git add` точних файлів завдання й окремий commit.

### Task 2: перейменувати C embedding API як один ABI break

**Файли:**
- Modify: `crates/sens-embed/src/lib.rs`
- Rename: `crates/sens-embed/include/my_lisp_embed.h` → `crates/sens-embed/include/sens_embed.h`
- Modify: `crates/sens-embed/README.md`
- Modify: `crates/sens-embed/tests/static-consumer/{CMakeLists.txt,main.c}`
- Test: unit tests у `crates/sens-embed/src/lib.rs` і C static consumer.

**Інтерфейси:** замінити публічні типи/символи `MyLispEmbed*`, `MY_LISP_EMBED_*`, `my_lisp_embed_*` на `SensEmbed*`, `SENS_EMBED_*`, `sens_embed_*`. Поточний ABI version `5` змінити на `6`; старі експортовані C символи не лишати.

- [ ] **Крок 1: додати перевірку ABI v6 і SENS-імен.** Перевірка Rust і C header повинна вимагати номер `6` та SENS-префікси.
- [ ] **Крок 2: перевірити червоний стан.** Поточні v5/старі імена мають порушити цю перевірку.
- [ ] **Крок 3: перейменувати Rust API та header послідовно.** Зберегти типи аргументів, layout, ownership, результати та поведінку ABI; змінити лише публічну ідентичність і версію.
- [ ] **Крок 4: перевести C consumer.** Оновити include, символи, CMake cache variable і назви executable на SENS.
- [ ] **Крок 5: перевірити.** `cargo test --locked -p sens-embed`; зібрати й запустити `crates/sens-embed/tests/static-consumer` за командою CI workflow `embed-staticlib.yml`.
- [ ] **Крок 6: комітити окремо** після успішного Rust і C-consumer тесту.

### Task 3: вивести стару назву islands wire protocol

**Файли:**
- Modify: `crates/sens-cli/src/islands.rs`
- Modify: `crates/sens-cli/tests/islands_cli.rs`
- Modify: `crates/sens-cli/tests/islands_release_asset.rs`
- Regenerate/update: `packaging/islands-manifest-v1.json`, `tests/fixtures/islands-manifest-v1.json`
- Test: `crates/sens-cli/tests/{islands_cli.rs,islands_release_asset.rs}`

**Інтерфейси:** канонічний протокол — `sens-islands-manifest/1`; старий `my-lisp-islands-manifest/1` відхиляється. File layout і семантика installer не змінюються.

- [ ] **Крок 1: додати позитивний тест нового protocol ID та негативний тест точного старого ID.** Старий ID має повертати `unsupported manifest protocol`.
- [ ] **Крок 2: підтвердити негативний тест на поточному decoder.** Старий ID наразі приймається; тест мусить упасти через прийняття старого формату.
- [ ] **Крок 3: оновити validator, release asset і fixtures** на `sens-islands-manifest/1`.
- [ ] **Крок 4: запустити** `cargo test --locked -p sens-cli --test islands_cli --test islands_release_asset`.
- [ ] **Крок 5: комітити окремо** після проходження обох protocol тестів.

### Task 4: перенести CML semantic export і його consumer разом

**Файли SENS:**
- Modify: `crates/sens-cli/src/bin/cml-export.rs`
- Rename/update: root `mylisp-cml-export.lisp` → `sens-cml-export.lisp` і `mylisp-cml-export.wsm` → `sens-cml-export.wsm`
- Modify: export artifact tests, `scripts/check_ukr_callsite_migration.py`, чинні індекси/документи export

**Файли CML consumer (окремий репозиторій):**
- Rename/update: `contracts/mylisp-cml-export.lisp` → `contracts/sens-cml-export.lisp`, `src/semantic_export.rs`, `tests/semantic_export_slice1_test.rs` у `/home/agents/GitHub/cml`.
- Не змінювати наявні незбережені файли CML, доки їхній автор/призначення не встановлено.

**Інтерфейси:** один погоджений SENS шлях і digest; жоден consumer не читає старий шлях як alias.

- [ ] **Крок 1: зафіксувати поточний producer byte output та consumer digest** окремими цільовими тестами; не оновлювати digest вручну.
- [ ] **Крок 2: до перейменування узгодити обидва репозиторії.** У CML наявні незбережені файли; спочатку визначити їхнього автора й перетин, не перезаписуючи їх. Сповістити активного CML-агента, якщо він є.
- [ ] **Крок 3: перейменувати producer output на `sens-cml-export.{lisp,wsm}`**, regenerate producer output; обчислити новий digest самим producer.
- [ ] **Крок 4: в одному узгодженому зрізі перевести CML consumer, `contracts/sens-cml-export.lisp` та pinned digest** на нове ім'я; не змінювати семантичний payload.
- [ ] **Крок 5: підтвердити обидві сторони.** `cargo test --locked -p sens-cli --bin cml-export` для producer; `cargo test --locked --test semantic_export_slice1_test` у CML для consumer; старий шлях не має бути відкритим fallback.
- [ ] **Крок 6: комітити окремо в кожному репозиторії**, лише після перевірки staged diff кожного.

### Task 5: перейменувати згенеровану конституцію та актуальні guard-и

**Файли:**
- Modify: `scripts/build-constitution.lisp`, `scripts/check_axiom_coverage.py`, `scripts/semantic-authority-guard.lisp`
- Rename: `my-lisp-constitution.lisp` → `sens-constitution.lisp`
- Modify: `crates/sens-cli/tests/constitution_projection.rs`, `tasks.lisp` (лише чинні незавершені records), актуальні README/authority docs
- Test: `crates/sens-cli/tests/constitution_projection.rs`; `scripts/check-current-authority-docs.sh`; repo verification gate.

**Інтерфейси:** authority inputs лишаються `tests/fixtures/conformance.lisp` і генератор; generated SENS projection зберігає байтову детермінованість та рівень authority.

- [ ] **Крок 1: оновити projection test**, щоб вимагав SENS output path і ловив посилання генератора/guard-ів на старий активний шлях.
- [ ] **Крок 2: підтвердити RED:** старе ім'я output зараз задовольняє test; нова очікувана назва відсутня.
- [ ] **Крок 3: перейменувати output на `sens-constitution.lisp` та всі live consumers** і згенерувати файл чинним `sens` CLI, не редагувати generated projection вручну.
- [ ] **Крок 4: оновити guards** так, щоб вони перевіряли актуальну назву SENS і дозволяли тільки контекстні історичні згадки.
- [ ] **Крок 5: oracle-перевірити змінені `.lisp` файли через `target/debug/sens --oracle-check <file>`; потім перевірити.** `cargo test --locked -p sens-cli --test constitution_projection`; `scripts/check-current-authority-docs.sh`; `target/debug/sens scripts/verify-repo.lisp`.
- [ ] **Крок 6: комітити generator, generated file, consumers і guards одним coherent commit.**

### Task 6: перевести активні CI та локальні інструменти, не переписуючи архів

**Файли:** `scripts/*.py`, `scripts/*.sh`, активні `.github/workflows/*.yml`, поточні docs та `tasks.lisp`.

**Інтерфейси:** команди використовують наявні Cargo package/target-и; активні описи називають продукт SENS. Історичні task completion і evidence не змінюються.

- [ ] **Крок 1: скласти tracked inventory** старих імен у командах `run:`, build/install кроках, shell scripts і незавершених task records; для кожного записати рішення `migrate`, `retire` або `historical/foreign` у review diff/координаційному звіті, не додаючи окремий артефакт без потреби.
- [ ] **Крок 2: не додавати загальний regex-тест лише для числа збігів.** Перевірити живі entrypoints наявними Cargo, Guix, CI та repo guards; окремий регресійний тест додавати лише для конкретного активного інтерфейсу, який інакше не має перевірки.
- [ ] **Крок 3: підтвердити RED** на виявлених командах `--bin my-lisp`, `-p my-lisp-cli`, і `target/debug/my-lisp`; класифікувати кожне джерело як активне чи історичне перед виправленням.
- [ ] **Крок 4: перевести валідні live сценарії на `sens`/`sens-cli`;** невалідні workflow-и з посиланнями на неіснуючі `crates/my-lisp` не переписувати навмання: вимкнути/видалити лише після перевірки їхнього призначення та відсутності актуального доказу.
- [ ] **Крок 5: змінити guards і current docs** на SENS-first; живий текст про минуле лишити лише як явну історію.
- [ ] **Крок 6: запустити shell/YAML/static guards і всі нові цільові перевірки;** не запускати повні GitHub Actions workflow-и.
- [ ] **Крок 7: комітити зрізами**: чинні інструменти, CI, актуальні docs/tasks — окремі коміти.

### Task 7: перевірити повну міграцію та залишкові згадки

**Файли:** tracked repo inventory; за потреби невеликий allowlist лише для незмінної provenance/чужих назв.

- [ ] **Крок 1: виконати пошук у tracked файлах** для `my-lisp`, `my_lisp`, `mylisp` і списку старих ABI/protocol/artifact символів.
- [ ] **Крок 2: класифікувати кожен залишок за файлом і причиною.** Усі активні команди, export symbols, wire IDs і current identity мають бути відсутні; не додавати великі blanket allowlist-и.
- [ ] **Крок 3: перевірити Cargo/Guix/ABI/islands/export/constitution acceptance commands** із попередніх завдань.
- [ ] **Крок 4: `git diff --check`;** цільовий build/test лише після `docs/agent-coordination/AGENT-RESOURCE-POLICY.md` і `wsm-agent bench-ready`, якщо workload виходить за межі коротких цільових тестів.
- [ ] **Крок 5: review повного diff** на відсутність зміни семантики, доменів, T5M, сторонньої історії та незбережених змін інших агентів.
- [ ] **Крок 6: зафіксувати фінальний commit SHA в координації**; push до `main` лише після синхронізації з актуальним `origin/main` і перевірки fast-forward.

## Самоперевірка плану

- **Покриття:** CLI/Guix — Завдання 1; C embedding — 2; islands protocol — 3; CML export — 4; generated constitution/guards — 5; CI/scripts/docs — 6; контроль залишків і фінальні докази — 7.
- **Кроки:** кожен тест спершу додається/оновлюється й має визначений RED; зміни й перевірки відокремлені по вертикальних зрізах.
- **Інтерфейсна узгодженість:** CLI лишається `sens`; embedding API — `sens_embed_*`, ABI v6; islands — `sens-islands-manifest/1`; export — `sens-cml-export.{lisp,wsm}` з consumer `contracts/sens-cml-export.lisp`; constitution — `sens-constitution.lisp`.
- **Найбільший ризик:** CML має власні локальні незбережені untracked тести. Завдання 4 зупиняє перейменування export до власницької класифікації та узгодження, не перезаписує ці файли.
- **Пропорційність:** сім незалежно перевірних комітів покривають несумісний CLI/API/protocol cutover і потрібні consumers; загальний repo-wide rewrite не пропонується.
