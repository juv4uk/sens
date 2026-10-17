# Бенчмарк SENS і CPython

> **Методологічне застереження:** `runs/20261017T051528Z`,
> `runs/20261017T051819Z` і `runs/20261017T052024Z` вимірювали source-level
> SENS через попередньо завантажений Rust `Session`/exact evaluator проти
> CPython. Це корисні історичні дані про ті два runtime-шляхи, але **не**
> benchmark фізичного тритового T5-файла проти Python `.py`. Не використовуйте
> їхні коефіцієнти як швидкість фізичної SENS-програми. Сирі дані збережені.
>
> Єдиний валідний у цій папці фізичний SENS-vs-Python прогін наразі — вузький
> D5 `LABEL COPY` source-to-result pilot у
> [`physical/runs/20261017T053621Z/README.uk.md`](physical/runs/20261017T053621Z/README.uk.md).
> Він запускає `sens-trit eval` на справжніх T5-байтах і CPython на `.py`
> джерелі, включаючи старт процесу. Це одна програма на одному хості, не
> загальний висновок і не вимір чистої швидкості обчислень.

Цей дослідницький зріз доповнює `benchmarks/cross-language/`, не змінюючи
історичний `run.py` (Function8/FASL) та попередні результати. Він порівнює
конкретні реалізації алгоритмів, а не абстрактні мови.

## Поточний обсяг

`workloads.json` є контрактом кандидатів, їхніх параметрів і стану parity.
Жоден workload не вимірюється до перевірки однакової відповіді. Початкові
виконувані кандидати — binary trees N=10, рекурсивний `fib` і малий
Ackermann-Péter `A(3,3)` із наявного міжмовного корпусу. JSON
parse/serialize лишається `BLOCKED`: поточний exact D9 JSON-parse не має
викличного Core runtime mechanism. Кандидат може лишитися `BLOCKED`, якщо поточний
SENS-owned execution path не підтримує потрібну операцію; не можна
підміняти його Function8/FASL, host-реалізацією під виглядом SENS або іншим
алгоритмом.

Порівнюється source-код workload-ів. Завантаження процесу, розбір джерела,
ініціалізація сесії та correctness gate відбуваються до таймінгу. Для
кожної реалізації виконуються 10 warmup-викликів і 100 окремо заміряних
викликів у тому самому процесі. Зберігаються всі latency samples та
provenance. Для короткого workload-а це вимірювання evaluator/runtime
boundary, а не загальна швидкодія мови.

CPython запускає `.py` і сам компілює його у внутрішній bytecode під час
імпорту; готовий `.pyc` не використовується (`-B`). Отже це зіставлення
однакових source-level алгоритмів, але різних фактичних runtime шляхів:
SENS exact evaluator проти CPython VM. Воно не є порівнянням фізичних
представлень source-коду і bytecode.

Звітуються median, p95 та p99 за nearest-rank. При `n=100` p99 дорівнює
максимальному порядковому sample і не є надійною оцінкою далекого хвоста.
RSS baseline знімається після setup і warmup; абсолютний `VmHWM` та його
delta від baseline включають allocator/runtime ефекти. Графіки будуються
лише зі збережених raw samples.

Загальний висновок про переможця заборонений, якщо менше трьох workload-ів
пройшли parity й отримали повні дані. У такому разі звіт показує лише
часткові результати та точні причини `BLOCKED`.

## Запуск

Залежності — чинний Rust toolchain і Python 3; Python-код використовує лише
стандартну бібліотеку. Спершу перевірте коректність без вимірювання:

```sh
cargo test --offline --manifest-path benchmarks/cross-language/sens-vs-python/runner/Cargo.toml
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s benchmarks/cross-language/sens-vs-python/tests -v
```

Перед benchmark потрібен свіжий `wsm-agent bench-ready` зі статусом `READY`.
Координатор сам перевіряє readiness, parity, 10 warmup, рівно 100 samples та
неперезапис run-каталогу; запуски йдуть послідовно. Release runner будується
після окремого READY:

```sh
cargo build --offline --release --manifest-path benchmarks/cross-language/sens-vs-python/runner/Cargo.toml -j 1
python3 -B benchmarks/cross-language/sens-vs-python/python/coordinate.py \
  --sens-runner benchmarks/cross-language/sens-vs-python/runner/target/release/sens-vs-python-bench
```

Кожен запуск створює унікальний `runs/<UTC timestamp>/` з `metadata.json`,
первинними JSON у `raw/`, графіками у `plots/` і звітом `report.uk.md`.
Аргумент `--run-id` дає змогу задати ідентифікатор; наявний каталог призводить
до відмови, а не перезапису. Відмова preflight означає, що виміри не слід
запускати вручну в обхід guard.

## Фактичні запуски

Фінальний збалансований запуск `20261017T052024Z` має три workload-и з
parity PASS і по 100 samples на сторону. Його медіани: binary trees N=10 —
SENS 412.756 ms, CPython 19.796 ms; fib N=16 — SENS 5.678 ms, CPython
0.201 ms; Ackermann A(3,3) — SENS 4.567 ms, CPython 0.189 ms. У цих трьох
вузьких профілях виміряний CPython швидший; це не є загальним рейтингом мов.
JSON, n-body, Mandelbrot і regex лишилися BLOCKED з описаних вище причин.

Є незалежний збалансований повтор `20261017T051819Z`. Медіани SENS у двох
збалансованих запусках відрізняються (наприклад, binary trees ~479 проти
413 ms), отже результати чутливі до системного шуму; не трактуйте відношення
як стабільну константу без повторів на контрольованішому host.
Ранній пілот `20261017T051528Z` з фіксованим порядком SENS-first збережений
окремо як калібрувальне свідчення; його не об’єднано з двома збалансованими
запусками.

Повний таблицевий звіт, метадані, raw samples і SVG збережені у
[`runs/20261017T052024Z/report.uk.md`](runs/20261017T052024Z/report.uk.md).
Перед використанням результатів звіряйте run ID і hash provenance.

Див. [шаблон звіту](report-template.uk.md) та [машинний інвентар](workloads.json).
