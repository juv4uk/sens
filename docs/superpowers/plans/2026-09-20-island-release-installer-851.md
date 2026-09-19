# #851: план реалізації release installer для islands

**Мета:** додати до `my-lisp-cli` read-only `islands plan` і `islands status`,
які читають versioned manifest та показують capability observation без зміни
семантики мови.

**Дизайн:** `crates/my-lisp-cli/src/islands.rs` володіє Rust manifest model,
platform selection та rendering plan/status. `main.rs` лише розпізнає
`islands` subcommand. Fixture manifest є test data, не source semantic truth.

**Специфікація:** `docs/superpowers/specs/2026-09-20-island-release-installer-851-design.md`.

## Глобальні обмеження

- V1 не виконує download, package-manager install або automatic fallback.
- Ні manifest, ні status не видають і не змінюють SID.
- `available` означає runtime availability, не semantic admission.
- Manifest показує version, provenance, license, platform і provider до будь-якої install-дії.
- Змінений Rust проходить focused test і strict clippy; нові Lisp файли тут не потрібні.

## Task 1: Manifest model та pure platform selection

**Файли:**
- Створити: `crates/my-lisp-cli/src/islands.rs`
- Створити: `crates/my-lisp-cli/tests/islands_manifest.rs`
- Створити: `tests/fixtures/islands-manifest-v1.json`

**Інтерфейс:** `IslandManifest::parse(&str) -> Result<IslandManifest, String>`
та `IslandManifest::plan_for(&[String], Platform) -> Vec<IslandPlan>`.

1. Написати RED tests для Prolog/CLIPS Linux plan, unsupported target і
   checksum field release asset.
2. Запустити `cargo test -p my-lisp-cli --test islands_manifest` і побачити
   fail через відсутній module/API.
3. Реалізувати serde manifest schema: stable key, version, license,
   provenance, platform, provider, executable/probe або explicit unsupported.
4. Реалізувати pure selector без filesystem/network side effects.
5. Повторити focused test і `cargo clippy -p my-lisp-cli --test islands_manifest -- -D warnings`.

## Task 2: CLI `islands plan` та `islands status`

**Файли:**
- Змінити: `crates/my-lisp-cli/src/main.rs`
- Змінити: `crates/my-lisp-cli/src/islands.rs`
- Створити: `crates/my-lisp-cli/tests/islands_cli.rs`

**Інтерфейс:**
`my-lisp islands plan --manifest <path> --with prolog,clips`;
`my-lisp islands status --manifest <path>`.

1. Написати RED tests, що `plan` друкує version/provenance/license/provider і
   не створює install directory.
2. Написати RED test, що `status` розрізняє absent та unsupported.
3. Додати narrow CLI dispatch, який не впливає на REPL/oracle paths.
4. Render plan/status у стабільному text або JSON format; `install` поки
   повертає explicit `not implemented in installer v1`.
5. Запустити tests та strict clippy.

## Task 3: Documentation й release integration boundary

**Файли:**
- Створити: `docs/ISLAND-INSTALLER.md`
- Змінити: `.github/workflows/release.yml`

1. Написати test або static check, що release manifest є asset release job.
2. Додати manifest fixture/generation до release assets без secrets або
   third-party artifact download.
3. Документувати українською: install ≠ semantic admission; manifest data,
   licence/provenance display, four capability statuses.
4. Запустити targeted tests, clippy і `cargo xtask verify`.

## Перевірки review

- Невідомий island має named error, а не fallback до іншого runtime.
- Unsupported platform має `unsupported`, не `absent`.
- SHA-256/manifest provenance не може бути silently omitted для release asset.
- Один island можна планувати незалежно від інших.
- CLI не виконує side effect від `plan` або `status`.
