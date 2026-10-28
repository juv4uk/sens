# Як відтворити це дослідження

Усе нижче виконується з кореня репозиторію. Жоден крок не потребує правок
коду й не містить вписаних руками чисел.

## 1. Перевірити, що мови роблять ОДНАКОВУ роботу

```bash
python3 benchmarks/language-energy-study/parity_check.py --selftest
python3 benchmarks/language-energy-study/parity_check.py \
  --task T09-bit-operations --run "node benchmarks/language-energy-study/corpus/javascript/t09_bitcount.mjs"
```

Очікувано: `ПАРИТЕТ-МАШИНА: УСІ ПЕРЕВІРКИ ПРОЙДЕНО` і `PARITY_OK`.

**Не міряйте нічого, поки не отримали `PARITY_OK`.** Інакше вимірюєте різну
роботу, і числа нічого не означають.

Свою реалізацію (SENS, Rust, C, Go) підключайте тим самим способом:

```bash
python3 benchmarks/language-energy-study/parity_check.py \
  --task T09-bit-operations --run "<шлях до вашого бінарника>"
```

Команда отримує `TASK_ID`, `TASK_N`, `TASK_SEED`… у середовищі й мусить
надрукувати **рівно один рядок** — вихід.

## 2. Зібрати парні дані

```bash
# одна задача, швидка перевірка ланцюга
python3 benchmarks/language-energy-study/run_study.py \
  --tasks T01-symbolic-recursion --smoke --out raw-smoke.json

# повний прогін однієї задачі
python3 benchmarks/language-energy-study/run_study.py \
  --tasks T01-symbolic-recursion --measure \
  --processes 8 --per-process 4 --out raw-T01.json
```

Що гарантує раннер:
- кожен запуск — **окремий процес** (одиниця ресемплінгу);
- порядок **AB/BA чергується**, щоб дрейф частоти не приписався одній мові;
- `peak_rss_kib` береться через `os.wait4` — **на кожен процес**, а не
  накопичувальний максимум;
- енергія **не вигадується**: без RAPL лишається `ENERGY_NOT_MEASURED`.

## 3. Відтворити таблицю з сирих даних

```bash
python3 benchmarks/language-energy-study/report_table.py --markdown
```

Скрипт читає всі `raw/*.json` і рахує таблицю через `verdict.py`. Seed
фіксований (5227), тому повторний прогін дає **ті самі** числа. Якщо метрики
немає в даних — рядок пропускається, а не заповнюється нулем.

## 4. Перевірити саму статистику

```bash
python3 benchmarks/measurement-triad/test_verdict_simulation.py
```

25 перевірок з **відомою істиною** (генератор): рівень хибних висновків,
відомий ефект, heavy tails, викиди, автокореляція, AB/BA, Holm, відсутність
data-dependent stopping.

## Що потрібно для енергії (і чого немає тут)

Енергія вимагає **RAPL** (`/sys/class/powercap/intel-rapl:*/energy_uj`).
У середовищі, де готувався цей документ, датчика не було, тому **всі**
результати містять `ENERGY_NOT_MEASURED`.

Щоб виміряти енергію:

1. переконайтесь, що RAPL доступний і читається без root;
2. додайте `energy_uj` до пари як `baseline_energy_uj` / `candidate_energy_uj`;
3. запустіть `report_table.py` — метрика підхопиться автоматично.

**RAPL CPU package ≠ енергія процесу.** Пакет вимірює всю підсистему; атрибуція
конкретному процесу потребує окремої домовленості й мусить бути названа в
публікації.

## Чого ці дані НЕ доводять

- нічого про **SENS**: у середовищі не було компілятора, тому SENS у вимірах
  не брав участі;
- нічого про **енергію**: `ENERGY_NOT_MEASURED`;
- нічого **міжмашинного**: усе знято на одній машині, незалежної реплікації
  немає (`#6291` = `NOT_REPRODUCED`);
- **переможця немає**: при перекритті 95% ДІ висновок не робиться.

Деталі обмежень — у `limitations-and-negative-results.md`.
