# Результати benchmark SENS vs CPython

> **ІСТОРИЧНИЙ EVALUATOR-ПРОГІН, НЕ фізичний T5-vs-Python-source доказ.**
> SENS тут виконував попередньо розібране дерево через Rust `Session`; це не
> підтверджує швидкодію фізичного тритового виконуваного файла. Див.
> [фізичний source-to-result pilot](../../physical/runs/20261017T053621Z/README.uk.md).

Run: `20261017T051528Z`
SENS HEAD: `d5141f0287eed1c4a35c16755bd0ce457048c2c5` · CPython `3.12.12` · `rustc 1.99.0 (b940084d7 2026-09-28)`
Host: desktop · Intel(R) Core(TM) i5-6400 CPU @ 2.70GHz · Linux-6.18.33.2-microsoft-standard-WSL2-x86_64-with-glibc2.41
SENS binary SHA-256: `17332d1c655a426071d6c959b2a13fd15d5c99632925be5d922d09a65531c43c` · manifest SHA-256: `c1c74a19310ff283f9591601d8d131185e6c8f3815cd298289a40ee708c9fe23`

Таймінг включає лише виклик уже завантаженої реалізації. Запуск процесу, підготовка й перевірка parity виключені.

Ratio `CPython/SENS` — медіана CPython, поділена на медіану SENS; значення нижче 1 означає менший час CPython.

| Workload (параметри) | Статус | Реалізація | Parity | n | median (µs) | p95 (µs) | p99 (µs) | RSS baseline/peak/Δ (KiB) | CPython/SENS median |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| binary-trees (N=10) | PASS | SENS | PASS | 100 | 537683.334 | 823311.129 | 1003279.760 | 6800/6864/64 | 0.074× |
| binary-trees (N=10) | PASS | CPython source | PASS | 100 | 39776.745 | 60863.105 | 63099.975 | 13488/13536/48 | — |

| fib (N=16) | PASS | SENS | PASS | 100 | 14773.458 | 18231.115 | 28156.516 | 6776/6840/64 | 0.015× |
| fib (N=16) | PASS | CPython source | PASS | 100 | 218.186 | 570.990 | 1891.204 | 13424/13432/8 | — |

| ackermann (m=3, n=3) | PASS | SENS | PASS | 100 | 5353.224 | 14491.532 | 15797.273 | 6964/7028/64 | 0.036× |
| ackermann (m=3, n=3) | PASS | CPython source | PASS | 100 | 191.966 | 234.443 | 4898.811 | 13424/13428/4 | — |

| json-parse-serialize (input_fixture=fixtures/json-small.json) | BLOCKED | — | — | — | — | — | — | — | — |

| n-body (—) | BLOCKED | — | — | — | — | — | — | — | — |

| mandelbrot (—) | BLOCKED | — | — | — | — | — | — | — | — |

| regex (—) | BLOCKED | — | — | — | — | — | — | — | — |

## Обмеження

p99 за 100 спостережень фактично є другим найбільшим значенням і не характеризує далекий хвіст. RSS — процесний VmRSS після warmup та VmHWM після вимірів; він включає середовище виконання й алокатор.

SENS вимірюється через поточний exact source reader/evaluator, CPython — через виклик функції в CPython. Це зіставлення конкретних runtime-ів, не чиста властивість мов. Загальний переможець не оголошується; workload-и відрізняються за навантаженням.

Невиконані workload-и:
- `json-parse-serialize`: У поточному exact reader приймається D9 JSON-parse identity, але немає викличного Core runtime mechanism; змішане source-ім’я не зв’язане. Не підміняти історичним W8 builtin або host-парсером поза SENS.
- `n-body`: Немає підтвердженої зіставної поточної числової семантики/точності SENS і CPython для запропонованого workload.
- `mandelbrot`: Немає підтвердженої зіставної поточної числової семантики/точності SENS і CPython для запропонованого workload.
- `regex`: Не визначено спільний regex engine і контракт поведінки.

Повні raw samples і метадані лежать у `raw/`; графіки побудовано без фільтрації samples.
