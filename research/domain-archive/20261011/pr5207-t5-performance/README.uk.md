# Історичний bench/perf донор PR #5207

Точний оригінал з https://github.com/juv4uk/sens/pull/5207
Head SHA: `b7d2b965020f0d6045db86fe70466c8148d47371`.

Усі 3 Git-блоби перенесено незмінними (SHA кожного файла збережено); структура каталогів повторює первинні шляхи.
**Це архів дослідження T5, не production зміна чинного `main`.**
Не переписувати поточний `crates/sens/src/ternary_transport.rs` кодом зі старої гілки: в ньому є новіші незалежні зміни. Збережено для порівняльних benchmark, oracle replay та потенційної вибіркової інтеграції тільки після незалежного CI.

- `.github/workflows/t5-decoder-paired-ab.yml`
- `benchmarks/physical-sens-runtime/paired_decoder.py`
- `crates/sens/src/ternary_transport.rs`
