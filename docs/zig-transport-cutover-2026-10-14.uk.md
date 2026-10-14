# Перехід фізичного транспорту SENS на Zig · 14.10.2026

## Явне рішення власника: «переходим на зіг»

**Переходимо на Zig для фізичних кодеків та транспорту.** Мова SENS, її ратифіковані двійкові слова й D2/D3 закони, SENS evaluator, невідворотні нормативні рішення і 2046 координат **не перетворюються на Zig-семантику**. Zig володіє лише зовнішніми байтами, пакуванням, конвертом; зміна ідентичності через десятковий SID8/W8/Sens8 неприпустима.

### Вже реалізовані механізми (feature-gated cutover)

- `research/zig-codecs/t5/t5.zig` — незалежний exact-width T5; D1–D9, padding/width/canonicality.
- `research/zig-codecs/f3c/f3c.zig` — обмежений F3C, явний `.senc` з `0xf3`, без sniffing/fallback, тільки якщо весь файл коротший.
- `research/zig-codecs/transport.zig` — Zig фізичний файловий інструмент; `t5-check`, `t5-roundtrip`, `f3c-pack`, `f3c-check`, `f3c-unpack`; create-exclusive, вихідні дані зберігаються.
- `research/zig-codecs/transport_abi.zig` — Zig-owned синхронний C ABI v1: T5 validate/encode і F3C pack/unpack; **виклик не передає власності пам’яті через FFI**.
- `crates/sens-cli/build.rs` і `crates/sens-cli/src/bin/sens-trit.rs` — коли задано `--features zig-transport`, компілюється фізичний Zig ABI, `sens-trit encode`, `encode-f3`/F3C decode й фізична `.sens` перевірка користуються Zig, а Rust reader перевіряє канонічну граматику і виконує програму. Rust reference залишається як **перехідний контроль і сумісність збірок без Zig**.

## Відтворення на Linux з чинним піном Zig 0.16.0

```sh
zig version
zig test research/zig-codecs/tests.zig -lc
zig build-exe research/zig-codecs/transport.zig -O ReleaseFast -lc -femit-bin=target/sens-zig-transport
target/sens-zig-transport t5-check input.sens
target/sens-zig-transport f3c-pack input.sens output.senc
target/sens-zig-transport f3c-unpack output.senc restored.sens
cmp input.sens restored.sens
cargo build --locked -p sens-cli --bin sens-trit --features zig-transport
target/debug/sens-trit eval input.sens
target/debug/sens-trit eval-f3 output.senc
```

**Версія Zig впливає на відтворення збірки, не на wire.** Сьогодні центральний `.github/workflows/ci.yml` пінує Zig 0.16.0; ранні бенчмарки GitHub проводилися на 0.17.0. Висновки зі швидкості мають фіксувати точні версії, прапори й сирі SHA бінарників; швидкість `zig-transport` через Rust FFI сама собою не дорівнює microbenchmark цифрам Zig.

## Контракти безпеки

1. `t5-check` гарантує **лише транспорт**, не граматику і не право виконувати програму. Нативний SENS canonical D2+evaluator зберігає останнє слово.
2. F3C `.senc` декодується **тільки явно**; невірний маркер, байти чи недоведена форма — відмова. Немає автоматичного fallback на T5.
3. Відсутність економії означає використання T5, а не помилку вже канонічної програми.
4. Перед виконанням недовіреного `.senc` потрібен довірений **SHA-256 фізичного носія**, як у чинному `verify-f3-sha256`/`eval-f3-sha256`; проста внутрішня F3C мітка не забезпечує захист від підміни.
5. Діагностика кожного red має бути інформативною; semantic PASS вимагає реального нативного SENS виконання, не Rust/Zig самооцінки.

## Статус релізу

**Cutover у робочій гілці, не злитий у main.** Крок із `--features zig-transport` є практичною інтеграцією для доказу, а не доказом повної міграції всього core на Zig. Доки немає успішної компіляції ABI/нативної квитанції, повного корпусу файлів і інформативних green gates, **не вмикати Zig feature за замовчуванням для всього workspace**, не видаляти Rust reference і не стверджувати «production завершено». F3M лишається дослідницьким профілем. Конверт Zig — окрема ланка, метадані не можуть змінювати SENS-семантику.

Докази: [T5/F3C real paired benchmarks](../research/zig-codecs/RESULTS-2026-10-14.uk.md), [#5766](https://github.com/juv4uk/sens/issues/5766), [#5767](https://github.com/juv4uk/sens/issues/5767), [#5768](https://github.com/juv4uk/sens/issues/5768), [#5770](https://github.com/juv4uk/sens/issues/5770), [#5771](https://github.com/juv4uk/sens/issues/5771).
