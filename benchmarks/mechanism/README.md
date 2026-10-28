# Бенчмарки механізмів Rust і Zig та мови SENS

Механізми перевіряємо тією мовою, яка їх реалізує. `rust-byte-copy-bench.rs` та `zig-byte-copy-bench.zig` копіюють **ті самі байти** `lib/core4.lisp`, кожен має прогрів, 11 проб по 512 копій, p50/p90 та перевірку цілісності даних. Мовних законів у цих бенчмарках **немає**.

`rustc -O benchmarks/mechanism/rust-byte-copy-bench.rs -o /tmp/sens-rust-bench && /tmp/sens-rust-bench`

`zig test -O ReleaseFast -lc benchmarks/mechanism/zig-byte-copy-bench.zig`

**SENS:** наявні `benchmarks/lists.lisp`, `benchmarks/arithmetic.lisp`, `benchmarks/parser.lisp`, `benchmarks/recursion.lisp` запускаються окремо у CI. Їхні закони і мутанти належать `tests/semantic/`, виконання — виключно нативному SENS через Zig/T5M.

Числа Rust/Zig не є рейтингом мов: компілятор, цільова машина, виділення пам'яті та оптимізації відрізняються. Так само час повного SENS CLI, який містить bootstrap, не є чистим часом eval. На загальному GitHub runner не виставляємо автоматичних порогів прискорення, а зберігаємо p50/p90, розмір і SHA коміту. Інваріант — точне копіювання, а не задана швидкість.

Для подальшого розвитку: Criterion.rs (статистика та регресії), hyperfine (прогрів і зовнішні процеси), CL-Bench (окреме вимірювання виконання Lisp), офіційний Zig 0.16 (змінені API таймерів).

## Конкурс трьох сфер · Contract 11.8 / #6183

| Сфера | Власник | Що можна вимірювати | Чого не можна вирішувати |
| --- | --- | --- | --- |
| Механізм | **Rust** | копіювання, пакування, heap/arena, CPU/RAPL та апаратні лічильники | семантичні значення, закони D1–D10, правильність програми |
| Коридор | **Zig** | T5/T5M байти, ширину, інверсію, ABI, перенесення, час encode/decode | обчислюваний результат Lisp/SENS |
| Семантика й логіка | **SENS** | нативні програми, закони та мутанти у `tests/semantic/*.lisp`, конкурс `benchmarks/contest-uk` | делегування суду Python/Rust/Zig |

Жодне число з Rust або Zig не є мовним PASS. Парність фізичного носія
перевіряє Zig, а семантичний результат засвідчує виконання SENS.
Shell може запускати етапи, але не є мовним оракулом. Дослідні свідки
донорів не є ratified SENS-логікою.

### Джоулі: Rust-вимірювач механізму Linux RAPL

Новий самодостатній `rapl-energy-bench.rs` використовує лише `std`
і читає **package** `energy_uj` перед запуском одного зовнішнього
пакетного стенда й після нього. Він не аналізує stdout SENS, не
встановлює очікуваних значень та не привласнює логічний вердикт.

```sh
rustc -O benchmarks/mechanism/rapl-energy-bench.rs -o /tmp/sens-rapl
rustc --test benchmarks/mechanism/rapl-energy-bench.rs -o /tmp/sens-rapl-tests
/tmp/sens-rapl-tests
/tmp/sens-rapl -- ./target/release/sens --benchmark-physical benchmarks/lists.sens --core4-runtime
```

Для **справді пакетного** workload, який сам виконує рівно 100000
операцій за один процес, можна передати `--operations 100000`.
Число операцій є **заявленим, а не перевіреним** Rust — на підставі
одного запуску SENS CLI не можна стверджувати, що це 100000 форм.
Без `--operations` виводиться лише загальна енергія пакета.

```sh
/tmp/sens-rapl --operations 100000 -- ./prebatched-mechanism-benchmark
```

За відсутності `/sys/class/powercap/intel-rapl:*/energy_uj`,
проблемі доступу (зокрема WSL2) або нульовій роздільності лічильника
завершує з кодом 2, **не** видаючи нульових/оцінних джоулів.
Можна явно вказати `--counter /sys/class/powercap/intel-rapl:0/energy_uj`.
`SENS_RAPL_ROOT` — лише перевизначення каталогу пошуку, корисне для
механічного тесту читача; не замінює фізичний датчик.

Лічильник є **системним package**, не лічильником PID: результати
включають фон машини. Package та Cores перекриваються — не сумувати.
Два зчитування дозволяють врахувати **не більше одного** обертання
енергетичного лічильника; довгі навантаження необхідно розбивати на
пакети. Робити прогрів, парні A/B-повторення, чергувати порядок, вести
baseline простою та порівнювати тільки однакові машини/SHA/умови.
Фактичні джоулі тут **ще не опубліковано**.

### Наявні незмінені конкурсанти

```sh
# Rust: чиста механіка байтів
rustc -O benchmarks/mechanism/rust-byte-copy-bench.rs -o /tmp/sens-rust-bench
/tmp/sens-rust-bench

# Zig: фізичні T5M кодеки та corridor без мовної семантики
zig run -O ReleaseFast bench_t5m.zig

# SENS: нативне виконання та конкурс власних .sens/.lisp програм
SENS_CONTEST_REPEATS=5 bash benchmarks/contest-uk/run-native.sh
```

Результат вимірювання джоулів — **фізична метрика**, не рейтинг
коректності. Для офіційного релізу потрібен окремий нативний SENS
семантичний PASS та Zig T5M corridor PASS на поточному коміті.
