# SENS l0.42.0 — release evidence ledger

> **DRAFT · NO-GO (2026-10-12).** Не є release certificate. Цей файл навмисно відокремлює **підтверджену мовну ратифікацію** від **ще не перевіреної готовності конкретного релізного SHA**. Невідоме = BLOCK, не PASS.

## Точка фіксації (заповнити лише після freeze)

| Поле | Значення |
|---|---|
| Candidate tag | `l0.42.0` |
| Candidate Git SHA (40 hex) | **UNSET** |
| Date/time UTC | **UNSET** |
| Contract source SHA-256 | **UNSET** |
| Contract generation | **11.9** (перевірити з pinned tree) |
| Rust version / rustup toolchain digest | **UNSET** |
| Cargo.lock SHA-256 | **UNSET** |
| CI run ID and immutable logs | **UNSET** |
| OS, CPU arch, container/runner image identifiers | **UNSET** |
| Owner release authorization | **UNSET** |
| Verdict | **NO-GO** |

## Мовна ратифікація ≠ виконуваний механізм

| Модель | Authority / задекларований рівень | Виконуваність / незалежний релізний свідок |
|---|---|---|
| D1–D9 | Ратифікований фундамент Contract 11.9 | **NOT YET CERTIFIED ON CANDIDATE SHA** |
| D10 | Whole-domain 1024/1024 ратифіковано 2026-10-12 | F1/F2/F3/runtime/T5: **PENDING**, не називати 1024 callable |
| D24+ | Окрема ратифікована числова драбина | Повне загальне physical T5 admission: **NOT CLAIMED** |
| T5 (`.sens`) | General/default physical carrier | Whole release executable corpus parity: **PENDING** |
| F3C (`.senc`) | Explicit tiny compact route | Ще потрібен exact-candidate stage/replay/digest |
| F3M (`.f3m`) | Bounded enumerative research | НЕ general-production release promise |

Authority: [CURRENT.md](CURRENT.md), [language-contract.lisp](language-contract.lisp), [проектна реальність](docs/project-reality-2026-10-12.uk.md).

## D10: наявні докази — чесний розподіл по рівнях

Поелементний аудит [усіх 1024 D10 записів](docs/research/D10-PROOF-COVERAGE-AUDIT-20261012.uk.md) (pinned Git blob `7e6acb2531308ae5f63600d4e0042111cc3ec59c`) підтверджує:

- **256/256** селекторів мають конструктивну алгебраїчну перевірку на моделі повного дерева пар і 256 попарно різних адрес; усі їхні координати й батьківські зв'язки збігаються з поточним D10/D9. Це **математичний**, а не T5/runtime доказ.
- **768** інших заповнених D10 координат не означають 768 виконаних функцій. **720** рядків мають `provenance`, **376** — позитивні та негативні описи/приклади; **349** явно очікують незалежності свідка.
- У **326** рядках поле `independent_oracle` прямо не заявляє SENS PASS; у v18 **0** явних `independent_oracle=VERIFIED` / `F2 PASS` і **0** `physical_t5_authorized=true`. Водночас спеціалізовані математичні та донорські оракули реально існують; їхні *тисячі test cases* не слід плутати з тисячами D10 residents.
- Тому **«800 функцій D10 доведені як фізично виконувані»** на цьому SHA не підтверджено. Наступний крок — прив'язати існуючі незалежні джерела до кожного stable_id і вести F1, F2 donor, F2 SENS, F3 global, F4 T5 окремо.

Це уточнення **не скасовує** whole-domain ратифікацію 1024/1024 і не переводить статус релізу з NO-GO у GO.

## Обов'язкові спостережувані ворота на тому самому SHA

