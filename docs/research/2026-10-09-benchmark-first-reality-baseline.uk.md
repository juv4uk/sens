# SENS: перший числовий базис benchmark-first (9 жовтня 2026)

> **Доказ, не ратифікація та не рекорд швидкості мови.** Наведені цифри взято
> із завершеного **успішного** GitHub-hosted Actions
> [Current physical SENS performance benchmarks #37980932549](https://github.com/juv4uk/sens/actions/runs/37980932549),
> SHA `b12ee66a7d12f8b488d0ca93c485aa1456e3064e`, job `113990944439`.
> CPU: **AMD EPYC 7763 64-Core Processor**. Результати актуальні **тільки**
> для цього SHA, корпусу й runner'а; у наступних ревізіях обов'язково
> вимірювати повторно. Тривалість компіляції не включено.

## Фізичний формат і процеси

Реальні release-команди `sens <file.sens>` та `sens-trit eval <file.sens>`;
19 вимірів після 3 прогрівань. p50/p95 — настінний час з запуском процесу,
читанням файла, T5-декодуванням і виконанням.

| D3 QUOTE форми | Packed T5, Б | ASCII 0/1, Б | T5 / ASCII | `sens` p50, мс | `sens` p95, мс | `sens-trit eval` p50, мс |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 4 | 17 | 0.235 | 1.383 | 1.571 | 1.275 |
| 16 | 55 | 272 | 0.202 | 1.309 | 1.570 | 1.220 |
| 128 | 435 | 2176 | 0.200 | 1.400 | 1.547 | 1.287 |
| 1024 | 3482 | 17408 | 0.200 | 2.143 | 2.252 | 1.992 |

**Теза, яку підтримують виміри:** для 1024 повторених D3 QUOTE пакований
T5 у `17408 / 3482 ≈ 5.00×` компактніший, ніж видима послідовність
доменних слів із пробілами. Це порівняння *двох представлень того самого
коду*, не порівняння розмірів рівноцінних програм Python/C/Lisp.

## Гарячий T5 → D2 без запуску процесу

11 незалежних серій, рівно однакові physical T5 байти й D2-граматика.
Метрика — p50, наносекунд на одну пачку з зазначеною кількістю форм.

| Форми | T5→видимий текст→D2, нс | T5→typed words→D2, нс | Visible / typed |
|---:|---:|---:|---:|
| 1 | 972 | 553 | 1.758× |
| 16 | 13 713 | 6 495 | 2.111× |
| 128 | 104 981 | 49 981 | 2.100× |
| 1024 | 1 093 451 | 549 341 | 1.990× |

**Теза:** прямий typed-word шлях виміряно приблизно вдвічі швидшим за
шлях із матеріалізацією видимого тексту для цих *самих* операцій reader'а.
Це **не** 2× пришвидшення всієї мови чи native CPU eval. Інші фази,
особливо startup, мають окремий бюджет.

## Власні виконувані D5-програми

Фізичні програми перевірені на однаковий stdout у `sens` і
`sens-trit eval`. Гаряче `eval_lowered`: 9 серій по 64 виклики;
процес і CLI startup виключено.

| Програма | Доменних слів | Physical T5, Б | `eval_lowered` p50, нс/виклик | p95, нс/виклик |
|---|---:|---:|---:|---:|
| D5 LABEL recursion | 78 | 54 | 5 502 | 5 797 |
| D5 LABEL copy | 96 | 66 | 8 620 | 8 757 |
| D5 LABEL MAP | 135 | 95 | 12 652 | 13 386 |

Це різні задачі; швидкості цих трьох рядків **не** є взаємними
коефіцієнтами прискорення. CLI parity — механічний запобіжник, не
незалежний Lisp-оракул.

## Рішення для наступного вимірювального циклу

1. Використовувати **чинні** hosted benchmark workflows
   `.github/workflows/physical-sens-benchmark.yml`,
   `sens-reality-bench.yml`, `sens-performance.yml`; не множити їх.
   Архівувати raw samples, Git SHA, SHA256 бінарників/корпусу, CPU,
   `rustc`, параметри repetitions і warmup.
2. До нових headline-заяв вимірювати окремо: cold startup, exact T5→D2,
   lowering, warm execution, p50/p95, фізичні байти і Cachegrind
   інструкції/слово. Витрати на typed-width/framing ніколи не ховати.
3. Порівняння з CPython, Chez, C, LuaJIT чи попереднім SENS — **лише**
   однаковий workload, доказ результату/оракула, однакове залізо,
   прогрітий та холодний режими, аналогічна методика. Блокований
   семантикою корпус маркувати `BLOCKED`, без вигаданого speedup.
4. Старі зелені benchmark-result та поточний червоний Hosted CI/
   Vertical Day можуть співіснувати. Перше **не є** доказом
   наскрізної семантичної правильності всіх поточних програм.

### Як повторити на GitHub-hosted runner

```bash
cargo build --locked --release -p sens-cli --bin sens --bin sens-trit
cargo build --locked --release -p sens \
  --example physical_sens_hot_bench --example physical_sens_d5_hot_bench
python3 benchmarks/physical-sens-runtime/run.py \
  --sens target/release/sens --sens-trit target/release/sens-trit \
  --reps 19 --warmups 3 --sizes 1,16,128,1024 --out /tmp/sens-physical
python3 benchmarks/physical-sens-runtime/hot.py \
  --binary target/release/examples/physical_sens_hot_bench \
  --sizes 1,16,128,1024 --samples 11 --work-budget 65536 \
  --out /tmp/sens-physical
```

Першоджерело чисел — прикріплений результат зазначеного GitHub Actions;
цей документ — **пінований історичний baseline**, не новий тест і не
підміна первинного артефакту.
