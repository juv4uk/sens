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
   - steady execution у звіті = (repeat N - ready) / N.
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
