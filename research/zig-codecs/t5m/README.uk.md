# Zig ↔ asm ↔ Rust T5M · механічний парний бенчмарк

**T5M — дефолтний фізичний носій SENS:** 5 трітів/байт (`3^5 = 243 < 256`),
роздільник-трит 2. Це **окрема тека**, яка **не чіпає** чинний харнес
`research/zig-codecs/t5/`: той самий драйвер і той самий кодек, плюс новий
**асемблерний** бекенд. T5 і T5M тут — один і той самий кодек (5 трітів/байт);
«t5m» — назва дефолтного носія.

## Бекенди

| бекенд | джерело | що міряє |
|---|---|---|
| `zig` | `research/zig-codecs/t5/bench.zig` (кодек `t5/t5.zig`) | word → byte (end-to-end) |
| `asm` | `research/zig-codecs/t5m/bench_asm.zig` + `research/asm-t5m/t5m_pack.S` | ядро pack/unpack (trit → byte) |
| `rust` | `crates/sens/examples/zig_t5_matched_bench.rs` | word → byte (end-to-end) |

**Важливо про межі:** `zig`/`rust` міряють повний шлях слово→байт, а `asm` — лише
ядро пакування на вже побудованому потоці тритів. Тому рядки **не прямо
порівнювані** між собою; спільне в них — рівність фізичних байтів.

## Запуск (ручний; потрібні Linux x86_64, Zig 0.16.0, Rust/Cargo, `as`, libc)

```bash
python3 research/zig-codecs/t5m/run_paired_bench.py \
  --out-dir /tmp/sens-zig-asm-rust-t5m --pairs 3
cat /tmp/sens-zig-asm-rust-t5m/STATUS
cat /tmp/sens-zig-asm-rust-t5m/summary.md
```

Драйвер збирає всі три бекенди, **звіряє повну рівність фізичних байтів і
фікстур між ними ДО таймінгу** і лише тоді публікує таблицю. Якщо паритет не
пройшов — `BLOCKED_NO_TIMING`, а не вигаданий speedup. Можна обмежити бекенди:
`--impls zig,asm` (без Rust).

## Результати (локально в сендбоксі, p50 нс/оп, `--impls zig,asm`)

| Форми | Операція | zig (word→byte) | asm (ядро) |
|---:|---|---:|---:|
| 1 | encode | 39.6 | 6.8 |
| 1 | decode | 137.6 | 14.3 |
| 16 | encode | 356.1 | 79.4 |
| 16 | decode | 1096.1 | 187.8 |
| 128 | encode | 2671.8 | 644.4 |
| 128 | decode | 7295.7 | 1638.3 |
| 1024 | encode | 21114.5 | 5217.7 |
| 1024 | decode | 56739.1 | 12465.4 |

## Що НЕ доведено

Пам'ять/алокації, cachegrind, cold startup, bootstrap CI — **NOT_MEASURED**.
Це транспортна механіка, **не** SENS-семантика і **не** дозвіл на production
cutover. Важкі бенчмарки — лише ручний режим; нових автоматичних workflow не
додано (єдина автоматична точка — наявна `ci.yml`).

Raw samples: `samples.jsonl`; environment/SHA: `environment.json`.
