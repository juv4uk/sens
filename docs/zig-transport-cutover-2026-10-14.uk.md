# Перехід фізичного транспорту SENS на Zig · 14.10.2026

## Явне рішення власника: «переходим на зіг» → «зроби дефолтним кодеком»

**Переходимо на Zig для фізичних кодеків та транспорту.** Мова SENS, її ратифіковані двійкові слова й D2/D3 закони, SENS evaluator, невідворотні нормативні рішення і 2046 координат **не перетворюються на Zig-семантику**. Zig володіє лише зовнішніми байтами, пакуванням, конвертом; зміна ідентичності через десятковий SID8/W8/Sens8 неприпустима.

### Вже реалізовані механізми (Zig за замовчуванням у sens-cli)

- `research/zig-codecs/t5/t5.zig` — незалежний exact-width T5; D1–D9, padding/width/canonicality.
- `research/zig-codecs/f3c/f3c.zig` — обмежений F3C, явний `.senc` з `0xf3`, без sniffing/fallback, тільки якщо весь файл коротший.
- `research/zig-codecs/transport.zig` — Zig фізичний файловий інструмент; `t5-check`, `t5-roundtrip`, `f3c-pack`, `f3c-check`, `f3c-unpack`; create-exclusive, вихідні дані зберігаються.
- `research/zig-codecs/transport_abi.zig` — Zig-owned синхронний C ABI v1: T5 validate/encode і F3C pack/unpack; **виклик не передає власності пам’яті через FFI**.
- `crates/sens-cli/build.rs` і `crates/sens-cli/src/bin/sens-trit.rs` — звичайна Cargo-збірка `sens-cli` компілює фізичний Zig ABI за замовчуванням, `sens-trit encode`, `encode-f3`/F3C decode й фізична `.sens` перевірка користуються Zig, а Rust reader перевіряє канонічну граматику і виконує програму. Rust reference залишається як **незалежний контроль**, а збірка Rust-only вмикається тільки явно через `--no-default-features` (не прихований fallback).

## Відтворення на Linux з чинним піном Zig 0.16.0

```sh
zig version
zig test research/zig-codecs/tests.zig -lc
zig build-exe research/zig-codecs/transport.zig -O ReleaseFast -lc -femit-bin=target/sens-zig-transport
target/sens-zig-transport t5-check input.sens
target/sens-zig-transport f3c-pack input.sens output.senc
target/sens-zig-transport f3c-unpack output.senc restored.sens
cmp input.sens restored.sens
cargo build --locked -p sens-cli --bin sens-trit
target/debug/sens-trit backend  # transport=zig abi=2 semantic_authority=SENS
target/debug/sens-trit eval input.sens
target/debug/sens-trit eval-f3 output.senc
```

**Типова збірка `sens-cli` тепер потребує Zig в PATH або `ZIG=/шлях/до/zig`.** Показати режим без Zig (лише явна сумісність): `cargo build --locked -p sens-cli --bin sens-trit --no-default-features` і `target/debug/sens-trit backend` → `transport=rust-reference semantic_authority=SENS`. Ця опція НЕ змінює формат T5/F3C і не є автоматичним fallback.

**Версія Zig впливає на відтворення збірки, не на wire.** Сьогодні центральний `.github/workflows/ci.yml` пінує Zig 0.16.0; ранні бенчмарки GitHub проводилися на 0.17.0. Висновки зі швидкості мають фіксувати точні версії, прапори й сирі SHA бінарників; швидкість `zig-transport` через Rust FFI сама собою не дорівнює microbenchmark цифрам Zig.

## Контракти безпеки

1. `t5-check` гарантує **лише транспорт**, не граматику і не право виконувати програму. Нативний SENS canonical D2+evaluator зберігає останнє слово.
2. F3C `.senc` декодується **тільки явно**; невірний маркер, байти чи недоведена форма — відмова. Немає автоматичного fallback на T5.
3. Відсутність економії означає використання T5, а не помилку вже канонічної програми.
4. Перед виконанням недовіреного `.senc` потрібен довірений **SHA-256 фізичного носія**, як у чинному `verify-f3-sha256`/`eval-f3-sha256`; проста внутрішня F3C мітка не забезпечує захист від підміни.
5. Діагностика кожного red має бути інформативною; semantic PASS вимагає реального нативного SENS виконання, не Rust/Zig самооцінки.

## Статус релізу

