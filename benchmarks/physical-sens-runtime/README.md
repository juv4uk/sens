# Фізичний SENS — об’єктивний runtime benchmark

Вимірюються **реальні виконувані файли** `.sens` у release-збірці з точним
T5-транспортом, канонічною D2-структурою та D3 QUOTE-послідовностями.

Стенд навмисно відділяє:
- **`sens-exec`** — запуск `sens file.sens`, включно з cold process, T5, D2 і виконанням;
- **`sens-trit-eval`** — другий CLI тієї ж реалізації; parity обов'язкова, це *не* конкурент іншою мовою;
- **`rust-t5-view`** і **`python-t5-view`** — незалежні реалізації відкриття й відображення того самого T5 без виконання;
- **обсяг файлів** — packed T5 проти пробільного ASCII-перегляду, у байтах.

Проведення: 3 прогрівальні і 19 вимірюваних запусків кожної lane
на кожному навантаженні (1, 16, 128 і 1024 незалежних форм).
Порядок lane чергується; записуються **сирі наносекунди**, медіана, p95,
пропускна здатність у формах/с, SHA-256 і версії середовища.

```bash
cargo build --release --locked -p sens-cli --bin sens --bin sens-trit
python3 benchmarks/physical-sens-runtime/run.py \
  --sens target/release/sens \
  --sens-trit target/release/sens-trit \
  --out /tmp/sens-physical-bench --reps 19 --warmups 3
```

Вихід: `raw.tsv`, `results.json`, `environment.json`, `report.md`.
На GitHub — workflow `physical-sens-benchmark.yml`, GitHub-hosted runner.

**Заборона хибних висновків:** час із запуском процесу не є чистим часом
обчислень; однаковий SENS oracle в обох CLI не є міжмовною перевіркою.
Спільний runner має фонове навантаження, тому окремі p50/p95 — свідчення,
не жорстка регресійна межа. Немає доказу переваги над Python як
повноцінною мовою без окремого спільного алгоритмічного workload.
