# Потоковий T5-кодувальник: перший GitHub-hosted benchmark

**Статус:** реальні вимірювання на точному коді; не новий закон SENS.
Усі числа належать незмінному SHA
[`722a52344a2dc66b7f7102d8f1b2954b53da9eae`](https://github.com/juv4uk/sens/commit/722a52344a2dc66b7f7102d8f1b2954b53da9eae),
[GitHub Actions #37981141798 — SUCCESS](https://github.com/juv4uk/sens/actions/runs/37981141798).
[Сирі серії та середовище, artifact 11641320570](https://github.com/juv4uk/sens/actions/runs/37981141798/artifacts/11641320570).

Один GitHub-hosted runner Ubuntu 24.04, release-збірка Rust,
11 серій для кожного розміру; бенчмарк прогрівається всередині процесу.
**p50/p95 — нс на один виклик** кодувальника, без запуску процесу
та дискового читання. Той самий масив ратифікованих слів D2/D3 QUOTE.
Старий і новий шляхи до вимірювання відтворили **байт у байт** ті
самі фізичні T5-дані; ніякої нової семантики D1–D9.

| D3 QUOTE форм | Старий p50 нс | Старий p95 нс | Новий p50 нс | Новий p95 нс | p50 старий/новий |
|---:|---:|---:|---:|---:|---:|
| 1 | 109 | 110 | 70 | 71 | 1,557× |
| 16 | 923 | 932 | 789 | 796 | 1,170× |
| 128 | 6 244 | 6 332 | 5 942 | 5 963 | 1,051× |
| 1 024 | 48 896 | 50 192 | 47 852 | 49 273 | 1,022× |

## Що змінилося

У `crates/sens/src/ternary_transport.rs` колишній `Vec<u8>` повного
набору тритів замінено однопрохідним накопиченням рівно п'яти тритів
безпосередньо у вихідному байті. Транспортний `2` лишився
**лише межею між двійковими словами й фінальним padding**.

У `crates/sens/examples/physical_sens_hot_bench.rs` лишився
двопрохідний контроль `two_pass_t5_allocation_control`, але
**не як частина runtime**, а як незалежний від нового коду
механічний еталон для побайтового та часово́го порівняння.

## Межа висновку

Це вимірювання кодування T5 **без** D2 AST, SENS eval, GC, I/O
або CPU-native lowering. Прискорення на цьому невеликому корпусі
не є прогнозом для інших програм чи іншого hardware.
Зменшення проміжної алокації обґрунтоване кодом; окремого
пікового RSS-замірювання тут немає. Повний Hosted CI
та Vertical Day слід оцінювати окремо.

Відтворення:

```bash
cargo build --release --locked -p sens --example physical_sens_hot_bench
python3 benchmarks/physical-sens-runtime/hot.py \
  --binary target/release/examples/physical_sens_hot_bench \
  --sizes 1,16,128,1024 --samples 11 --work-budget 65536 \
  --out /tmp/sens-physical-bench
```
