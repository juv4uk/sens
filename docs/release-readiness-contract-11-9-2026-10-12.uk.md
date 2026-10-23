# SENS — план міграції та релізна готовність (Contract 11.9)

**Дата аудиту:** 2026-10-12. **Статус:** ПІДГОТОВКА / **NO-GO для публікації**.
**Цільова координація:** [реліз l0.42.0 #4196](https://github.com/juv4uk/sens/issues/4196), [єдиний release chain #4250](https://github.com/juv4uk/sens/issues/4250), [міграційний рій #4449](https://github.com/juv4uk/sens/issues/4449), [два кодеки #5440](https://github.com/juv4uk/sens/issues/5440). Це **операційний чекліст**, а не новий мовний контракт і не обхід існуючого release.yml.

## 1. Незмінні правила

- Семантична ідентичність = точні двійкові біти + точний домен + допущений/доведений закон. Лише [CURRENT.md](../CURRENT.md) і [language-contract.lisp](../language-contract.lisp) визначають активну мовну владу.
- **D1–D9:** чинний фундамент; старі SID8/Sens8 — лише історичне походження та ізольований compatibility transport, не універсальний простір функцій. D10 власником ратифікований цілком **1024/1024**, проте незалежні F1/F2/F3/T5/runtime докази ще потрібні: не рекламувати виконання 1024 функцій. D24+ числова драбина ратифікована; виконувані NEG/RATIO-композиції та їхній packed numeric framing **не дорівнюють** готовому загальному фізичному `.sens`/T5 формату для них.
- **T5M `.sens`** — поточний загальний production/default формат; старий T5 — лише явний compatibility-маршрут. **F3C `.senc`** — окремий явний компактний маршрут із маркером 0xF3, лише за суворої економії та доведеної байтової зворотності. F3M `.f3m` — bounded/research мікросім'я, не production-default. Немає magic-sniffing і fallback під час декодування пошкодженого `.senc`.
- Для **допущеної виконуваної** програми зберігати трійку: українська проєкція `name.lisp`, фізичний T5M `name.sens`, читабельний файл `name` без розширення (тільки 0/1, по одному пробілу, кінцевий LF). Фізичне `.sens` не є текстом; людський view не є незалежним авторитетом. Не вважати каталоги ISA/схеми/історичні докази виконуваними програмами.
- Лише `main` для нових змін: **не створювати гілок**. Попередні гілки — матеріал аудиту й доказової консолідації, не привід переписувати history чи скидати CI. Один відповідальний інтегратор [#5041](https://github.com/juv4uk/sens/issues/5041).
- Не видаляти первинні `.lisp`, не переписувати масово `.sens`, не примушувати негативний guard зеленіти, не ослаблювати release-blocking checks.

## 2. Виміряна вихідна точка — НЕ release certificate

**CI вибірка на commit `da5ab14e42bf...` (2026-10-12 09:14 UTC),** після якої `main` просунувся принаймні до `08fa100d00b0d1763f065b9d6b51b941244c4b92` (09:16 UTC). Потрібно повторити **всі** ворота на одному майбутньому **точному** candidate SHA; не переносити verdict автоматично між комітами.

| Напрям | Вимір / причина BLOCK | Доказ |
|---|---|---|
| Hosted CI | `fs_bridge_diagnostics` відхилив відновлення exported world package; D3 stale logic test вказує на `scripts/check-island-math-evidence.lisp`; time-source regression також падає | [run 38228581929](https://github.com/juv4uk/sens/actions/runs/38228581929) |
| T5 migration inventory (M0) | Manifest drift: новий producer/consumer `benchmarks/physical-binary-performance/test_word_projection.py` відсутній у закоміченому реєстрі | [run 38228581777](https://github.com/juv4uk/sens/actions/runs/38228581777), [#5444](https://github.com/juv4uk/sens/issues/5444) |
| T5 readiness census | 664 розглянуті файли; 12 mechanical candidates, 652 BLOCK у source-era auto; **0** незалежно сертифікованих оригінальних виконуваних міграцій. Частина файлів — архіви або декларативні джерела, не «652 програми» | [run 38228581843](https://github.com/juv4uk/sens/actions/runs/38228581843) |
| T5 file authority | Повне перенесення assembled original Lisp oracle заблоковане семантичним допуском; verdict T5 oracle не отримано | [run 38228581765](https://github.com/juv4uk/sens/actions/runs/38228581765) |
| Native vertical smoke | `sens-host --test native_cond_profile` має реальне FAILED на EQ/COND branches | [run 38228581849](https://github.com/juv4uk/sens/actions/runs/38228581849) |
| LET source replay | Pinned очікування розійшлося з поточними `lib/forward.lisp`, `lib/knowledge.lisp` (перевірити семантичний delta до оновлення witness) | [run 38228581890](https://github.com/juv4uk/sens/actions/runs/38228581890) |
| Релізна упаковка | Усі сім канонічних crates, Cargo.lock, `scripts/release.lisp`, Guix і installer оновлено до `0.42.0`; parity/installer CI та перевірка всього candidate SHA ще обов’язкові | [crates/sens-cli/Cargo.toml](../crates/sens-cli/Cargo.toml), [#4197](https://github.com/juv4uk/sens/issues/4197) |

Зовнішні залежності **не припускати готовими**: перевірити фактичний стан CML, GraalVM, Futhark/CUDA, FPGA та їхні exact-SHA CI. На час аудиту GitHub повідомляв default branch `master` для `juv4uk/cml`, а `juv4uk/wsm-mu-lisp` за цією адресою не відкривався. `juv4uk/sens` і `juv4uk/sens-futhark` повернули `public`: перед релізом перевірити потрібну власнику політику видимості (не змінювати автоматично).

## 3. Послідовність підготовки

### M0 — заморозити scope та зробити read-only інвентаризацію
- [ ] На початку кожної хвилі зафіксувати `git rev-parse HEAD`, commit/tag, domain contract, git blob SHA кожного вхідного файла, файл-маніфест і список усіх активних producer/consumer; не посилатися на тест іншого SHA.
- [ ] Відрізнити `EXECUTABLE`, `DECLARATIVE`, `ARCHIVE`, `UNRESOLVED`; fail-closed для невідомих класів. Сканувати весь tracked корпус, не вибіркові 11 зручних прикладів.
- [ ] Прогнати `python3 scripts/migrate.py candidates --report /tmp/sens-candidates.json`; пройти first-() cohorts: D2-as-data, nonbinary words, historical W8 collisions, LET, quotation/text/numbers, host effects.
- [ ] Прогнати `python3 scripts/report_t5_t5m_triplet_inventory.py . --strict --report /tmp/sens-triplets.json` (очікуване блокування до допуску); синхронізувати живий inventory та `M0` manifest лише за доказом і протестувати негативний drift witness.

### M1 — семантичний допуск кожного оригіналу
- [ ] Для кожного виконуваного `.lisp` визначити source-era + точний Git blob + історичний незалежний oracle + сучасний oracle, successor за ратифікованим exact domain, typed/physical хеші.
- [ ] Користуватися [admit-t5-migration](ADMIT-T5-MIGRATION.uk.md) — **спершу dry-run, лише VERIFIED_NOT_WRITTEN → explicit write поза source tree**, без мовчазних замін або pass-through старих SID8.
- [ ] Порівняти незалежні stdout/semantics, `sens-trit eval`, exact-word/domain parity, `encode(decode(.sens)) == .sens`; негативні контролі на ambiguity, D2 control-as-data, stale COND/ATOM/EQ, truncation/padding.
- [ ] Для допущених файлів відтворити same-stem трійку, потім випробувати її окремим строгим release gate. Fixture-canary — не свідчення завершеної міграції історичної програми.

### M2 — два кодеки без пошкодження поточного корпусу
- [ ] Зібрати `cargo build --locked --release -p sens --example two_codec_small_programs` і пройти наявний [offline rehearsal](two-codec-migration-plan-2026-10-11.uk.md).
- [ ] Staging **поза checkout**: manifest source SHA-256/stage SHA-256 + byte-perfect decode F3C назад у T5, corrupted-marker negative, restore-stage, незмінний `git diff`.
- [ ] Здійснювати opt-in `.senc` лише для перевірених tiny програм. **Ніяких** масових in-place змін чи автоматичного переведення downstream; exact parity CML/GPU/FPGA/GraalVM окремо.

### M3 — release-candidate ворота на ОДНОМУ SHA
- [ ] Усунути всі фактичні падіння `Hosted CI`, T5 M0, file authority, native EQ/COND, LET witness; не «лікувати» failure вимкненням перевірки.
- [ ] `cargo test --locked --workspace` і `cargo clippy --locked --workspace --all-targets -- -D warnings`; Python migration/guard unittest, D1–D9 ratification, D10 ratification *metadata*, D24+ exact numeric boundaries, T5/F3C CLI roundtrip.
- [ ] `release-preflight.yml` + повний strict `release.yml` gate: всі релізні T5 triples мають physical/view/independent Ukrainian oracle admission; `view_missing=0`, `physical_blocked=0`, `uk_oracle_verified=physical_pairs_seen`, `release_admitted=physical_pairs_seen`. Наявний tag workflow спеціально блокує випуск — **не обходити**.
- [ ] Перевірити Linux/Windows/macOS/portable Web assets, інсталятор, manifest, release versions, перевірку на чистому середовищі, checksums і provenance. Якщо апаратний substrate недоступний, позначати `UNVERIFIED`, не `PASS`.
- [ ] Готовність збірки і релізу повинна стосуватися того самого `main@<full SHA>`. На час фінальної перевірки припинити сторонні зміни в релізній області, але не створювати окремої Git-гілки.

### M4 — публікація лише після GO
- [ ] Механічно вирівняти `l0.42.0` ↔ `0.42.0` і всі інсталяційні та asset-версії. Release notes: *Contract 11.9*, D10 **whole-domain owner-ratified but runtime not yet admitted**, D24+ виконувана Core-математика **без** удаваного T5 допуску.
- [ ] Зафіксувати точний SHA; створити **draft** release та підписані/перевірювані артефакти; опублікувати лише після GO і звірки хешів. Не пересувати вже випущений tag; у разі failure — no publish, fix у `main`, новий SHA, повторити всі checks.
- [ ] Зберегти старий стабільний реліз і T5 оригінали для rollback; `.senc` не має бути єдиною копією програми. Розрізняти rollback deployment від семантичного fallback при decoder error.

## 4. Фінальне правило рішення

**GO =** усі обов'язкові release-checks зелені на одному повному SHA **І** корпус релізних executable трійок допущений незалежним oracle **І** готові всі обіцяні платформи/артефакти **І** версії/маніфести збігаються **І** відсутня невизнана міграційна втрата семантики.

**Будь-який UNKNOWN, FAIL або неперевірена зміна SHA ⇒ NO-GO**. Якщо бажаний обмежений preview замість повного `l0.42.0`, його scope і назву слід окремо узгодити; не називати scope-реліз загальною міграцією.

Джерела: [CURRENT.md](../CURRENT.md), [режими](project-modes-2026-10-12.uk.md), [два кодеки](codec-two-routes-t5-f3-2026-10-11.uk.md), [rehearsal](two-codec-migration-plan-2026-10-11.uk.md), [поточний release gate](../.github/workflows/release.yml).
