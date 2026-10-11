# Міжмовні бенчмарки SENS

Цей каталог вимірює **конкретні реалізації**, а не абстрактні "мови".
Перший зовнішній орієнтир — CPython (#1546). Lua (#1547), Racket CS
(#1548) і стандартний binary-trees (#1549) додаються окремими slices.

## Current D1–D8 boundary

Fresh cross-language SENS evidence is now governed by the current D1–D8 model:

- canonical identity = exact domain + exact bits;
- current SENS rows must be tagged `d1-d8-current`;
- historical flat-byte function identity is archive-only and may not appear in a fresh measured path;
- English is a surface/control, never semantic authority;
- #1668 is the replay/correctness gate;
- #3088/#3113 own paired English-surface vs canonical-D1–D8 evidence.

The historical `run.py` and `load_formats.py` lanes are preserved for provenance.
They must not be relabeled as current D1–D8 results.

### External controls available now

`external_controls.py` provides an independent, current-era control slice for
CPython, Lua 5.4 and Racket CS on the same five workloads:

```text
fib loop ackermann closures evenodd
```

Every runtime must produce the same expected result before timing. The first slice
records full-process Cachegrind I refs and wall time only. It deliberately emits
**no SENS row** until #1668/#3088/#3113 are GREEN.

Run only correctness:

    guix time-machine -C channels.scm -- shell \
      -m manifest.scm \
      -m benchmarks/cross-language/manifest.scm -- \
      python3 benchmarks/cross-language/external_controls.py --check-only

Run measurements:

    guix time-machine -C channels.scm -- shell \
      -m manifest.scm \
      -m benchmarks/cross-language/manifest.scm -- \
      python3 benchmarks/cross-language/external_controls.py \
        --reps 3 \
        --out /tmp/sens-external-controls

This gives a clean external baseline while the current canonical SENS runtime
finishes its replay/preflight spine. It is not an abstract-language ranking.

## Правила чесності

1. Правильність перевіряється **до** вимірювання.
2. Однакові алгоритм, параметри і очікувана відповідь.
3. У першому корпусі немає workload, де Python list міг би нечесно
   замінити Lisp pair/cons: лише fib, loop, ackermann, closures, evenodd.
4. **Лише історичний `run.py`:** його SENS lane використовує архівний
   flat-byte FASL і не є поточним D1–D8 доказом. Новий
   `external_controls.py` навмисно не має SENS-рядка до GREEN #1668/#3088/#3113.
5. Фази не змішуються:
   - startup — порожній процес/сесія;
   - load — прочитати й декодувати/скомпілювати програму без виконання;
   - ready — той самий load + setup/module initialization, без benchmark-call;
   - repeat N — той самий ready path + N benchmark-calls;
   - steady execution у звіті = (repeat N - ready) / N;
   - Cachegrind використовує мале N (default 3), бо I refs детерміновані й дорогі;
   - native wall/CPU використовує більше N (default 100), щоб process noise не домінував короткі workload.
6. Основне відтворюване мірило — кількість інструкцій Cachegrind.
   Wall/user time і RSS додаються окремо; вони не повинні підміняти
   instruction-count через шум self-hosted runner.
7. Таблиця показує workload-by-workload співвідношення реалізацій і не
   оголошує глобального "переможця мови".

## Запуск

Спочатку зібрати існуючий SENS benchmark binary:

    cargo build --release -p sens --example ci_bench

Далі в закріпленому Guix-середовищі:

    guix time-machine -C channels.scm -- shell \
      -m manifest.scm \
      -m benchmarks/cross-language/manifest.scm -- \
      python3 benchmarks/cross-language/run.py \
        --sens-bench target/release/examples/ci_bench

Для швидкої перевірки лише відповідей:

    python3 benchmarks/cross-language/run.py \
      --sens-bench target/release/examples/ci_bench \
      --check-only

Результат містить instructions.tsv, runtime.tsv, environment.json і report.md.

Steady execution навмисно не рахується як `full - load`: на коротких
програмах це різниця двох великих process-level чисел і вона може потонути
в шумі. Matched `ready` / `repeat N` ампліфікує саме виконання call,
залишаючи однаковий load/setup шлях по обидва боки віднімання.


## Перший steady-state witness

Run 36318596454 (head 320886c5, self-hosted wsm-i5-6400) уперше дав GREEN
matched measurement. На п'яти workload геометричне CPython/SENS за
Cachegrind I refs = 0.021, тобто поточний SENS evaluator виконує приблизно
47.6× більше інструкцій у steady execution. Водночас SENS startup був
приблизно 34.5× дешевшим.

Цей witness збережений як історична точка до environment optimization #1558.
Він не повинен підміняти повторний вимір після злиття #1558.


## Standard binary-trees scaffold (#1549)

The CLBG binary-trees workload has a pinned provenance note and an N=10
correctness oracle in this directory:

    python3 benchmarks/cross-language/binary_trees_reference.py --check-fixture

This is correctness infrastructure only. The SENS measured adapter is added
after canonical 2-part COND (#1663) lands, then it must reuse the same
cross-language phases and machine-readable result schema. No upstream timing
number is imported as our evidence.