**Zig T5/F3C злитий у `main` через PR #5780; за новим прямим рішенням власника `zig-transport` — DEFAULT FEATURE лише пакета `sens-cli`.** У звичайній збірці `sens-trit` Zig створює фізичні байти, Rust/SENS core здійснює допуск і виконання. Для незалежного reference-run без Zig треба *явно* задати `--no-default-features`; якщо Zig відсутній у типовій збірці, збірка падає, а не відступає мовчки на Rust.

**Межа:** це НЕ зміна типової фізичної структури (`.sens` T5 і `.senc` F3C залишаються як були), не ввімкнення Zig у `sens` core/WASM/freestanding/FPGA, не завершення E1/E2/E3 і не оголошення зеленого релізу. Rust reference збережено до повного corpus-паритету. Загальний CI має відомий окремий RED SID8/D8 (#5778) — не маскувати. F3M лишається дослідним профілем. Конверт Zig не може змінювати SENS-семантику.

Докази: [T5/F3C real paired benchmarks](../research/zig-codecs/RESULTS-2026-10-14.uk.md), [#5766](https://github.com/juv4uk/sens/issues/5766), [#5767](https://github.com/juv4uk/sens/issues/5767), [#5768](https://github.com/juv4uk/sens/issues/5768), [#5770](https://github.com/juv4uk/sens/issues/5770), [#5771](https://github.com/juv4uk/sens/issues/5771).

## ABI v2, без Rust layout → SENS (14.10.2026)
- Основний `sens-trit` передає механічні слова Zig як caller-owned послідовність трійок байтів `[exact_width_u8, payload_MSB_u8, payload_LSB_u8]`. Це **тільки внутрішній ABI шлюзу**, не новий wire-format і не мовне значення SENS.
- Фізичні T5 байти виробляє тільки Zig; Rust передає ширину й біти як opaque payload, без доменних номерів, host-enum, `repr(C)` або native endian.
- `sens_zig_t5_encode_be3` відхиляє нецілі трійки, нульову/непідтримувану ширину, надлишковий payload і недостатню місткість буфера.
- `sens_zig_codec_abi_version() == 2`; попередній експорт `sens_zig_t5_encode` збережений для старого ABI-клієнта, але **за замовчуванням не викликається** із `sens-trit`. Поза межами host не переносити `usize/isize` у фізичний конверт.
- Доказ в `research/zig-codecs/transport_abi.zig`: різні фізичні T5 для D1:1 та D2:01, позитивний golden і негативні перекручені triplets. Це mechanical gate; семантичне рішення належить SENS.

## Обов'язкові парні бенчмарки кожного коміту · рішення власника 14.10.2026

**За прямим рішенням власника T5 та F3C benchmarks є обов'язковими для кожного GitHub push / PR**, незалежно від назви гілки або changed paths. Виконуються **тільки** в чинному автоматичному `.github/workflows/ci.yml`: Zig 0.16.0 (перевірений pinned download) ↔ Rust `--locked --release`, по **3 зовнішні парні серії** для кожного кодека на одному runner з перемішаним порядком запуску.

- До кожного timing підтвердити **побайтову ідентичність** Zig↔Rust (фізичний T5/F3C, не SENS-семантику). Parity mismatch, missing sample, невірний SHA / pin / invalid elapsed / відсутній артефакт **блокують CI**. Жодного мовчазного skip.
- Повинні існувати `STATUS`, `environment.json` із Git SHA, compiler version та SHA бінарників, `samples.jsonl`, `summary.md`. Обов'язковий evidence-gate звіряє **240 T5** та **120 F3C** рядків, обидва backend, рівно 3 пари. Окремий `upload-artifact` виконується навіть після помилки; відсутність артефакту — помилка.
- **Швидкість не є семантичною істиною**, і самі плинні таймінги GitHub-hosted runner не мають hardcoded fail-порогу. CI блокує непідтверджені/неповні виміри, а не повільніший Zig або Rust. Немає неправдивих заяв про 95% K–J interval чи продуктивність усього SENS.
- Це **обов'язковий фокусний mechanical benchmark**, а не автоматичне покриття всіх профілів, великий corpus, cross-target ESP32 або freestanding proof. Для цих задач вимоги #5770/#5771/#5772–#5775 залишаються відкритими.

Локальне відтворення (Zig 0.16.0 і Rust/Cargo доступні в PATH):
```sh
python3 research/zig-codecs/t5/run_paired_bench.py --zig-pin 0.16.0 --pairs 3 --out-dir /tmp/sens-t5-paired
python3 research/zig-codecs/f3c/run_paired_bench.py --zig-pin 0.16.0 --pairs 3 --out-dir /tmp/sens-f3c-paired
```
