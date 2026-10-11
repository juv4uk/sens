# Nano-SENS seed-v0 — виміряний baseline (2026-10-12)

Статус: **PASS — два незалежні чисті прогони; звіти байт-ідентичні.** Це перший виміряний operational seed-v0, не мінімальний і не SENS-native seed.

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

Baseline gate зелений; дослідницькі кампанії можуть починатися послідовно, але не об'єднуватися в один результат.

1. **K1 — static-link + strip C1:** окремий baseline/variant, повні тести, lineage та два чистих запуски; не стирати секції без їхнього окремого обліку.
2. **K2 — заміна Rust-компонентів на SENS-програму:** кожну заміну перевіряти окремо. Вести дві незалежні метрики — trusted-seed bytes та чітко визначений independence-index.
3. **K3 — Framed-3 self-extracting seed:** research-only, з окремими encode/decode, semantic witness і fail-closed negative tests.
4. **K4 — slot-VM:** окремий виконавчий варіант і міст до microcpu; повний corpus та збіг observables до заміни runtime.

Перед K2–K4 перевірити донорські матеріали: stage0/hex0 на [bootstrappable.org](https://bootstrappable.org/), SectorLisp та TinyCC. Наведені як орієнтири розміри донорів не порівнювати з цим seed, доки не збігаються межі байтів, target і правила обліку. Історичні Lisp — донори/тести, не автоматичне ядро.

## Семантичні межі

- Contract 11.8 зберігає семантичну владу. Rust, GCC, linker, codec і VM — механізми/свідки, не джерела мовного значення.
- D10 дослідний і не є залежністю Nano-SENS. У поточному `knowledge/d10-v1-semantic-inventory.json` на main зафіксовано **675/1024** selected research candidates, 349 remaining, 0 ратифікованих D10 residents. Це не підтверджує формулювання 1024/1024 selected; іншу цифру змінювати лише після перевірки конкретного SHA та відповідного ledger.
- Нових гілок, доменів або семантичних таблиць для Nano-SENS не створювати.

**Висновок першого етапу:** метрика більше не BLOCKED. Seed-v0 = 34,580,696 bytes on-disk; обидва незалежні чисті звіти збігаються байт у байт. Оптимізація не входила до цього baseline.


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
