# Фізичний D3: native SENS проти µCPU

Цей малий дослід доповнює Reality Matrix (#3680) та старі зовнішні контрольні
серії (#1413, #1668) **окремим зрізом актуального фізично виконуваного SENS**.
Він не створює нового семантичного benchmark і не підмінює перевірки тих задач.
Використані фікстури — поточні D3 self-test: позитивна й негативна, де інвертовано
рівно один D1-біт. Обидва рушії отримують однакові git-tracked T5-байти `.sens`.

## Що вимірюється

Перед таймінгом native CLI та Python µCPU мають видати однакові очікувані
результати `1` і `0` для обох фікстур. Runner відмовляється від файла, якщо той
не має суфікса `.sens`, лежить за межами репозиторію, не tracked у Git або порожній.

| Фаза | Native SENS | Python µCPU |
|---|---|---|
| Повна in-memory | T5 decode + D2 parse + нова `Session` + eval | T5 decode + µCPU compile + execute |
| Тепла | eval уже розібраних форм у повторно використаній `Session` | replay попередньо зібраної slot tape |

Ці реалізації мають різні внутрішні подання, тож це **пілот конкретних реалізацій
D1–D3**, а не рейтинг мов і не загальна заява про прискорення SENS. Таймінг не
включає запуск процесу та дисковий I/O; тепла фаза навмисно не включає повне
декодування/компіляцію.

## Чесніша межа: новий процес до відповіді

`process_bench.py` доповнює старий фазовий пілот парним виміром повного
користувацького виклику:

| Реалізація | Команда дочірнього процесу | Спільні включені етапи |
|---|---|---|
| Native SENS | `sens FILE.sens` | запуск процесу, читання того самого файла, T5 decode, виконання, stdout і завершення |
| Python µCPU | `python3 physical_cli.py FILE.sens` | запуск CPython, імпорт µCPU, читання того самого файла, T5 decode/µCPU compile, виконання, stdout і завершення |

Перед таймінгом обидві команди повинні повернути однакову очікувану відповідь.
Кожен вимір — новий дочірній процес; порядок сторін змінюється через пару.
Батьківський `perf_counter_ns` охоплює `subprocess.run` цілком, включно зі
створенням процесу та захопленням stdout/stderr. Build і correctness gate не
входять. Warmup робить кеш файлів ОС прогрітим; холодний дисковий кеш тут не
контролюється. Це зіставне **end-to-end порівняння двох реалізацій на цих
фізичних D3-файлах**, але не чистий вимір CPU-ядра й не рейтинг мов. Сирі
парні тривалості та порядок кожної пари зберігаються у JSON.

Зібрати один раз ті самі release-бінарники з pinned toolchain, як описано нижче,
потім виконати шість незалежних процесних реплік і звести raw JSON:

```sh
evidence=benchmarks/cross-language/reality-matrix/physical-sens/evidence/20261017-wsl2-i5-6400
for run in 1 2 3 4 5 6; do
  python3 benchmarks/cross-language/reality-matrix/physical-sens/process_bench.py \
    --sens-cli "$PWD/target/release/sens" \
    --reps 21 --warmup 3 \
    --out "$evidence/fresh-process-rep-$run.json"
done
python3 benchmarks/cross-language/reality-matrix/physical-sens/aggregate_process.py \
  "$evidence"/fresh-process-rep-{1,2,3,4,5,6}.json \
  --out "$evidence/fresh-process-summary.json"
```

Для малих 136-байтових fixture запуск runtime є помітною частиною результату —
це тут навмисно, бо саме повний виклик і вимірюється. Не віднімай startup
математично від end-to-end median: таке віднімання двох шумних величин
повернуло б той самий нечесний фазовий зріз.

## Попередні результати завантаження проти CPython

Попереднє порівняння є в [#1546](https://github.com/juv4uk/sens/issues/1546),
а машинні дані — в
[`benchmarks/cross-language/results/20261002-load-formats-i5-6400/`](../../results/20261002-load-formats-i5-6400/).
На i5-6400, Python 3.12.12 і Valgrind 3.27.0 геометричне співвідношення
Cachegrind інструкцій для load-фази було `.py / SENS = 434.55×` та
`.pyc / SENS = 224.58×`; startup вимірювався окремо, а потім віднімався
попарно з кожного повтору. Однак SENS-сторона цього виміру — **історичний
Function8 FASL**, не поточне фізичне Contract 11.9 виконання. Це інструкції,
не wall-clock, і ці коефіцієнти не можна переносити на нинішній native SENS.

Цей новий process-level pilot порівнює native SENS з **CPython-hosted µCPU**,
а не з еквівалентними Python `.py` / `.pyc` програмами з #1546. Нових current
SENS-vs-CPython source/bytecode load ratios тут не заявляємо: їх можна
публікувати лише після окремого correctness/parity replay за поточним
контрактом і межами #1546/#1668.

### Поточна SENS-програма проти Python-вихідного тексту

Додатковий окремий експеримент тепер є в
[source-copy-benchmark.uk.md](source-copy-benchmark.uk.md): D5 `LABEL COPY`
у справжньому тритовому T5 `.sens` представленні проти рекурсивного Python
source над відповідною pair-структурою. Доменні слова SENS залишаються
двійковими exact-width координатами; це не байткод. Перед часом вимагається
однаковий stdout `(1 0 ())`; запускається `.py` source без окремого
precompiled/`.pyc` режиму. Числа є лише вузьким локальним end-to-end
пілотом і не підтверджують мовний speedup.

## Відтворення

З кореня чистого checkout:

```sh
ZIG="$(guix package -I | awk '$1 == "zig" { print $4 "/bin/zig"; exit }')"
ZIG="$ZIG" CARGO_BUILD_JOBS=1 cargo build --locked --release -p sens-cli --bin sens
ZIG="$ZIG" CARGO_BUILD_JOBS=1 cargo build --locked --release -p sens --example physical_t5_phase_probe
python3 -m unittest discover -s tests -p 'test_microcpu_slots.py' -v
python3 -m unittest discover -s benchmarks/cross-language/reality-matrix/physical-sens -p 'test_run.py' -v
out=benchmarks/cross-language/reality-matrix/physical-sens/evidence/local-run
mkdir -p "$out"
for run in 1 2 3; do
  python3 benchmarks/cross-language/reality-matrix/physical-sens/run.py \
    --sens-cli "$PWD/target/release/sens" \
    --phase-probe "$PWD/target/release/examples/physical_t5_phase_probe" \
    --samples 11 --loops 100 --warmup 2 --out "$out/replicate-$run.json"
done
python3 benchmarks/cross-language/reality-matrix/physical-sens/aggregate.py \
  "$out"/replicate-{1,2,3}.json \
  --out benchmarks/cross-language/reality-matrix/physical-sens/comparison.json
python3 benchmarks/cross-language/reality-matrix/validate.py \
  benchmarks/cross-language/reality-matrix/physical-sens/comparison.json
```

Для benchmark-запису бажано виконати runner кілька разів як незалежні процеси.
JSON зберігає raw наносекунди кожного раунду, точний HEAD, версію контракту,
фізичний SHA-256, CPU/OS, версії Python/Rust та SHA обох native-бінарників.

## Пілот 2026-10-17

Базовий SENS: `main@5716836903165e24f73014b257be3d9e6a1c3518`, Contract 11.9.
Машина: WSL2 x86-64, Intel Core i5-6400, 4 CPU; rustc `1.99.0`, Zig pin `0.16.0`,
CPython `3.12.12`. Збірка native CLI пройшла з pinned Zig; без `ZIG` перша
спроба коректно відмовила з `Guard exact-source transport requires pinned Zig`.

Значення в таблиці — медіана 33 сирих раундів (3 незалежні процеси × 11
виміряних раундів); p95 також обчислено з усіх 33 вимірів. Одиниці — ns/operation.

| Фікстура (136 байтів, 223 слова) | Результат | Native full p50 / p95 | µCPU full p50 / p95 | Native warm p50 / p95 | µCPU warm p50 / p95 |
|---|---:|---:|---:|---:|---:|
| `d3-selftest.sens` · SHA-256 `3493225aebcf8703667a7b6d13aee1ec0d5f2a4d56b60a8fadcf593a2e1e8413` | `1` | 205413 / 264846 | 455477 / 649846 | 10686 / 19442 | 20496 / 42298 |
| `d3-selftest-negative.sens` · SHA-256 `a40485cc80c95517780652bdaaafd17a59c5304a8ac2cb9894ae68899e27be35` | `0` | 183234 / 362365 | 412039 / 523243 | 10408 / 11978 | 17224 / 49678 |

Кожен із трьох незалежних процесних повторів (обидві фікстури в кожному)
пройшов correctness gate `1/0` для обох рушіїв. Видно мінливість раундів і
викиди; тому навіть повторюваний напрямок цих двох мікровимірів — лише
спостереження даного WSL2-пілоту, **не** підтверджений мовний speedup чи
статистично узагальнений ефект. Для серйозної оцінки потрібні незалежні повтори
на контрольованому CPU/середовищі та заздалегідь визначені межі фаз.

### Парний запуск процесу до відповіді · 2026-10-17

Окремо від попередніх in-process фаз виконано 6 незалежних запусків runner-а,
по 21 парному запуску на фікстуру в кожному (126 пар/фікстуру). У кожній парі
нові процеси native SENS і CPython µCPU читають ті самі tracked фізичні байти;
порядок сторін чергується. Таймер включає запуск і завершення процесу,
runtime/module initialization, читання, декодування/µCPU compile, виконання та
stdout. Кеш файлів ОС прогрівався warmup-парами; холодний диск не вимірювався.

| Фізична фікстура | Пар | Native SENS p50 / p95, ns | Python µCPU p50 / p95, ns | Діапазон Python/native p50 між 6 репліками |
|---|---:|---:|---:|---:|
| d3-selftest.sens · SHA-256 3493225aebcf8703667a7b6d13aee1ec0d5f2a4d56b60a8fadcf593a2e1e8413 | 126 | 2,953,236 / 8,685,808 | 115,362,081 / 262,062,532 | 33.92×–82.60× |
| d3-selftest-negative.sens · SHA-256 a40485cc80c95517780652bdaaafd17a59c5304a8ac2cb9894ae68899e27be35 | 126 | 2,971,060 / 5,577,936 | 104,188,839 / 230,597,617 | 34.11×–40.95× |

Усі 12 пар «фікстура × репліка» пройшли parity `1`/`0`. Це лише описовий
process-to-result час двох конкретних реалізацій; великий розкид першої
позитивної репліки збережено в p95 і raw-файлах, а не відкинуто. Значення не
є мовним speedup, а p50 містить Python interpreter startup, якого немає у
попередніх in-process вимірах. Сирі пари та provenance збережено в
evidence/20261017-wsl2-i5-6400/fresh-process-rep-1.json …
fresh-process-rep-6.json.

Бінарники цього виміру: native `sens` SHA-256
`6db78d10a624c3b78c295384d94748d8da5920c539e52fa7a694a9006a1e5e5e`; фазовий
probe SHA-256 `e647698bd1b4ab884700d8c0ca8e5a7ea1f85048f931e9bf18947452b94976b9`.

Зведення, яке можна відтворити fail-closed агрегатором, доступне як
[`fresh-process-summary.json`](evidence/20261017-wsl2-i5-6400/fresh-process-summary.json).
Відношення pooled p50 становить 39.06× та 35.07× відповідно; це відношення
двох pooled медіан, не мовний speedup. Raw JSON шести незалежних проходів є в
[`evidence/20261017-wsl2-i5-6400/`](evidence/20261017-wsl2-i5-6400/).
Це додатковий вузький evidence до #3680; воно не закриває старі задачі #1413/#1668
і не стверджує еквівалентність із Python/Lua/Racket загалом.
