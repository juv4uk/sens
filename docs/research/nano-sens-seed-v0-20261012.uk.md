# Nano-SENS seed-v0 — виміряний baseline (2026-10-12)

Статус: **PASS для runner-component baseline; BLOCKED для повної метрики seed-input closure.** Два незалежні чисті прогони дали однаковий звіт. Пізніший аудит виявив, що runner під час виконання запускає `cargo run -p xtask -- compiler-export` у pinned SENS checkout; отже, вимір 34,580,696 Б — розмір компонента, а не повного набору байтів, без яких ланцюг не стартує. Повний seed-total не публікувати, доки closure не перелічено й не виміряно.

Відомий **operational input subtotal для попереднього K1 checkpoint: 35,985,025 Б**: runner ELF 34,575,192 Б + 114 SENS/xtask runtime-build inputs 1,397,243 Б + `contracts/machine-lowering-boundary.lisp` 1,129 Б (CML runtime read) + `wsm-my-lisp/asm/nucleus.s` 11,461 Б. Раніше бракувало відомого CML runtime-read контракту, тому 35,983,896 Б виправлено на 35,985,025 Б.

Найсвіжіший pinned checkpoint `juv4uk/cml@100f30174f728cf2564ceeb2348f58bd8ac7dd06` пройшов два clean runs: **189/189 тестів у кожному**, C1/C2 і звіти побайтно однакові, Cargo графи пройшли `--locked`, lock-файли не змінилися. Відомий **partial subtotal: 36,033,737 Б** = runner ELF 34,623,904 Б + 114 SENS inputs 1,397,243 Б + CML runtime-read контракт 1,129 Б + WSM nucleus 11,461 Б. SHA runner `6fbbc819eac32253d9eadb5e1dc8e80295bdb0bde9a285076edd8d7fc9e40eb3`; звіт SHA-256 `5e42feee14a65d33e8e909dbb384276b5255591a7233bac09efbe37fc9635c72`; [CI proof run](https://github.com/juv4uk/cml/actions/runs/38186932277), proof artifact ID `11719573111`, expires 2026-11-11 00:10:35 UTC. Відмінності runner provenance між source checkpoints не є оптимізаційним виграшем/програшом.

Наступний closure-крок не підміняє runtime trace 38187252311: додано окремий [Rust dep-info census](https://github.com/juv4uk/cml/blob/f01ff979b5626379c99a4cd5c5e890ca962b8a28/scripts/nano-sens-rustc-dep-info-census.py) для компіляційних входів CML і вкладеного SENS `xtask`. Він перевіряє actual `.d` inputs, pinned Git blob hashes і байт-ідентичність нормалізованого census у двох clean runs. Валідація [CI run 38191754506](https://github.com/juv4uk/cml/actions/runs/38191754506) наразі `queued`; до фактичного завершення не публікую compile-input counts і не змінюю останній підтверджений operational subtotal.

Обидва subtotal-и — від pinned файлів, **не повний seed-total і не доказ мінімальності**. Зовнішні vendored crates, Git metadata, toolchain/OS/shared libraries та ще не закриті inputs ідуть окремо. Canonical JSON: [`known_operational_input_subset` і `latest_verified_operational_checkpoint`](../evidence/nano-sens-seed-v0-2026-10-12.json).

Зовнішні crates для compile path `xtask → sens → serde` перевірені як vendored inputs: `.cargo/config.toml` замінює crates.io на `vendor/`. Активний вкладений SENS шлях використовує 7 пакетів / 296 файлів / **4,419,723 Б** у SENS checkout; SHA та розмір кожного файла закріплені у [`external_build_dependency_inventory.vendored_external_packages`](../evidence/nano-sens-seed-v0-source-closure-census-2026-10-12.json). Це сторонні crate-джерела, класифіковані як зовнішні й не включені до trusted-seed subtotal. `git rev-parse HEAD` залишається runtime-вимогою. Цей активний пакетний ledger не дорівнює повному `vendor/` checkout: у pinned дереві є **81 package roots / 3,963 tracked files / 141,366,139 Б** загального vendor footprint, який теж є зовнішнім і не входить у trusted seed. Двопрогонна runtime-траса показала, що Cargo успішно відкриває **444 vendor-файли / 4,940,765 Б**: усі 296 файлів семи вибраних crate-пакетів плюс 148 `Cargo.toml`/`.cargo-checksum.json` metadata-файлів з інших 74 roots. Це спостережена subset-границя, не доведений мінімум; прунинг vendor-пакетів треба довести контрольованим чистим/offline replay. [Raw trace runs](https://github.com/juv4uk/cml/actions/runs/38187252311) залишаються в 30-денних артефактах.

**Runtime trace checkpoint:** [K1 run 38187252311](https://github.com/juv4uk/cml/actions/runs/38187252311) пройшов два traced clean runs, кожен 189/189. Обидва traces використовували runner SHA `6fbbc819eac32253d9eadb5e1dc8e80295bdb0bde9a285076edd8d7fc9e40eb3`, а size reports були байт-ідентичні (SHA-256 `965701a837f622b7484d20ce3303cda4da9d5b647e4ca3c38535dfe3800e2fe4`); raw syscall traces не мусять збігатися, бо містять різні тимчасові події. У run 1: 58,029 рядків trace / 48,447 file syscalls; run 2: 58,113 / 48,915. Артефакти raw traces: IDs `11719862489` і `11719953009`, expire 2026-11-11 UTC. **Оновлення path-by-path census:** follow-up [CML run 38187252311](https://github.com/juv4uk/cml/actions/runs/38187252311) завершився двома traced clean runs. Обидва незалежні census-и перелічили ті самі **562 repository-path файли** з path-set SHA-256 `53320597b6b55667498bbc8f7c2b0bee7a6ea05b723c9385e339f5cff8ec87ad`. У трасі спостерігались 444 vendor paths / **4 940 765 Б**. Це закриває заплановану path-list observation для того pinned checkpoint, але не доводить мінімальний dependency set чи повний seed closure.

**Виправлення обліку Git metadata:** попередній підсумок CML `.git` + SENS submodule `.git` + WSM `.git` помилково рахував SENS двічі, бо підмодульний gitdir розташований усередині `CML/.git/modules/external/sens`. Ці raw sums скасовано. Виправлений meter у [CML workflow commit `100f3017`](https://github.com/juv4uk/cml/commit/100f30174f728cf2564ceeb2348f58bd8ac7dd06) виключає SENS gitdir із CML часткового підсумку, а SENS рахує рівно один раз. Найсвіжіший clean-run snapshot дав **35,515,603 Б** і **35,519,818 Б** для неперетинних CML/SENS/WSM gitdirs; різниця між прогонами підтверджує, що це повні checkout metadata snapshots, а не мінімізований набір refs/objects. [CI run 38186932277](https://github.com/juv4uk/cml/actions/runs/38186932277) пройшов обидва clean runs і compare. Ці зовнішні metadata не включені до operational subtotal. Повний ledger: [CML census та Git metadata report](https://github.com/juv4uk/cml/blob/master/evidence/nano-sens-cml-runner-input-census-2026-10-12.json).

CML `Cargo.lock` мав конкретну похибку: `sens 0.41.0` не містив edge до `serde`; перша команда `cargo tree --locked` це відхилила. Lock виправлено комітом [`c41704c`](https://github.com/juv4uk/cml/commit/c41704cbbd9e6f0b6c4c12597ab5e50da6ac66a3): 29,360 Б, blob `b9bd778db07efa1a1883665939707612063e2e2c`. Зовнішній CML граф має `syn 3.0.4`, вкладений SENS `xtask` — `syn 3.0.3`. На найсвіжішому [CI run 38186932277](https://github.com/juv4uk/cml/actions/runs/38186932277) обидва Cargo graph captures пройшли `--locked`, lock-файли не змінилися, а графи збіглися byte-for-byte. CML registry/cache bytes досі зовнішні й не виміряні.

CML `Cargo.lock` мав конкретну похибку: `sens 0.41.0` не містив edge до `serde`; перша команда `cargo tree --locked` це відхилила. Lock виправлено комітом [`c41704c`](https://github.com/juv4uk/cml/commit/c41704cbbd9e6f0b6c4c12597ab5e50da6ac66a3): 29,360 Б, blob `b9bd778db07efa1a1883665939707612063e2e2c`. Зовнішній CML граф має `syn 3.0.4`, вкладений SENS `xtask` — `syn 3.0.3`. На [CI run 38186651984](https://github.com/juv4uk/cml/actions/runs/38186651984) обидва Cargo graph captures пройшли `--locked`, lock-файли не змінилися, а графи збіглися byte-for-byte (попередній locked pass також збережено як історичний checkpoint). CML registry/cache bytes досі зовнішні й не виміряні. Повний ledger: [CML census та Git metadata report](https://github.com/juv4uk/cml/blob/master/evidence/nano-sens-cml-runner-input-census-2026-10-12.json).

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

Проміжний машинозчитуваний census: [`SENS source closure`](../evidence/nano-sens-seed-v0-source-closure-census-2026-10-12.json). Окремо зафіксовано [CML runner input census](https://github.com/juv4uk/cml/blob/master/evidence/nano-sens-cml-runner-input-census-2026-10-12.json) для pinned CML `3320fe3b00a4a099ecb9ff06e22e0be2b1fee499`: 62 default `cargo test --lib` module sources + 8 root/build/contract files = 70 paths / 1,320,729 Б. Follow-up CI `38185559594` на окремому CML checkpoint `e2f76f63017add8574f6c5224bf3a80857927faf` пройшов обидва clean runs і compare; для нього runner має SHA-256 `ea865f2911d7322319f96be0d3a25b555c59c62370dd5bdc25d3bde355c7ead3`, розмір 34,580,920 Б. Його не порівнювати як оптимізаційний виграш/програш з попереднім K1 runner `fe5b...` / 34,575,192 Б: це різні source checkpoints. Поточний SENS census: **117 pinned paths / 1,432,402 Б** у перевіреному subset (70 production Rust sources, 20 Cargo package manifests, 27 root/authority/embedded and CML-consumed inputs). Виправлено дві протилежні похибки попереднього census: вилучено 3,271-Б `bootstrap_measurement.rs`, доступний лише під `#[cfg(test)]`, і додано 13 compile-time include-файлів з `lib.rs` та пов’язаних production-модулів (разом 254,906 Б; 13-й — `lib/core.lisp`). Subtotal-и CML та SENS мають різні межі й не є seed-total.

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

Це **перевірені subset-и, не остаточний мінімальний closure**. Уже записано 70 production Rust source files SENS/xtask, 20 workspace manifests, відомі compile-time include inputs і 70 CML source/metadata paths. Відомі vendored crates виміряні окремо й виключені як зовнішні; повний `.git` snapshot також виміряний, але мінімальний набір refs/objects не встановлений. CML-only Git dependency `wsm-os-target` pinned на `d3663026dbcce73e2b8e32238910c3f8f7dea833`: повний repo tree = 22 tracked files / 48,742 Б; вибраний compile-source subset = 4 files / 24,935 Б, також класифікований як зовнішня залежність ([деталі в CML census](https://github.com/juv4uk/cml/blob/master/evidence/nano-sens-cml-runner-input-census-2026-10-12.json)). Залишаються автоматичне вичерпне підтвердження `cfg`/module-графа обох репозиторіїв, чистий controlled/offline replay із виміром registry/cache availability, усі runtime file reads і generated outputs. Тому `whole_chain_seed_closure_status = BLOCKED_PARTIAL_LOWER_BOUND_NOT_COMPLETE_OR_MINIMIZED`; одне число для повного seed наразі не публікується.

### K2 — перший кандидат після closure-аудиту

Поточний вузький target: **Rust transport/exporter** `crates/xtask/src/compiler_export.rs`, який читає D3/D4 identity-only corpus, викликає `sens::compiler_semantic_input_from_sens` і сам форматує compiler-semantic-request. Сам role-law вже виконується з `lib/compiler-nucleus.lisp` через `crates/sens/src/compiler_language.rs`; його не переносити до другої Rust-таблиці й не дублювати значення в Lisp.

K2 candidate — перенести формування запитів/обхід дев'яти fixture-рядків до SENS-owned програми та залишити в хості тільки представницькі механізми, pinned provenance й execution boundary. Спочатку довести побайтний паритет зі старим exporter і негативне fail-closed поводження. Якщо для запуску нової програми все одно потрібен окремий Cargo-built `xtask`, trusted-seed reduction не зараховується.

**Обов'язкова передумова перед K2:** замкнути мінімальний file closure і baseline bundle-total. Далі кожну заміну вимірювати як ціле: trusted-seed bytes (у межах повного closure) та independence-index окремо; індекс спершу визначити як прозорий ledger компонентів із формулою, а не довільний скаляр. Повний CML library corpus, fail-closed негативні випадки, lineage та два чисті byte-identical runs залишаються обов'язковими.


## Статичний Rust source-edge audit — 12.10.2026

[CI run 38190527591](https://github.com/juv4uk/sens/actions/runs/38190527591) на snapshot `a825e5d3d0afe615869117e0e2d22b926493a862` завершився **SUCCESS**. Окремий self-test аналізатора пройшов **7/7** позитивних і негативних перевірок. Аудит зафіксував три точні snapshots:

| Snapshot | Rust-файли | Статичні source edges | Невирішені observations у межах аналізатора |
|---|---:|---:|---:|
| SENS main snapshot `a825e5d3d0afe615869117e0e2d22b926493a862` | 77 | 111 | 0 |
| Pinned SENS `d0787a40fcea36501747732aa61b6de19fe29c70` | 71 | 90 | 0 |
| Pinned CML `ec4ba010cebd9fdc37b39224142dcac3ee907cfe` | 66 | 83 | 0 |

**Трактування:** нуль unresolved observations означає, що аналізатор не залишив невирішених ребер у своїй підтриманій статичній моделі для цих snapshots. Це **не** означає, що seed мінімальний або весь ланцюг замкнений: аналізатор сам називає відкритими active `cfg`-resolution (це не результат `rustc` для кожної конфігурації), dynamic include paths, build-script/proc-macro та environment inputs, Cargo/workspace dependency closure, vendor/registry/cache, Git refs/objects, toolchain/OS/shared libraries і контрольований clean offline replay.

Попередній успішний snapshot `96ee15564d7a707d31664dca6e55b331d76ea6de` у [run 38190369519](https://github.com/juv4uk/sens/actions/runs/38190369519) дав ті самі три набори лічильників. Довготривалий receipt з точними SHA, лічильниками та межами тверджень: [`evidence/nano-sens-static-source-edges-2026-10-12.json`](../evidence/nano-sens-static-source-edges-2026-10-12.json). Три raw machine-readable reports збережені в [найновішому CI artifact 11721233152](https://github.com/juv4uk/sens/actions/runs/38190527591/artifacts/11721233152), ZIP SHA-256 `52a95e38a40ee603350bc255440c0b1f9c6144de613ff43c2478ba1a9a8f8e6e`; raw artifact доступний до **11.11.2026 01:05:52 UTC**.

Це новий доказовий шар — **статична інвентаризація джерел**, а не новий запуск компілятора, не перерахунок seed bytes і не дозвіл оголосити повний seed total.
