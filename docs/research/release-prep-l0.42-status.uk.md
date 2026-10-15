# l0.42.0 — статус підготовки до релізу (за RELEASE.md, виміряно)

**Оновлено:** 2026-10-15 · tip `b5e0c01bfa95cf247907a6f381c1e6bf05fadea3` (main)  
**Джерело влади:** `RELEASE.md` (DRAFT · NO-GO), `RELEASE-EVIDENCE.md`,
`CURRENT.md` → `language-contract.lisp`.  
**Метод:** читання релізного апарата + запуск релізних перевірок на цьому SHA.
Rust/cargo smoke і full workspace test у середовищі не ганялись — tag-time
доказ на candidate SHA лишається обов'язковим.

Це **не** GO і не новий мовний контракт. Невідоме = BLOCK.

## Ворота → стан (перезамір 2026-10-15)

| # | Ворота (RELEASE.md) | Стан | Доказ на tip |
|---|---|---|---|
| 1 | Номер CLI/crates/інсталятора `0.42.0` | **DONE** | `crates/{sens,sens-cli,sens-host,sens-literate,sens-lsp,sens-semantic,sens-wasm}` усі `0.42.0`; `guix.scm` `0.42.0`; `packaging/install.sh` → `l0.42.0`; `scripts/release.lisp` вимагає `0.42.0` |
| 2 | P0 (#5406 T5, #5408 quantity, #2170 exact-width) + блокери #4196 | **OPEN** | issue-трекер; host-тест ≠ незалежний свідок |
| 3 | Pin toolchain (Rust, Actions) | **DONE (механічно)** | `rust-toolchain.toml` → `1.99.0`; `python3 scripts/check-release-pins.py` → `RELEASE_PINS_PASS channel=1.99.0 workflows=13`. Digest rustup/runner image у `RELEASE-EVIDENCE` ще **UNSET** |
| 4 | Один candidate SHA: cargo test --locked --workspace, clippy, D1–D9, D10 meta, T5/F3C, UK/T5/view, admission | **BLOCKED** | `knowledge/release-admission-ledger.json` **відсутній** → `RELEASE_ADMISSION_BLOCKED`; `uk_oracle_verified` / `release_admitted` не можуть бути PASS без ledger + oracle |
| 5 | Платформи + manifest + SHA-256 | **ВЖЕ В `release.yml`** | CLI matrix + MSI + web + islands-manifest + SHA256SUMS |
| 6 | Публікація лише після GO; атомарно | **ВЖЕ РЕАЛІЗОВАНО** | `create-release` draft; `publish-release` після success усіх asset-джоб і `$GITHUB_SHA == main` |
| 7 | `RELEASE-EVIDENCE.md` | **NO-GO** | candidate SHA, Cargo.lock SHA, CI run ID, owner authorization = **UNSET**; verdict **NO-GO** |

## Що змінилось від попереднього зрізу (6b980ca)

| Було (документ) | Стало (виміряно) |
|---|---|
| Ворота #1 «патч готовий» | **уже в main** — усі релізні crate `0.42.0` |
| Ворота #3 «немає rust-toolchain.toml / @stable» | **`rust-toolchain.toml` = 1.99.0**, pins PASS на 13 workflow |
| Admission ledger | як і раніше **відсутній** — hard BLOCK на #4 |

## Справжні hard-блокери (не номер версії)

1. **`knowledge/release-admission-ledger.json`** — схема `sens-release-admission-ledger/v1`, записи F1–F4 + `ratified=1` + typed_word_sha256 збіг з `.sens`. Без цього `check-release-admission-ledger.py` fail-closed.
2. **Незалежний український oracle** на corpus (не host truthiness).
3. **Freeze candidate SHA** + заповнення `RELEASE-EVIDENCE.md` + owner GO.
4. **P0 issue** з #4196 / #5406 / #5408 / #2170 — закрити доказами, не «зеленим» обходом.

Відсутні human-readable view-файли **не** є головним блокером: вони знімають лише `view_missing`; semantic oracle лишається.

## Доказове уточнення після виправлення перевіряча — 2026-10-15

- [`dc623c0`](https://github.com/juv4uk/sens/commit/dc623c00358c7f0127c39e1c5336daabf488eae8) у `main` виправив саме **механічний** `scripts/check-release-admission-ledger.py`: `content_verified` рахує правильно перевірені T5-байти, але `uk_oracle_verified=0` і `release_admitted=0`, поки незалежні F1–F4 семантичні свідки не відтворені. Текстові SHA/path/line посилання у F1/F2/F4 самі по собі не є виконаним SENS-оракулом.
- У тому самому коміті оновлений [негативний тест](https://github.com/juv4uk/sens/blob/main/tests/test_check_release_admission_ledger.py): канонічний фізичний `.sens` із правдивим typed-word хешем, але вигаданими F2/F4 посиланнями **не** дістає семантичного допуску; CLI повертає `RELEASE_ADMISSION_BLOCKED`. Це перевірений diff/readback коду й тесту, **не** звіт про виконаний Hosted CI на кандидатові.
- **Наступний доказ для воріт #4:** реальне джерело F1, незалежні виконані позитивний і негативний F2, доказ F3-дедуплікації, фізичний виконуваний F4 та окремий український oracle на тому самому SHA. Відсутній `knowledge/release-admission-ledger.json` не можна заповнювати фіктивними посиланнями. Статус `NO-GO`, candidate SHA `UNSET`; підпис власника й publication не надані.

Це ненормативний додаток до датованого механічного зрізу вище, а не нова аксіома або самостійний release gate.

## Механічні команди (перезамір перед тегом)

```sh
git rev-parse HEAD
python3 scripts/check-release-pins.py
python3 scripts/check-release-admission-ledger.py   # очікується BLOCKED без ledger
# після ledger + oracle + freeze:
# cargo test --locked --workspace
# scripts/verify_release_ci.py <SHA> juv4uk/sens
```

## Межі

- Не тегував, не публікував, не вигадував admission-ledger і не ставив GO.
- Transport-bench (Zig↔Rust) і cross-language BLOCKED **не** замінюють релізні ворота #4/#7.
- Числа на точному SHA вище; дерево рухається — перезаміряти перед GO.
