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

## Обов'язкові спостережувані ворота на тому самому SHA

| Gate | Evidence to attach | Verdict |
|---|---|---|
| `cargo test --locked --workspace` | URL, runner, SHA, raw log | UNKNOWN |
| `cargo clippy --locked --workspace --all-targets -- -D warnings` | URL, runner, SHA | UNKNOWN |
| D1–D9 exact-width / COND/ATOM/EQ negative controls | Source+binary/oracle parity & run URL | UNKNOWN |
| D10 owner-ratification metadata and proof limits | Pinned manifest digest; negative callable tests | UNKNOWN |
| T5 and F3C roundtrip + corrupted input refusal | Physical byte golden fixtures | UNKNOWN |
| All release-scope `.lisp` ↔ `.sens` ↔ extensionless triples | Full corpus inventory + independent Ukrainian oracle ledger | UNKNOWN |
| T5 authority, quantity witness, exact-width blockers | [#5406](https://github.com/juv4uk/sens/issues/5406), [#5408](https://github.com/juv4uk/sens/issues/5408), [#2170](https://github.com/juv4uk/sens/issues/2170) | OPEN |
| `release-preflight.yml` + mandatory hosted/native jobs | Exact SHA, all required checks | UNKNOWN |
| Linux/Windows/macOS CLI + MSI + portable Web | Platform-specific install/smoke results | UNKNOWN |
| SHA-256 of every release asset and independent clean replay | Published digest manifest, verified bytes, environment | UNKNOWN |
| Clean release publication (no incomplete visible release) | Atomic publication workflow proof | UNKNOWN |

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
