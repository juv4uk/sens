# Nano-SENS seed-v0 — виміряний baseline (2026-10-12)

Статус: **PASS для runner-component baseline; BLOCKED для повної метрики seed-input closure.** Два незалежні чисті прогони дали однаковий звіт. Пізніший аудит виявив, що runner під час виконання запускає `cargo run -p xtask -- compiler-export` у pinned SENS checkout; отже, вимір 34,580,696 Б — розмір компонента, а не повного набору байтів, без яких ланцюг не стартує. Повний seed-total не публікувати, доки closure не перелічено й не виміряно.

Зовнішні crates для compile path `xtask → sens → serde` закріплено окремо в JSON census за версіями та `Cargo.lock` checksums: `serde 1.0.229`, `serde_core 1.0.229`, `serde_derive 1.0.229`, `proc-macro2 1.0.107`, `quote 1.0.47`, `syn 3.0.3`, `unicode-ident 1.0.24`. Їхні registry archive/cache bytes не входять у наведені 1,432,402 Б; availability і розмір зовнішнього кешу ще не виміряні. `cargo run -p xtask -- compiler-export` також виконує `git rev-parse HEAD`, тому `.git` metadata лишається явною залежністю до її вимірювання або вилучення з runtime chain.

## Первинні докази

- CML workflow run: [38182268999](https://github.com/juv4uk/cml/actions/runs/38182268999) — два matrix jobs і compare job завершилися PASS.
- Два-run proof: `nano-sens-two-clean-runs-proof/1`, SHA-256 `2e3110b5033ecd8927e35fe7540ee2e0b6cbff773c198d58a7bc30aa11aa615e`.
- Канонічний `nano-sens-size-report/1` SHA-256: `dd4473beb15d6bba6f8cabc12b4ae7885d388231b70750f4fdfc29bb0f18eca3`.
- Lineage report SHA-256: `1152eb6247561a595375600f02653503747b8b9542a8c6f9eaabb3316d3c939d`.
- Довготривала адреса запису в SENS main: [evidence/nano-sens-seed-v0-2026-10-12.json](https://github.com/juv4uk/sens/blob/main/evidence/nano-sens-seed-v0-2026-10-12.json).
- GitHub Actions raw artifacts мають retention 30 днів, до 2026-11-10 UTC.

## Перше чесне число

| Артефакт | On-disk bytes | Loadable PT_LOAD file bytes | Executable code-section bytes |
|---|---:|---:|---:|
| seed-v0 C0 runner | **34,580,696** | 6,038,608 | 4,145,007 |
| C1 executable | 92,248 | 85,685 | 70,655 |
| C2 executable | 92,248 | 85,685 | 70,655 |

Вимірювач: GNU `readelf -W -l/-S`. Це три різні метрики; вони не підміняють одна одну.

**Що названо seed-v0:** `seed-v0-c0-runner.bin`, SHA-256 `d45e09837a10103879c3d405c54ddf53ee2b1376bce969ccd20316ece4065be4` — CML Rust `lib` test-runner executable, що запускає host/bootstrap witness, створює C1 і запускає C1/C2. Це великий operational baseline, який містить Rust bootstrap-код. Це не претензія на мінімальність і не сенс-програма, яку можна прочитати на сторінці.

C1/C2 executable SHA-256 однаковий: `27b8fbf096cddbb77be2b4bf57cc58bf8b4fac4accc42adbcfbc10d6cd95f375`. Згенероване C1/C2 джерело однакове (SHA-256 `89199fe59621ce0434e70f2a161cdc3089ef8d588d6d8cc461a1e4f72372d225`); canonical compiler-artifact output збігається (SHA-256 `303d96cd1467fae319fb2dcf2c12e1a73c840bb0a0ecab67f3609ffde411d79a`). Критерій не послаблювався: `byte-identical-artifact`.

## Pinned джерела й зовнішні залежності

- CML workflow checkout SHA: `9b852bc70b3d529933b85dd592f301e0b1e9e37d`.
- SENS submodule SHA: `d0787a40fcea36501747732aa61b6de19fe29c70`.
- Compiler nucleus SHA-256: `34863f297e0f4f6f21c30dffc34a8bb85822015a89d13028c700b5a679f61b7e`.
- Contract SHA-256: `177d532d24c1f0738a934152f65c7f01f90b5593c8dbfe519e31148c0aa80c40`.
- Structural-law projection SHA-256: `3ce5bb4e042bfec446199a9c77787d0a022109e9a6d6442a4f93b50f68e34e9a`.
- Measurement/validation tools pinned to SENS commit `ca9babfec9d20259a206153476d7717f91be3bb6`.

Зовнішні залежності, їхні версії та shared-library names збережено у bootstrap manifest і **не включено** до 34,580,696 bytes: rustc 1.99.0, Cargo 1.99.0, GCC 13.3.0, GNU ld 2.42, target `x86_64-linux-gnu`, Ubuntu runner, `libgcc_s.so.1`, `libc.so.6`, `ld-linux-x86-64.so.2`, `linux-vdso.so.1`. Байти цих залежностей, мінімальний seed та повний GAS/NASM golden-corpus parity ще не виміряні/доведені.

## Наступні ворота — одна кампанія за раз

Для K1 виконано лише окремий C1-local correctness/size experiment. Повний seed-v0 gate залишається BLOCKED; K2–K4 не стартують до закриття й вимірювання повного input closure. Кампанії не змішувати.

1. **K1 — static-link + strip C1:** окремий baseline/variant, повні тести, lineage та два чистих запуски; не стирати секції без їхнього окремого обліку.
2. **K2 — заміна Rust-компонентів на SENS-програму:** кожну заміну перевіряти окремо. Вести дві незалежні метрики — trusted-seed bytes та чітко визначений independence-index.
3. **K3 — Framed-3 self-extracting seed:** research-only, з окремими encode/decode, semantic witness і fail-closed negative tests.
4. **K4 — slot-VM:** окремий виконавчий варіант і міст до microcpu; повний corpus та збіг observables до заміни runtime.

Перед K2–K4 перевірити донорські матеріали: stage0/hex0 на [bootstrappable.org](https://bootstrappable.org/), SectorLisp та TinyCC. Наведені як орієнтири розміри донорів не порівнювати з цим seed, доки не збігаються межі байтів, target і правила обліку. Історичні Lisp — донори/тести, не автоматичне ядро.

## Семантичні межі

- Contract 11.8 зберігає семантичну владу. Rust, GCC, linker, codec і VM — механізми/свідки, не джерела мовного значення.
- D10 дослідний і не є залежністю Nano-SENS. У поточному `knowledge/d10-v1-semantic-inventory.json` на main зафіксовано **675/1024** selected research candidates, 349 remaining, 0 ратифікованих D10 residents. Це не підтверджує формулювання 1024/1024 selected; іншу цифру змінювати лише після перевірки конкретного SHA та відповідного ledger.
- Нових гілок, доменів або семантичних таблиць для Nano-SENS не створювати.

**Висновок первинного прогону:** PASS лише для вимірювання runner-component baseline; повна метрика seed-input closure і досі **BLOCKED**. Значення 34,580,696 Б — розмір ELF-компонента, не повний seed-total. Повний total не публікувати; початкова таблиця не є доказом мінімального seed.


## K1 — static-link + strip C1: вимір завершено, виграшу розміру немає

Дата: 2026-10-12. Рішення: **PASS_MEASURED / NO SIZE WIN**. Повний доказ: [evidence/nano-sens-k1-static-link-2026-10-12.json](../evidence/nano-sens-k1-static-link-2026-10-12.json). [CML Actions run](https://github.com/juv4uk/cml/actions/runs/38183052531).

Два незалежні чисті запуски пройшли повний CML library corpus: **189 passed / 0 failed у кожному**. У кожному запуску статично зібраний C1 відтворив baseline-вихід побайтно; malformed SW1 input було відхилено. Lineage C1/C2 залишився byte-identical. Порівняльний job підтвердив, що два `nano-sens-size-report/1` однакові байт у байт, SHA-256 `ad41654be6b742816566c3f542b9e1712677e8be63880cc5c12e42ce583f519d`. Докази з retention 30 днів: [two-clean-runs ZIP](https://github.com/juv4uk/cml/actions/runs/38183052531/artifacts/11718651632), expiry 2026-11-10 UTC.

| C1 variant | On-disk | Loadable PT_LOAD file bytes | Executable code-section bytes |
|---|---:|---:|---:|
| Baseline dynamic C1 (`-s`, no build ID) | 92,248 | 85,685 | 70,655 |
| K1 static-link + strip (`-static -s`, no build ID) | 792,544 | 775,255 | 586,312 |
| K1 minus baseline | **+700,296** | **+689,570** | **+515,657** |

Static variant has the same output SHA-256 as baseline: `303d96cd1467fae319fb2dcf2c12e1a73c840bb0a0ecab67f3609ffde411d79a`. But it is 759.14% larger on disk, 804.77% larger in loadable file bytes, and 729.82% larger in executable code-section bytes. Therefore **K1 is not adopted as a size-reduction strategy**. This is a measured negative result, not a failed correctness witness.

Scope warning: the CML test-runner inside this K1 run is instrumented by new test code and therefore has a different file size from the frozen seed-v0 run. Do not report that runner size as a new seed-v0 baseline or compare it directly with the original 34,580,696-byte baseline. This K1 comparison concerns the unchanged baseline C1 versus its static-linked variant only.

The full GAS/NASM golden-corpus parity and total shared-library/toolchain dependency bytes remain unmeasured. Neither can be inferred from these results.

## Next: K2 readiness, before changing the seed

K2 starts with **one Rust-owned component at a time**, not wholesale substitution of the compiler. The first candidate-selection pass should map the current seed-v0 call chain to exact files and pinned SHAs, then select the smallest self-contained Rust-owned orchestration/serialization component whose contract already has a positive and negative witness. Do not replace semantic authority, do not move hidden dependencies outside the byte count, and do not alter the C1/C2 equivalence gate.

K2 must publish two separate series:
- **trusted-seed bytes**: exact operational seed artifact bytes, measured with the same on-disk/loadable/code-section rules and the same declared dependency boundary;
- **independence-index**: publish the formula and explicit inventory of which required executable components are authored in SENS versus Rust/host tools. It must not be an arbitrary scalar: report the numerator/denominator or component ledger, with each component pinned and each classification supported by evidence.

A replacement only counts if the complete positive corpus, fail-closed negative corpus, lineage, and two clean runs all pass. If trusted-seed bytes fall while the independence measure does not improve (or vice versa), record that tradeoff rather than declaring an overall win. K3 and K4 remain behind their own gates; this K1 result is not permission to combine campaigns.


## Виправлення межі seed-v0 — аудит runtime input closure (2026-10-12)

Перевірка коду після K1 виявила, що `src/sens_c1_artifact.rs::pinned_compiler_export()` під час тесту запускає окремий процес:

```text
cargo run --manifest-path external/sens/Cargo.toml -p xtask -- compiler-export
```

Отже, `seed-v0-c0-runner.bin` (34,580,696 Б у первинному прогоні) — виміряний ELF-компонент, але не єдиний runtime-вхід. Ланцюгу також потрібні pinned SENS checkout/ Cargo workspace inputs для побудови `xtask` і SENS runtime. Це не toolchain/linker/ОС: кодові файли й compiler nucleus не можна непомітно переносити в «external dependencies» і виключати з seed-total.

Проміжний машинозчитуваний census: [`SENS source closure`](../evidence/nano-sens-seed-v0-source-closure-census-2026-10-12.json). Окремо зафіксовано [CML runner input census](https://github.com/juv4uk/cml/blob/master/evidence/nano-sens-cml-runner-input-census-2026-10-12.json) для pinned CML `3320fe3b00a4a099ecb9ff06e22e0be2b1fee499): 62 default `cargo test --lib` module sources + 8 root/build/contract files = 70 paths / 1,320,729 Б. Це інший підрахунок, окремий від SENS subset; не складати ці числа в seed-total. Поточний census після аудиту include-ів: **117 pinned paths / 1,432,402 Б** у перевіреному SENS subset (70 production Rust sources, 20 Cargo package manifests, 27 root/authority/embedded and CML-consumed inputs). Виправлено дві протилежні похибки попереднього census: вилучено 3,271-Б `bootstrap_measurement.rs`, який доступний лише під `#[cfg(test)]`, і додано 13 compile-time include-файлів з `lib.rs` та пов’язаних production-модулів (разом 254,906 Б; 13-й — `lib/core.lisp`, вбудований `gpu_oracle_conformance.rs`). Цей subset все ще не є повним closure чи seed-total; повна автоматична перевірка графа модулів та `.git`/Cargo inputs залишається відкритою.

Відомі точні pinned вузли ланцюга на SENS SHA `d0787a40fcea36501747732aa61b6de19fe29c70`:

| Файл | Git blob SHA | Bytes |
|---|---|---:|
| `Cargo.toml` | `880cd66b98fd2fb9ea34fe428526f09a073fb8c3` | 1,492 |
| `Cargo.lock` | `293e933d0fdb78954386243eae431c2826b62a79` | 20,813 |
| `.cargo/config.toml` | `ae9cf46bf18b89c74c88462c29713601c7972f01` | 136 |
| `crates/xtask/Cargo.toml` | `eed4c217f9d61b4db486b06df0fe80c163961a25` | 345 |
| `crates/xtask/src/main.rs` | `7b05ea47e12d35e702bd33b1969b1767ce0ddab8` | 9,133 |
| `crates/xtask/src/compiler_export.rs` | `8d8afb359f9f7adb35c4c76f662189226b5a332a` | 10,553 |
| `crates/sens/Cargo.toml` | `50b4c7a37ca3aa82993bea6b258b5de3b488820c` | 674 |
| `crates/sens/src/lib.rs` | `386158468ec44c20433ddee8432c1c81f9907ef9` | 27,192 |
| `crates/sens/src/compiler_language.rs` | `b15cee61eb8f0c40761a0d467c3818eeea89ca5f` | 59,607 |
| `lib/compiler-nucleus.lisp` | `c81ff7341a3a18c7cb6ff8e77038318bb935b232` | 24,506 |
| `contracts/compiler-nucleus-identity-corpus-v1.tsv` | `c57b0df98f467ddcad067158dad1c97a349ad1bf` | 426 |

Це **перевірені subset-и, не остаточний мінімальний closure**. Уже записано 70 production Rust source files SENS/xtask, 20 workspace manifests, відомі compile-time include inputs і ще 70 CML source/metadata paths. Залишаються автоматичне вичерпне підтвердження `cfg`/module-графа обох репозиторіїв, усі активні Cargo build/test dependency sources (включно з `wsm-os-target` і registry cache), runtime file reads, generated outputs та точний облік `.git` metadata. Тому `whole_chain_seed_closure_status = BLOCKED_PARTIAL_LOWER_BOUND_NOT_COMPLETE_OR_MINIMIZED`; одне число для повного seed наразі не публікується. Компонентний вимір зберігається як історично pinned baseline й не стирається.

### K2 — перший кандидат після closure-аудиту

Поточний вузький target: **Rust transport/exporter** `crates/xtask/src/compiler_export.rs`, який читає D3/D4 identity-only corpus, викликає `sens::compiler_semantic_input_from_sens` і сам форматує compiler-semantic-request. Сам role-law вже виконується з `lib/compiler-nucleus.lisp` через `crates/sens/src/compiler_language.rs`; його не переносити до другої Rust-таблиці й не дублювати значення в Lisp.

K2 candidate — перенести формування запитів/обхід дев'яти fixture-рядків до SENS-owned програми та залишити в хості тільки представницькі механізми, pinned provenance й execution boundary. Спочатку довести побайтний паритет зі старим exporter і негативне fail-closed поводження. Якщо для запуску нової програми все одно потрібен окремий Cargo-built `xtask`, trusted-seed reduction не зараховується.

**Обов'язкова передумова перед K2:** замкнути мінімальний file closure і baseline bundle-total. Далі кожну заміну вимірювати як ціле: trusted-seed bytes (у межах повного closure) та independence-index окремо; індекс спершу визначити як прозорий ledger компонентів із формулою, а не довільний скаляр. Повний CML library corpus, fail-closed негативні випадки, lineage та два чисті byte-identical runs залишаються обов'язковими.
