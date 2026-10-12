# l0.42.0 — статус підготовки до релізу (за RELEASE.md, виміряно)

**Ревізія:** `6b980ca78ba3893fc16c6b3b8c91565567173a8c` (main)
**Джерело влади:** `RELEASE.md` (DRAFT · NO-GO), `RELEASE-EVIDENCE.md`,
`CURRENT.md` → `language-contract.lisp`.
**Метод:** читання релізного апарата + запуск релізних перевірок. Rust/cargo
в середовищі немає — tag-time smoke не ганяв.

`RELEASE.md` перелічує **7 релізних воріт**. Нижче кожне зі станом «виміряно».

## Ворота → стан

| # | Ворота (RELEASE.md) | Стан | Доказ |
|---|---|---|---|
| 1 | Вирівняти номер CLI/crates/інсталятора: `0.41.0` → `0.42.0` | **ПАТЧ ГОТОВИЙ** | `l0.42.0-version-alignment.patch`, 14 замін у 10 файлах |
| 2 | Закрити P0 (#5406 T5 authority, #5408 quantity witness, #2170 exact-width) + блокери #4196 | **OPEN** | issue-трекери |
| 3 | Закріпити toolchain (конкретна версія Rust, Cargo.lock, Actions) | **НЕ ЗРОБЛЕНО** | 161 workflow використовують `dtolnay/rust-toolchain`, з них **180 × `@stable`**, лише 1 × `@nightly`; `rust-toolchain.toml` відсутній |
| 4 | Для одного SHA: `cargo test --locked --workspace`, clippy, D1–D9, D10 metadata, T5/F3C roundtrip, corpus-wide UK/T5/view gate | **BLOCKED** | triple inventory: `uk_oracle_verified=0/23`, `release_admitted=0/23` |
| 5 | Платформи + manifest + SHA-256 + походження | **ВЖЕ В `release.yml`** | 4 матриці CLI + MSI + web + `islands-manifest-v1.json` + `SHA256SUMS` |
| 6 | Публікація лише після GO; атомарно | **ВЖЕ РЕАЛІЗОВАНО** | draft-first + `publish-release` (див. нижче) |
| 7 | Прикріпити докази (`RELEASE-EVIDENCE.md`) | **UNSET / NO-GO** | усі поля `UNSET`, verdict `NO-GO` |

## Важлива корекція до тексту RELEASE.md

`RELEASE.md` застерігає: «нинішній `release.yml` створює release record до
завершення всіх збірок». **На поточній ревізії це вже не так.** Перевірено в
`.github/workflows/release.yml` (419 рядків):

- `create-release` створює реліз із `draft: true`;
- **усі** asset-джоби (`publish-island-manifest`, `build-cli` ×4, `build-msi`,
  `build-web`) заливають у чернетку (`draft: true`);
- фінальна джоба `publish-release` (`needs: [усі]`) перевіряє, що реліз досі
  чернетка і що `$GITHUB_SHA == main`, вимагає **повний** набір активів,
  рахує `SHA256SUMS` і лише тоді робить `--draft=false`.

Тобто **ворота #5 і #6 (друга половина #5604) уже закриті в main**. Отже #5604
варто звірити з цим фактом — його опис може бути вже виконаним.

## Що саме закриває цей патч (ворота #1)

`l0.42.0-version-alignment.patch` — суто номерний, без семантики:

- `crates/{sens,sens-cli,sens-host,sens-literate,sens-lsp,sens-semantic,sens-wasm}/Cargo.toml` — `version` 0.41.0 → 0.42.0;
- `guix.scm` — `(version "0.42.0")`;
- `packaging/install.sh` — 3 × `ASSET_NAME` + `DOWNLOAD_URL` (`…/l0.42.0/…`);
- `scripts/release.lisp` — коментар-приклад і рядок перевірки версії.

Це узгоджується з assert у `release.yml` (`RELEASE_TAG == "l"+version`) і з
тестом `cargo test -p sens-lsp --test release_parity` (усі релізні crate мають
однакову версію). Патч перевірено: `git apply --check` → **APPLIES CLEANLY**.

## Що лишається (і чому це не механічно)

- **Ворота #2** — P0-issue, рішення й докази власника.
- **Ворота #3** — треба **обрати** конкретну версію Rust (зараз `stable`);
  вибір версії — рішення власника, вигадувати номер не можна. Готовий
  завести `rust-toolchain.toml` і замінити `@stable` на неї, щойно версію назвуть.
- **Ворота #4** — справжній hard-блокер: незалежний український oracle
  (`uk_oracle_verified=0/23`) і ратифікований admission-ledger. Це не робота
  з текстом, а ратифікація власника.

## Межі

- Я не тегував, не публікував, не чіпав ратифікованих артефактів.
- Патч — лише номери версій; він не робить реліз готовим і не скасовує NO-GO.
- Числа — на точному SHA вище; перезаміряти перед тегом.