| Gate | Evidence to attach | Verdict |
|---|---|---|
| `cargo test --locked --workspace` | URL, runner, SHA, raw log | UNKNOWN |
| `cargo clippy --locked --workspace --all-targets -- -D warnings` | URL, runner, SHA | UNKNOWN |
| Release package/tag version alignment | `crates/sens-cli/Cargo.toml` is `0.41.0`; proposed tag `l0.42.0` requires `0.42.0` | BLOCKED |
| D1–D9 exact-width / COND/ATOM/EQ negative controls | Source+binary/oracle parity & run URL | UNKNOWN |
| D10 owner-ratification metadata and proof limits | Pinned manifest digest; negative callable tests | UNKNOWN |
| T5 and F3C roundtrip + corrupted input refusal | Physical byte golden fixtures | UNKNOWN |
| All release-scope `.lisp` ↔ `.sens` ↔ extensionless triples | Full corpus inventory + independent Ukrainian oracle ledger | UNKNOWN |
| T5 authority, quantity witness, exact-width blockers | [#5406](https://github.com/juv4uk/sens/issues/5406), [#5408](https://github.com/juv4uk/sens/issues/5408), [#2170](https://github.com/juv4uk/sens/issues/2170) | OPEN |
| Filesystem runtime and exact-domain admission | Earlier [#5603](https://github.com/juv4uk/sens/issues/5603) / [run 38176345658](https://github.com/juv4uk/sens/actions/runs/38176345658): `content_store` 22/24 tests failed. Newer visible [run 38228581929](https://github.com/juv4uk/sens/actions/runs/38228581929) still fails overall: filesystem macro/alist path-bound witnesses, obsolete COND/ATOM/EQ scanner regressions, time-source witnesses and stale core-logic audit are red; its `content-store integration` step is green. | BLOCKED; rerun after fixes |
| `release-preflight.yml` + mandatory hosted/native jobs | Exact SHA, all required checks | UNKNOWN |
| Linux/Windows/macOS CLI + MSI + portable Web | Platform-specific install/smoke results | UNKNOWN |
| SHA-256 of every release asset and independent clean replay | Workflow computes `SHA256SUMS` and re-downloads / byte-compares draft assets; no candidate tag or release artifacts exist yet | IMPLEMENTED, NOT RUN / UNKNOWN |
| Clean release publication (no incomplete visible release) | Single `release-publish` job; staged artifacts; exact-main-SHA + explicit owner GO; complete asset set, provenance, SHA256SUMS and byte-exact draft replay; commit [50048ecc](https://github.com/juv4uk/sens/commit/50048ecc3edd782e2a4ab5f9ed42aeb86f4b0280) | IMPLEMENTED ON MAIN; CI / failure-injection verification UNKNOWN (still blocks GO) |

**GO iff** всі потрібні gates на **одному** Git SHA позитивні, усі обіцяні платформи й файли перевірені, без жодного невирішеного `UNKNOWN/BLOCKED/FAIL`. Не підміняти невиконані platform gates успішними локальними тестами.

## Бенчмарки: модель доказів, не рекламні коефіцієнти

У релізному пакунку для **кожного** твердження про швидкість/розмір потрібні: workload та вхідні дані; точний source/runner SHA; точна версія toolchain; warm/cold; машина й фонове навантаження; raw виміри; результат parity; порівняльний engine і версія; спосіб розрахунку медіани/довірчих меж.

- [Звіт поточного project reality](docs/project-reality-2026-10-12.uk.md) містить чітко обмежені доказові приклади; це **не** еквівалент бенчмарку всього випуску.
- [`docs/benchmarks.md`](docs/benchmarks.md) — історичний my-lisp, серпень/вересень 2026, не Contract 11.9 і не новий exact-SHA бенчмарк.
- Риторика «60× старт» або «99,9%» **не переходить** у релізний факт без контрольованого актуального відтворення.

## Журнал рішення

- **2026-10-12:** створено шаблон доказового пакунка; жоден candidate SHA не заморожено, жодного підпису чи GO не засвідчено.
- Після кожної зміни релізних байтів: попередній verdict кандидата недійсний; новий SHA → повний повтор перевірок.

Документи: [release scope](RELEASE.md), [операційний runbook](docs/release-readiness-contract-11-9-2026-10-12.uk.md), [#4198 exact-SHA cut](https://github.com/juv4uk/sens/issues/4198).

## Операційний журнал підготовки — 2026-10-12 (M0 / Cargo release)

Це **доказ вузьких виконаних задач**, не сертифікат `l0.42.0`; `candidate SHA = UNSET`, випуск залишається **NO-GO**.

| Робота | Факт | Межа доказу |
|---|---|---|
| M0 physical-T5 producer/consumer manifest | Закрито drift `benchmarks/physical-binary-performance/test_word_projection.py`; [атомарний коміт 4b9adf8](https://github.com/juv4uk/sens/commit/4b9adf824ccfa71868820eee224745232f279e03), наступні синхронізації agentів; [зелений CI 38232293478](https://github.com/juv4uk/sens/actions/runs/38232293478) на `ef96318e78e4dd67a0af140ac5918eceaf43421e` | Успішний **M0 inventory**, не semantic/oracle admission і не випуск на цьому SHA |
| `release.yml` Cargo dependency resolution | Сім додаткових `cargo test/build` команд отримали `--locked`; [коміт 7c0dffb](https://github.com/juv4uk/sens/commit/7c0dffbb7653ce759441c416923527d447dfa199) | Синтаксичний аудит у `main` підтверджує `--locked` для команд Cargo; **реальний tagged asset build ще не проводився** |
| `release-preflight.yml` | Додано `push`-тригер для релізних змін `main`, focused `clippy --locked`; [коміт 80b6f6d](https://github.com/juv4uk/sens/commit/80b6f6d8c5d9fe8d6832e7ca91bf7425d515e12e) | Конфігурація збережена; **успішного workflow run не зафіксовано** під час цього аудиту, тому gate залишається UNKNOWN |
| Інші обов'язкові CI | Latest checked `Hosted CI`, native vertical smoke, T5 file-authority на сусідніх HEAD ще мають FAIL | Не переносити чужий/старий verdict на майбутній release candidate; **NO-GO** |

Усі наступні докази замінюють лише відповідні UNKNOWN/FAIL після перевірки **одного** `main@<40-hex SHA>`. Release-публікація лишається з незалежним явним owner-GO та strict triplet admission.
