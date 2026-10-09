# Міжмовні бенчмарки SENS

## Current authority override — Contract 11.8 / D1–D9

Current language authority is `language-contract.lisp` Contract 11.8:
D1–D9 are the ratified current foundation; D10 is research. Canonical identity
is exact bits + exact domain + admitted/proved law.

This directory contains several **historical benchmark generations** as well as
reusable measurement machinery. Historical D1–D4, D1–D8 and Contract 11.6
rows remain valid provenance for the exact generation that produced them, but
they must never be relabeled as current Contract 11.8 evidence.

Fresh current replay is coordinated by #4129. Current rows must record
`contract_version=11.8`,
`semantic_generation=contract-11-8-exact-d1-d9`, exact git/corpus/artifact
provenance, and semantic parity before timing. Missing D9 execution mechanisms
are explicit `BLOCKED-MECHANISM`; they must not fall back to historical
Sens8/Sid8/Function8 paths.

The sections below preserve older harness documentation unless explicitly
marked otherwise.

Цей каталог вимірює **конкретні реалізації**, а не абстрактні "мови".
Перший зовнішній орієнтир — CPython (#1546); Lua 5.4 (#1547) і Racket CS
(#1548) використовують той самий корпус та machine-readable формат.
Standard binary-trees (#1549) лишається окремим workload slice.

## Historical D1-D4 boundary

The historical shared harness still uses the old Function8 FASL SENS lane.
It is preserved for provenance but must not be relabeled as current D1-D4
whole-program evidence. #1668 owns the replay onto ratified exact-width D1-D4.

For load-format evidence, `load_formats.py` adds a fairer CPython cached lane:

- CPython source: UTF-8 read + `compile()`;
- CPython `.pyc`: direct magic/header validation + marshal code-object decode;
- SENS: prebuilt historical Function8 FASL decode.

The `.pyc` artifact is generated before timing by the same CPython version.
Raw repetitions and binary/runtime provenance are emitted next to the summary.

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