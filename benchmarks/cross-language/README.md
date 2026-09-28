# Міжмовні бенчмарки SENS

Цей каталог вимірює **конкретні реалізації**, а не абстрактні "мови".
Перший зовнішній орієнтир — CPython (#1546). Lua (#1547), Racket CS
(#1548) і стандартний binary-trees (#1549) додаються окремими slices.

## Правила чесності

1. Правильність перевіряється **до** вимірювання.
2. Однакові алгоритм, параметри і очікувана відповідь.
3. У першому корпусі немає workload, де Python list міг би нечесно
   замінити Lisp pair/cons: лише fib, loop, ackermann, closures, evenodd.
4. SENS виконується з FASL, де функція SENS — один байт. CPython виконує
   звичайний source/bytecode шлях своєї реалізації.
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
