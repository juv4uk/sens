# Історичний bench/perf донор PR #5221

Точний оригінал з https://github.com/juv4uk/sens/pull/5221
Head SHA: `1036e46060dc2f27c29fad4e9f0c4ecb6ddbb48c`.

Усі 4 Git-блоби перенесено незмінними (SHA кожного файла збережено); структура каталогів повторює первинні шляхи.
**Це архів дослідження T5, не production зміна чинного `main`.**
Не переписувати поточний `crates/sens/src/ternary_transport.rs` кодом зі старої гілки: в ньому є новіші незалежні зміни. Збережено для порівняльних benchmark, oracle replay та потенційної вибіркової інтеграції тільки після незалежного CI.

- `.github/workflows/physical-sens-benchmark.yml`
- `benchmarks/physical-sens-runtime/hot.py`
- `crates/sens/examples/physical_sens_hot_bench.rs`
- `crates/sens/src/ternary_transport.rs`
