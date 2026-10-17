# Результати benchmark SENS vs CPython

> **ІСТОРИЧНИЙ EVALUATOR-ПРОГІН, НЕ фізичний T5-vs-Python-source доказ.**
> SENS тут виконував попередньо розібране дерево через Rust `Session`; це не
> підтверджує швидкодію фізичного тритового виконуваного файла. Див.
> [фізичний source-to-result pilot](../../physical/runs/20261017T053621Z/README.uk.md).

Run: `20261017T052024Z`
SENS HEAD: `d5141f0287eed1c4a35c16755bd0ce457048c2c5` · CPython `3.12.12` · `rustc 1.99.0 (b940084d7 2026-09-28)`
Host: desktop · Intel(R) Core(TM) i5-6400 CPU @ 2.70GHz · Linux-6.18.33.2-microsoft-standard-WSL2-x86_64-with-glibc2.41
SENS binary SHA-256: `2b6a12bd787507deeb5f6bbc40a33549649518a932dad4c62de5f8a228432ba6` · manifest SHA-256: `2d679bc1b96c7fd22e2c23ea84dbb4a2aacbcff69854979f7870e5484162ccb4`

Порядок пар workload-ів: `[{"workload": "binary-trees", "implementations": ["SENS", "CPython source"]}, {"workload": "fib", "implementations": ["CPython source", "SENS"]}, {"workload": "ackermann", "implementations": ["SENS", "CPython source"]}]`.

Таймінг включає лише виклик уже завантаженої реалізації. Запуск процесу, підготовка й перевірка parity виключені.

Ratio `CPython/SENS` — медіана CPython, поділена на медіану SENS; значення нижче 1 означає менший час CPython.

| Workload (параметри) | Статус | Реалізація | Parity | n | median (µs) | p95 (µs) | p99 (µs) | RSS baseline/peak/Δ (KiB) | CPython/SENS median |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| binary-trees (N=10) | PASS | SENS | PASS | 100 | 412755.500 | 447424.552 | 459688.438 | 6840/6904/64 | 0.048× |
| binary-trees (N=10) | PASS | CPython source | PASS | 100 | 19795.712 | 26263.617 | 34379.106 | 13436/13480/44 | — |

| fib (N=16) | PASS | SENS | PASS | 100 | 5677.792 | 7487.621 | 10239.891 | 6800/6864/64 | 0.035× |
| fib (N=16) | PASS | CPython source | PASS | 100 | 201.279 | 373.148 | 560.363 | 13420/13428/8 | — |

| ackermann (m=3, n=3) | PASS | SENS | PASS | 100 | 4566.541 | 6017.730 | 7837.281 | 7000/7064/64 | 0.041× |
| ackermann (m=3, n=3) | PASS | CPython source | PASS | 100 | 189.386 | 258.272 | 1271.327 | 13464/13468/4 | — |

| json-parse-serialize (input_fixture=fixtures/json-small.json) | BLOCKED | — | — | — | — | — | — | — | — |

| n-body (—) | BLOCKED | — | — | — | — | — | — | — | — |

| mandelbrot (—) | BLOCKED | — | — | — | — | — | — | — | — |

| regex (—) | BLOCKED | — | — | — | — | — | — | — | — |

## Обмеження

p99 за 100 спостережень фактично є другим найбільшим значенням і не характеризує далекий хвіст. RSS — процесний VmRSS після warmup та VmHWM після вимірів; він включає середовище виконання й алокатор.

Зіставляються однакові алгоритми, визначені у SENS source та Python `.py`. SENS виконує вже розібране/понижене source-дерево через поточний exact evaluator; CPython під час імпорту `.py` компілює його у внутрішній bytecode, але готовий `.pyc` не використовується. Таймінг не вимірює парсер або startup: він порівнює конкретні runtime-шляхи evaluator проти CPython VM, а не фізичні представлення чи властивість мов загалом.

Збалансований повтор показав міжзапусковий розкид медіан, тому одиничні коефіцієнти не є стабільними константами. Загальний переможець не оголошується; workload-и відрізняються за навантаженням.

Невиконані workload-и:
- `json-parse-serialize`: У поточному exact reader приймається D9 JSON-parse identity, але немає викличного Core runtime mechanism; змішане source-ім’я не зв’язане. Не підміняти історичним W8 builtin або host-парсером поза SENS.
- `n-body`: Немає підтвердженої зіставної поточної числової семантики/точності SENS і CPython для запропонованого workload.
- `mandelbrot`: Немає підтвердженої зіставної поточної числової семантики/точності SENS і CPython для запропонованого workload.
- `regex`: Не визначено спільний regex engine і контракт поведінки.

Повні raw samples і метадані лежать у `raw/`; графіки побудовано без фільтрації samples.
