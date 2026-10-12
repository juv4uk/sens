# Міжмовні бенчмарки SENS

## Current authority override — Contract 11.9 / D1–D10 residency

Current language authority is `language-contract.lisp` Contract 11.9.
D1–D10 are owner-ratified as semantic residents, but residency is not the
same as executable runtime authority. D10 F1/F2/F3 evidence and physical T5
execution remain pending and must fail closed. D24+ numeric domains are
separately owner-ratified.

Historical rows (including D1–D4, D1–D8 and Contract 11.6/11.8) remain valid
provenance for the exact generation that produced them; they must not be
relabeled as current Contract 11.9 evidence. A fresh row must record its exact
Git SHA, Contract 11.9, semantic generation, corpus/artifact provenance and
semantic parity before timing. Missing mechanisms are explicit
`BLOCKED-MECHANISM`; never fall back to Sens8/Sid8/Function8.

The sections below preserve older harness documentation unless explicitly
marked otherwise.

Цей каталог вимірює **конкретні реалізації**, а не абстрактні "мови".
Перший зовнішній орієнтир — CPython (#1546); Lua 5.4 (#1547) і Racket CS
(#1548) використовують той самий корпус та machine-readable формат.
Standard binary-trees (#1549) лишається окремим workload slice.

## Current Python-comparison status — Contract 11.9

The existing `run.py` is a **historical harness**, not a current SENS benchmark:
its SENS lane encodes and decodes the old Function8 FASL artifact. Do not use
its output as current Contract 11.9 evidence or as a current Python-vs-SENS
ratio. #1546 tracks the Python replay; #1668 owns the correctness gate.

Current semantic authority is D1–D10 residency, with execution authority
proved separately per mechanism. D10 F1/F2/F3 evidence and physical T5 execution
remain pending. A workload may be timed only after oracle correctness and exact
canonical-domain parity pass; otherwise report `BLOCKED-MECHANISM` (or the
specific parity blocker). No Sens8/Sid8/Function8 fallback is permitted.

The Python comparison must preserve the five workloads
`fib, loop, ackermann, closures, evenodd` and split phases into process startup,
CPython `.py` read+compile, reproducibly generated `.pyc` load, canonical SENS
decode, setup/ready, repeated execution and one-shot. Pin exact SENS main SHA,
CPython version, environment and raw samples before publishing results.

## Historical D1-D4 boundary

The historical shared harness still uses the old Function8 FASL SENS lane.
It is preserved for provenance but must not be relabeled as current D1-D4
whole-program evidence. #1668 owns the replay onto the currently ratified
canonical exact-width domains.

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
        --sens-bench target/release/examples/ci_bench \
        --historical-function8-fasl  # provenance only; not current Contract 11.9

Для швидкої перевірки лише відповідей:

    python3 benchmarks/cross-language/run.py \
      --sens-bench target/release/examples/ci_bench \
      --check-only --historical-function8-fasl

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
matched measurement **для тодішнього історичного SENS evaluator**. На п'яти
workload геометричне CPython/SENS за Cachegrind I refs = 0.021: тодішній SENS
evaluator використовував приблизно 47.6× більше інструкцій у steady execution.
Водночас SENS startup був приблизно 34.5× дешевшим.

Це лише історичний результат старого Function8/FASL покоління. Він не є
показником Contract 11.9, не є wall-clock ratio і не повинен підміняти свіжий
canonical replay після #1668. Поточний run.py усе ще використовує FASL, тож
до міграції та GREEN parity жоден новий результат цього harness не можна
публікувати як актуальне порівняння SENS із Python.



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