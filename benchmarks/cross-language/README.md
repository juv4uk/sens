# Міжмовні бенчмарки SENS

Цей каталог вимірює **конкретні реалізації**, а не абстрактні "мови".
Порівняння виконуються лише на однакових workload, параметрах і очікуваних
відповідях.

## Поточна межа — Contract 11.5

Чинна семантична основа SENS:

```text
CURRENT:  D1 D2 D3 D4 D5 D6
RESEARCH: D7 D8
MECHANICS: W1-W8
```

D6 має ратифіковану ідентичність 64/64, але не кожен resident обов'язково має
runtime-механізм. Тому benchmark окремо фіксує semantic residency і callability.
Жоден fresh SENS row не може проходити через Sens8/Sid8/Function8.

Correctness gate для нового міжмовного порівняння: #1668. D6 mechanism coverage:
#3394. Протокол вимірювань: #1987.

## Зовнішні контролі

`external_controls.py` запускає однаковий п'ятизадачний корпус:

```text
fib
loop
ackermann
closures
evenodd
```

Реалізації:

- CPython — динамічний mainstream baseline (#1546);
- Lua 5.4 — компактний інтерпретатор (#1547);
- Racket CS — Lisp-family implementation control (#1548);
- SBCL — classic Common Lisp/native compiler control (#3410);
- optimized Rust — native machine-code lower-bound control (#3411).

Rust source компілюється через `rustc -O` **до** execution timing. Compile cost не
змішується з runtime cost і буде окремою фазою. SBCL не є семантичним
авторитетом для SENS — це лише близький Lisp-контроль.

Поки #1668 не GREEN на current exact-domain D1-D6, цей harness навмисно не
емітує SENS timing row. Це дозволяє отримати чисті зовнішні baseline-и без
підміни нової мови історичними Function8 цифрами.

### Correctness only

```bash
guix time-machine -C channels.scm -- shell \
  -m manifest.scm \
  -m benchmarks/cross-language/manifest.scm -- \
  python3 benchmarks/cross-language/external_controls.py --check-only
```

### Measurements

```bash
guix time-machine -C channels.scm -- shell \
  -m manifest.scm \
  -m benchmarks/cross-language/manifest.scm -- \
  python3 benchmarks/cross-language/external_controls.py \
    --reps 3 \
    --out /tmp/sens-external-controls
```

Результат містить:

- `external-full.tsv` — сирі рядки;
- `environment.json` — git SHA, версії runtime/compiler, CPU, параметри;
- `report.md` — медіани I refs і wall time.

## Правила чесності

1. Правильність перевіряється **до** будь-якого timing.
2. Однакові алгоритм, параметри та expected result.
3. Primary CPU metric — Valgrind Cachegrind I refs; wall time — допоміжний.
4. Source/load/compile/setup/steady execution не можна змішувати в одному
   висновку. Поточний external-control-v2 є лише full-process першою фазою.
5. Precompiled/native artifacts порівнюються окремо від source compilation.
6. Raw rows завжди несуть provenance: SHA, runtime/compiler versions, параметри.
7. Таблиці показують реалізації workload-by-workload; не проголошують
   універсального "переможця мови".
8. Historical Function8/Sens8 результати не входять у fresh Contract 11.5 ratios.

## Історична точка

Run 36318596454 (head 320886c5, self-hosted i5-6400) — старий Function8-era
witness. На п'яти workload геометричне CPython/SENS за Cachegrind I refs було
0.021, тобто тодішній SENS evaluator виконував приблизно 47.6× більше
інструкцій у steady execution, зате startup SENS був приблизно 34.5× дешевшим.

Це **архівна точка**, не показник поточного D1-D6 SENS.

## Standard binary-trees (#1549)

CLBG-compatible `binary-trees` має окремий N=10 correctness oracle:

```bash
python3 benchmarks/cross-language/binary_trees_reference.py --check-fixture
```

Timing для SENS додається лише після current exact-domain adapter; чужі upstream
timing numbers не імпортуються як наше evidence.
