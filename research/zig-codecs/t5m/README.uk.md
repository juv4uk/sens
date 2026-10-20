# Zig ↔ asm ↔ Rust T5M · механічний парний бенчмарк

**T5M — дефолтний фізичний носій SENS:** 5 трітів/байт (`3^5 = 243 < 256`),
роздільник-трит 2. Це **окрема тека**, яка **не чіпає** чинний харнес
`research/zig-codecs/t5/`: той самий драйвер і той самий кодек, плюс новий
**асемблерний** бекенд. T5 і T5M тут — один і той самий кодек (5 трітів/байт).

## Бекенди

| бекенд | джерело | що міряє |
|---|---|---|
| `zig` | `research/zig-codecs/t5/bench.zig` (кодек `t5/t5.zig`) | word → byte (end-to-end) |
| `asm` | `research/zig-codecs/t5m/bench_asm.zig` + `research/asm-t5m/t5m_words.S` + `t5m_pack.S` | word → byte (end-to-end) |
| `rust` | `crates/sens/examples/zig_t5_matched_bench.rs` | word → byte (end-to-end) |

Усі бекенди міряють той самий шлях **слово→байт / байт→слово**, тож рядки
прямо порівнювані; спільний інваріант — рівність фізичних байтів.

## Запуск (ручний; потрібні Linux x86_64, Zig 0.16.0, Rust/Cargo, `as`, libc)

```bash
python3 research/zig-codecs/t5m/run_paired_bench.py \
  --out-dir /tmp/sens-zig-asm-rust-t5m --pairs 3
cat /tmp/sens-zig-asm-rust-t5m/STATUS
cat /tmp/sens-zig-asm-rust-t5m/summary.md
```

Драйвер збирає всі бекенди, **звіряє повну рівність фізичних байтів і
фікстур між ними ДО таймінгу** і лише тоді публікує таблицю. Якщо паритет не
пройшов — `BLOCKED_NO_TIMING`, а не вигаданий speedup. Можна обмежити бекенди:
`--impls zig,asm` (без Rust).

## Результати (p50 нс/оп, `--impls zig,asm`)

Див. анотацію `RESULTS-2026-10-20.uk.md`. Коротко:

| Форми | Операція | zig | asm |
|---:|---|---:|---:|
| 1 | encode / decode | 52.5 / 203.8 | 35.6 / 35.5 |
| 16 | encode / decode | 507.6 / 1559.7 | 588.1 / 570.5 |
| 128 | encode / decode | 4005.7 / 10952.0 | 3060.9 / 4174.1 |
| 1024 | encode / decode | 27806.2 / 72740.4 | 24181.6 / 38365.0 |

## Що НЕ доведено

Пам'ять/алокації, cachegrind, cold startup, bootstrap CI — **NOT_MEASURED**.
Це транспортна механіка, **не** SENS-семантика і **не** дозвіл на production
cutover. Важкі бенчмарки — лише ручний режим; нових автоматичних workflow не
додано (єдина автоматична точка — наявна `ci.yml`).

Raw samples: `samples.jsonl`; environment/SHA: `environment.json`.
