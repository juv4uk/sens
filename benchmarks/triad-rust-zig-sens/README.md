# Конкурс бенчмарків: три незалежні сфери

**Rust відповідає за механізм; Zig — за фізичний коридор; SENS — за семантику та логіку.**
Механічна точність байтів не є доказом мовного закону. Мовний закон
перевіряється виконанням SENS-свідка та його негативного мутанта.

Активний ручний workflow: [`.github/workflows/sens-performance.yml`](../../.github/workflows/sens-performance.yml).
Він складається з **трьох незалежних jobs**, а не змішаного рейтингу.
Кожен job зберігає сирі дані окремо й позначає їх SHA Git-коміту.
Відсутність свідка або зламана збірка = RED, не синтетичний PASS.

| Учасник | Що реально виконує | Де код | Дані |
|---|---|---|---|
| Rust · механізм | 512 копій незмінних байтів `lib/core4.lisp` у кожній пробі; точність `dest == source` за межами таймера | `benchmarks/mechanism/rust-byte-copy-bench.rs` | 1 прогрів + 11 проб, p50/p90/min/max наносекунд на batch |
| Rust · механізм | Packed/decoded exact-width слова без приписування їм функцій SENS | `crates/sens/examples/byte_pack_bench.rs` | 9 проб, фізичні байти, біти, raw p50/p90 ns/word |
| Rust · енергія механізму | Пакет справжніх D3 `owner_residency()` lookup; **без** перевірки мовної істини | `benchmarks/measurement-triad/src/bin/rapl_mechanism.rs` | Linux RAPL package, сирі µJ, тривалість, `J/lookup`; BLOCKED без лічильника |
| Zig · коридор | Той самий файл, 512 фізичних копій; порівняння байтів поза таймером | `benchmarks/mechanism/zig-byte-copy-bench.zig` | 1 прогрів + 11 проб, p50/p90/min/max наносекунд на batch |
| Zig · коридор | Справжній T5M encode/decode, фізична byte parity, від'ємні кадри | `bench_t5m.zig`, `bench_t5m_test.zig`, `research/zig-codecs/tests.zig` | 11 адаптивних проб T5M, ns/op, перевірки кодеків |
| SENS · логіка | Нативний SENS закон структури та хибний мутант через `--t5m-files`; два реальні D1-вердикти | `tests/semantic/бенчмарк-структура-{law,mutant}.lisp`, `scripts/prove-бенчмарк-структура.sh` | 11 виконань, p50/p90 мкс повного процесу, позитив/негатив |

## Відтворення локально

У корені репозиторію:

```sh
# Rust: механічне копіювання, байти без Lisp-eval
rustc -O --edition=2021 benchmarks/mechanism/rust-byte-copy-bench.rs -o /tmp/sens-rust-copy
/tmp/sens-rust-copy

# Rust: exact-width pack/decode, а не таблиця SENS-логіки
cargo run --locked --release -p sens --example byte_pack_bench -- series mixed 1024 9

# Rust: джоулі механізму через Linux powercap/RAPL; без сенсового оракула.
# Потрібен фізичний Linux-хост із package RAPL, інакше чесний BLOCKED.
export SENS_ROOT="$PWD"
( cd /tmp && cargo run --release \
    --manifest-path "$SENS_ROOT/benchmarks/measurement-triad/Cargo.toml" \
    --bin rapl_mechanism -- 1000000 7 )
# Zig 0.16: фізичний коридор, тести БАЙТІВ, не функцій
zig test -O ReleaseFast -lc benchmarks/mechanism/zig-byte-copy-bench.zig
zig test -lc research/zig-codecs/tests.zig
zig test -O ReleaseFast -lc bench_t5m_test.zig
zig run -O ReleaseFast -lc bench_t5m.zig

# SENS: лише виконуваний власний закон + негативний мутант
cargo build --locked -p sens-cli --bin sens --bin sens-trit --features benchmark-ast-visits
bash scripts/prove-бенчмарк-структура.sh "$PWD/target/debug/sens"
```

Той самий протокол у GitHub Actions можна запускати вручну через
**Actions → SENS contest → Run workflow**. Workflow не публікує артефакти
з неіснуючих Rust-тестів, не вигадує `results.txt`/`law-timings.tsv`
і не сертифікує відсутні свідки.

## Як судити результати

1. **Не складати швидкості різних сфер.** Rust вимірює механізм, Zig —
   транспорт, SENS — повний процес із завантаженням, читанням та виконанням.
   Навіть byte-copy у Rust/Zig — порівняльне фізичне навантаження, не доказ
   «швидкості мови».
2. **Точність завжди перед рейтингом.** Для Rust/Zig необхідна побайтова
   тотожність; для SENS — позитивний закон і негативний мутант.
   Будь-який RED дискваліфікує відповідну пробу.
3. **Публікувати raw, SHA, компілятори, апаратну платформу й одиниці.**
   Жодних чисел із попереднього коміту. На shared CI шум, різні job-машини
   й cache роблять міжмовний speedup непідтвердженим.
4. **Енергія — окрема метрика.** Джоулі можна вказувати лише за вимірюванням
   RAPL/powercap/perf на конкретній машині з вказаним доменом, інтервалом і
   похибкою; за відсутності лічильника писати `NOT_MEASURED`, не `0 J`.
5. **Не підмінювати SENS-оракул shell-таблицею.** Історичний
   `benchmarks/contest-uk/judge.sh` ще має очікувані результати всередині Bash.
   Поки ці твердження не перенесено до самоперевірних SENS-свідків,
   його результати НЕ є семантично сертифікованими для цього тристороннього конкурсу.

## Межа релізу

Цей workflow — **ручне вимірювання**. Він не замінює P0 релізу
`translation_boundary` і `wsm_fs_f6_pipeline`, не додає дозволу
публікувати реліз і не оголошує всі мовні закони SENS доведеними.

Методика: [paired benchmarking](../bench-methodology/README.md).
