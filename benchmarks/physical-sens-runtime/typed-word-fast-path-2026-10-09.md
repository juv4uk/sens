# Прямий T5 → W1–W9 → D2: два виміряні прискорення (2026-10-09)

**Стан:** два завершені успішні GitHub-hosted benchmark runs. Жодних нових мовних законів або surface-імен у Rust.

Механічна оптимізація: декодер T5 уже повертає точні слова з ширинами; D2 тепер читає їх напряму через `parse_canonical_word_sequence`. Попередній шлях ще раз пакував W1–W9 у щільний payload, а потім розпаковував перед тим самим D2 читачем.

**Порівняння в межах кожного runner** — p50 нс на операцію, процес не перезапускався, ті самі T5 bytes, D2 reader і спостережуваний результат; 11 незалежних серій після прогріву, 65 536 сумарних форм.

| D3 QUOTE форм | #37978837927 старий | новий | old/new | #37978901191 старий | новий | old/new |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 731 | 654 | 1.118× | 397 | 315 | 1.260× |
| 16 | 7 858 | 6 618 | 1.187× | 4 751 | 3 874 | 1.226× |
| 128 | 58 894 | 50 985 | 1.155× | 33 739 | 30 503 | 1.106× |
| 1024 | 620 689 | 544 347 | 1.140× | 386 307 | 337 354 | 1.145× |

- [GitHub Actions #37978837927](https://github.com/juv4uk/sens/actions/runs/37978837927), SUCCESS, SHA `f6e38437ba803bd898effdb4ecc9e62a22f124a7`.
- [GitHub Actions #37978901191](https://github.com/juv4uk/sens/actions/runs/37978901191), SUCCESS, SHA `a850896b836610ad1ac10d27c9b5d0df2b289fbc`.
- Кожен artifact містить `hot-raw.tsv`, `hot-results.json`, `hot-environment.json`, `hot-report.md`.

**Обмеження:** це виміряний механічний шлях T5→D2 на конкретному D3 QUOTE наборі, а не whole-language швидкість, не D5 рекурсія, не CPython/C/Rust порівняння, не GPU/FPGA. Абсолютні ns між shared GitHub runners різняться; пари старий/новий порівнюються *всередині одного запуску*. Код не створює нових семантичних резидентів.

**Незалежний safety signal:** `Physical binary SENS CLI smoke` зелений на SHA `9e537ccaad893da80274d9b6961be417d9c44713`. Повний Hosted CI на тому SHA залишається червоним через legacy тричленний D3:110 `COND` у `time.lisp`; green performance ≠ green Vertical Day.

Відтворити:
```bash
cargo build --locked --release -p sens --example physical_sens_hot_bench
python3 benchmarks/physical-sens-runtime/hot.py --binary target/release/examples/physical_sens_hot_bench --out /tmp/sens-hot --samples 11 --work-budget 65536
```
