# Бенчмарки механізмів Rust і Zig та мови SENS

Механізми перевіряємо тією мовою, яка їх реалізує. `rust-byte-copy-bench.rs` та `zig-byte-copy-bench.zig` копіюють **ті самі байти** `lib/core4.lisp`, кожен має прогрів, 11 проб по 512 копій, p50/p90 та перевірку цілісності даних. Мовних законів у цих бенчмарках **немає**.

`rustc -O benchmarks/mechanism/rust-byte-copy-bench.rs -o /tmp/sens-rust-bench && /tmp/sens-rust-bench`

`zig test -O ReleaseFast -lc benchmarks/mechanism/zig-byte-copy-bench.zig`

**SENS:** наявні `benchmarks/lists.lisp`, `benchmarks/arithmetic.lisp`, `benchmarks/parser.lisp`, `benchmarks/recursion.lisp` запускаються окремо у CI. Їхні закони і мутанти належать `tests/semantic/`, виконання — виключно нативному SENS через Zig/T5M.

Числа Rust/Zig не є рейтингом мов: компілятор, цільова машина, виділення пам'яті та оптимізації відрізняються. Так само час повного SENS CLI, який містить bootstrap, не є чистим часом eval. На загальному GitHub runner не виставляємо автоматичних порогів прискорення, а зберігаємо p50/p90, розмір і SHA коміту. Інваріант — точне копіювання, а не задана швидкість.

Для подальшого розвитку: Criterion.rs (статистика та регресії), hyperfine (прогрів і зовнішні процеси), CL-Bench (окреме вимірювання виконання Lisp), офіційний Zig 0.16 (змінені API таймерів).
