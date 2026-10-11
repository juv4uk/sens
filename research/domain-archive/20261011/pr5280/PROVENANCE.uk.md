# Історичний знімок PR #5280 — Native Machine №1

Статус: ТІЛЬКИ АРХІВ ДОКАЗІВ. Не виконуваний канон і не production benchmark.

Джерело: https://github.com/juv4uk/sens/pull/5280
Зафіксований head PR: `3d1ac0441821475b68267b2af63c6be4557d0a3a`. Базою архівного включення був `main@365921409ce39b473883cd3f5dec9bb6e2899d79`.
Файли збережено побайтно через існуючі Git blob SHA у власному архівному префіксі; активні шляхи не змінено.
Початкові результати: вимірювання на AMD EPYC 7763, різні workload не порівнювати як speed ratio.
На вихідному PR native u64 CAR/CDR BLOCKED через тричастинний COND; не видавати за PASS.

Початкові Git blob SHA:
- `.github/workflows/native-machine-benchmark-1.yml`: `cae2a5846c7ab10564413c8d8633ec53ecc9678d` (added)
- `benchmarks/README.md`: `0c9f42d81f73dddd1e3403ec51f1f1f288a5329f` (modified)
- `benchmarks/native-machine-1/README.md`: `a5e2794e0b4d4f7f4decdbabadf4ea2c4448a941` (added)
- `benchmarks/native-machine-1/bench.json`: `db4b3d371956ac984cb57a930943797a1d7fb087` (added)
- `benchmarks/native-machine-1/summarize.py`: `0b6f4ab4b96fe570f26722217388e7dec3018ddd` (added)
- `benchmarks/native-machine-1/test_summarize.py`: `5cf8f8747194e5d789d80ac6a6b02db38074d2ea` (added)
- `crates/sens-host/examples/native_machine_bench.rs`: `1302209ea276334665069c990b404bc77f3ad2fe` (added)

Повторне використання — тільки після перевірки оракулів, exact current SHA, CI та семантичних меж D1–D9.
