# Результати benchmark SENS vs CPython

> **ІСТОРИЧНИЙ EVALUATOR-ПРОГІН, НЕ фізичний T5-vs-Python-source доказ.**
> SENS тут виконував попередньо розібране дерево через Rust `Session`; це не
> підтверджує швидкодію фізичного тритового виконуваного файла. Див.
> [фізичний source-to-result pilot](../../physical/runs/20261017T053621Z/README.uk.md).

Run: `20261017T051819Z`
SENS HEAD: `d5141f0287eed1c4a35c16755bd0ce457048c2c5` · CPython `3.12.12` · `rustc 1.99.0 (b940084d7 2026-09-28)`
Host: desktop · Intel(R) Core(TM) i5-6400 CPU @ 2.70GHz · Linux-6.18.33.2-microsoft-standard-WSL2-x86_64-with-glibc2.41
SENS binary SHA-256: `17332d1c655a426071d6c959b2a13fd15d5c99632925be5d922d09a65531c43c` · manifest SHA-256: `c1c74a19310ff283f9591601d8d131185e6c8f3815cd298289a40ee708c9fe23`

Порядок пар workload-ів: `[{"workload": "binary-trees", "implementations": ["SENS", "CPython source"]}, {"workload": "fib", "implementations": ["CPython source", "SENS"]}, {"workload": "ackermann", "implementations": ["SENS", "CPython source"]}]`.

Таймінг включає лише виклик уже завантаженої реалізації. Запуск процесу, підготовка й перевірка parity виключені.

Ratio `CPython/SENS` — медіана CPython, поділена на медіану SENS; значення нижче 1 означає менший час CPython.

| Workload (параметри) | Статус | Реалізація | Parity | n | median (µs) | p95 (µs) | p99 (µs) | RSS baseline/peak/Δ (KiB) | CPython/SENS median |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|
| binary-trees (N=10) | PASS | SENS | PASS | 100 | 479119.675 | 736477.134 | 775475.167 | 6804/6868/64 | 0.044× |
| binary-trees (N=10) | PASS | CPython source | PASS | 100 | 21194.172 | 37953.565 | 47609.218 | 13444/13492/48 | — |

| fib (N=16) | PASS | SENS | PASS | 100 | 6388.918 | 16127.487 | 17404.448 | 6808/6872/64 | 0.034× |
| fib (N=16) | PASS | CPython source | PASS | 100 | 217.528 | 330.558 | 632.910 | 13424/13432/8 | — |

| ackermann (m=3, n=3) | PASS | SENS | PASS | 100 | 4505.768 | 6104.714 | 8029.888 | 7000/7064/64 | 0.041× |
| ackermann (m=3, n=3) | PASS | CPython source | PASS | 100 | 185.359 | 304.589 | 555.204 | 13344/13348/4 | — |

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
