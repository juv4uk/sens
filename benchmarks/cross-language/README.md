# Міжмовні бенчмарки SENS

Цей каталог вимірює **конкретні реалізації**, а не абстрактні "мови".
Перший зовнішній орієнтир — CPython (#1546); Lua 5.4 (#1547) і Racket CS
(#1548) використовують той самий корпус та machine-readable формат.
Standard binary-trees (#1549) лишається окремим workload slice.

## Правила чесності

1. Правильність перевіряється **до** вимірювання.
2. Однакові алгоритм, параметри і очікувана відповідь.
3. У першому корпусі немає workload, де Python list міг би нечесно
   замінити Lisp pair/cons: лише fib, loop, ackermann, closures, evenodd.
4. SENS виконується з FASL, де функція SENS — один байт. CPython виконує
   звичайний source/bytecode шлях своєї реалізації. Lua 5.4 читає source
   через `loadfile`; benchmark fail-fast перевіряє саме major/minor 5.4.
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

## Lua 5.4 (#1547)

Lua не має окремої «вигідної» версії workload. Ті самі `fib`, `loop`,
`ackermann`, `closures`, `evenodd` генеруються з тими самими параметрами
і expected answers.

Matched driver `lua_driver.lua` має ті самі фази, що SENS/CPython:

- `load` — `loadfile`, chunk не виконується;
- `ready` — chunk виконується й повертає `{ bench = ... }`, але `bench`
  не викликається;
- `repeat N` — той самий ready path + N викликів `bench`;
- `full` — ready + один `bench` із друком відповіді.

Raw `instructions.tsv` і `runtime.tsv` не отримали нової схеми: Lua просто
є третім значенням колонки `implementation`. Це дозволяє порівнювати всі
три реалізації одним downstream-аналізом без паралельного формату.

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



## Racket CS (#1548)

Racket отримує ті самі `fib, loop, ackermann, closures, evenodd`, ті самі
параметри й expected answers. Harness fail-fast перевіряє, що
`racket --version` повідомляє CS runtime (`[cs]`).

Matched driver `racket_driver.rkt` розділяє фази так:

- `load` — `read-syntax` + `compile` module, без instantiation;
- `ready` — compiled module declaration + `dynamic-require ... #f`, без `bench`;
- `repeat N` — той самий ready path + N викликів exported `bench`;
- `full` — ready + один `bench` із друком відповіді.

Raw TSV schema не змінюється: `racket` — ще одне значення колонки
`implementation`. Report додає Racket CS поруч із SENS/CPython/Lua.

Racket source adapter не залежить від SENS COND syntax. Публікувати нові
SENS-comparative performance claims усе одно можна лише після #1668,
коли SENS benchmark corpus буде replay-нутий на canonical 2-part COND.

## Standard binary-trees scaffold (#1549)

The CLBG binary-trees workload has a pinned provenance note and an N=10
correctness oracle in this directory:

    python3 benchmarks/cross-language/binary_trees_reference.py --check-fixture

This is correctness infrastructure only. The SENS measured adapter is added
after canonical 2-part COND (#1663) lands, then it must reuse the same
cross-language phases and machine-readable result schema. No upstream timing
number is imported as our evidence.