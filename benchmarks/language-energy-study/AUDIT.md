# ENERGY-03 · Аудит фізичного Python/C/Rust пілоту

**Дата:** 2026-10-28 · **issue:** [#6288](https://github.com/juv4uk/sens/issues/6288) · **тип:** exploratory / **НЕ пререгістрований confirmatory результат**.

**Межа досліду:** один запуск дочірнього процесу, який читає незмінний `lib/core4.lisp` як **неінтерпретовані байти** і намагається скопіювати його буфер N разів. Це **не** запуск мовних законів SENS і **не** порівняння інтерпретаторів SENS/Python/Rust/C над еквівалентними програмами. Для семантики SENS авторитетом лишаються виключно власні виконувані позитивні та негативні свідки.

## Інвентар джерел і фізичного контракту

| Файл | Фізична робота / межа | Не доведено |
|---|---|---|
| `copy.py` | `dest[:] = source` в циклі N, далі один вибраний байт на ітерацію і фінальна рівність `dest == source` | Рівні витрати з нативним `memcpy`; вплив інтерпретатора |
| `copy.rs` | `dest.copy_from_slice(black_box(&source))`; `black_box` для читання і буфера; кінцева byte parity | Дизасемблером не доведено точну кількість фізичних записів/байтів |
| `copy.c` | `memcpy` через **volatile function pointer** у циклі, щоби компілятор не склав однакові виклики в один; фінальна byte parity | Повна відповідність оптимізацій та накладних витрат викликів Rust/C |
| `study.py` | Незалежний expected record за байтами корпусу; `/usr/bin/time` дає `%M/%U/%S`; `perf_counter_ns` обрамляє запуск; optional RAPL meter | Проміжна копія N разів незалежно **не** верифікується checksum; немає доказу процесної енергії |

**Критично:** `observed` підсумовує **рівно один байт** `dest[i % len(source)]` за ітерацію; фінальний `memcmp` / порівняння є тільки після циклу. Однаковий `PHYSICAL_COPY` record доводить узгодженість публічного спостереження, але **не** доводить 8192 повних фізичних копій. Цим пілотом заборонено науково ранжувати мови або робити claim «C/Rust/Python витрачає X Дж на однакову задачу». Новий C volatile indirect call є консервативним захистом **лише** C-шляху, не міжмовною сертифікацією; потрібні дизасемблер, профіль копій або інструментована контрольна збірка для **кожного** варіанта. Не включати overhead такої інструментації в фінальний timing.

## Межі метрик і відмови

1. **Cold process:** кожен зразок запускає окремий процес. Rust/C бінарники збираються перед вимірюванням, Python запускає інтерпретатор під час вимірювання. Це **startup + копіювання + exit + wrapper overhead**, не warm steady-state; compiled-vs-interpreted startup є конфаундером. Час від `perf_counter_ns` охоплює також Python-parent і `/usr/bin/time`; з RAPL використано `elapsed_ns` із зовнішнього Rust meter — **різні межі таймера**. Не змішувати два режими.
2. **RSS:** `/usr/bin/time -f %M` звітує **піковий RSS вимірюваного процесу** в KiB, не суму всіх процесів, не DRAM енергію, не загальну фізичну пам'ять машини. `0`, відсутній або невірний рядок → **BLOCKED**. User/system CPU seconds — окремі спостереження `%U/%S`.
3. **Енергія:** тільки **один** доступний `intel-rapl:N` `package-*` із `energy_uj` / `max_energy_range_uj`; `RUST_RAPL_PACKAGE` мусить мати `status=MEASURED`, `scope=whole_package_not_process`, коректний `counter`, `wrapped_once`, додатні цілі `energy_uj/elapsed_ns`. Без сенсора `energy_uj: null` і `status: NOT_MEASURED` у звіті; не нуль і не TDP. Package energy включає idle і сторонні задачі. Valid RAPL не означає wall energy або SCI.
4. **Паритет:** будь-який зайвий stdout рядок, відсутній чи додатковий `PHYSICAL_COPY`, невідповідний bytes/copies/observed, timeout, ненульовий exit, некоректний RSS або malformed RAPL → **fail closed**. `test_study.py` має недорогі негативні контрприклади із simulated subprocess; це **тести інструментарію**, не вимірювання машини.
5. **Повтори:** `study.py` має 8..64 блоків і 4..30 збалансованих AB/BA пар кожен, seed; але групування проб під `block-id` є проектним, не доказом фізичної незалежності (немає окремих reboot/rebuild/session). `verdict.py` реалізує hierarchical paired bootstrap, **не** точний estimator Kalibera–Jones. `-O2` C, `-O` Rust, Python default і `target-cpu=x86-64` зафіксовані, але **не** вважаються однаковою оптимізацією. Немає тут доказу CPU governor, теплового шуму або енергодатчика на hosted CI.
6. **Ресурсний бюджет (впроваджено в цьому PR):** `validate_pilot_budget()` рахує **всі** 4×blocks×pairs A/B process launches + три запускові warmup, а не лише один child. Сумарно деклароване byte-copy має бути **≤8 GiB**, на процес **≤3 GiB**, корпус **≤64 MiB**; перевищення → `DECLARED_TOTAL_COPY_BUDGET_EXCEEDED`, перш ніж компіляція/вимір почнуться. Default `--copies=64` замість 8192; на корпусі 322314 B за 8 блоків × 4 пари це 131 запуск і 2702280576 байтів (~2.52 GiB) декларативного копіювання. Колишній default 8192 означав ~322 GiB копіювання й тепер **відхиляється**. Ці байти — верхньорівнева заявлена робота, не незалежно виміряний memory traffic; warmup і метрики в `study.py` лишаються exploratory. Для smoke використовувати unit-тести з fake subprocess; важких CI-прогонів не запускати.

## Відтворюваність і доказовість

- Наявні outputs при **реальному** `study.py` запуску: `provenance.json` (SHA, compiler versions, environment, flags частково), `raw-samples.json`, `paired-report.json`, `summary.md`. Немає записаного в цьому аудиті нового вимірювання або фізичних джоулів.
- Відсутні у pilot output для confirmatory: complete compile commands/disassembly hashes, independent hardware session ids, kernel and stable governor/thermal baseline, raw RAPL before/after and max range, calibration #6289, stdout/stderr кожного індивідуального прогона, machine-readable exclusions, registered sampling plan #6286, незалежний proof all N copies. **НЕ ПУБЛІКУВАТИ РЕЙТИНГ.**
- **Негативний сценарій, який протокол відхиляє:** C 8192 викликів виконані, Rust compiler довів лише 1 повну копію, однаковий checksum. Навіть із точним `PHYSICAL_COPY` записом це `COPY_WORK_NOT_CERTIFIED` і нерівність функціональних одиниць; без незалежної інструментації — не confirmatory.
- **Негативний сценарій енергії:** GitHub-hosted VM без одного фізичного package zone → `ENERGY_NOT_MEASURED`, навіть якщо час і RSS є.

## Чому саме ці методологічні рішення

- **Pereira et al., SLE 2017**, DOI [10.1145/3136014.3136031](https://doi.org/10.1145/3136014.3136031): 27 мов / 10 задач, окремі time, peak memory і фізичне вимірювання енергії. Звідси вимога не трактувати час як енергію, однакові задачі, фіксований environment; *не* переносити їхні ранги на наш byte-copy пілот.
- **Pereira et al., SCP 2021**, DOI [10.1016/j.scico.2021.102609](https://doi.org/10.1016/j.scico.2021.102609): програмні реалізації та стиль коду впливають на узагальнення рейтингів; звідси окрема графа для відмінностей Python slice / Rust copy_from_slice / C memcpy та заборона загального claim.
- **Kalibera & Jones, ISMM 2013**, DOI [10.1145/2464157.2464160](https://doi.org/10.1145/2464157.2464160): розділення ієрархічних рівнів випадковості, повторів, effect-size CI. Звідси явне застереження про невалідовану незалежність блоків та потребу оцінки шуму, а не фальшиве `8 blocks = 8 independent machines`.
- **Wilkinson et al., Scientific Data 2016**, DOI [10.1038/sdata.2016.18](https://doi.org/10.1038/sdata.2016.18): FAIR застосовується також до коду/алгоритму/процесу. Звідси потреба raw evidence + environment + provenance у відтворюваному архіві, а не лише таблиці ratio.
- **Green Software Foundation SCI**, [специфікація](https://greensoftware.foundation/standards/sci/): **SCI = (E×I+M)/R**, включає grid carbon intensity та embodied emissions. Пілот вимірює, в кращому разі, RAPL CPU package E, тому **SCI/CO₂e тут НЕ виміряно**.

**Статус:** аудит і негативні тести є **кодом/документом**, не фінальним польовим дослідом. Наступні залежності: #6286 frozen protocol, #6289 калібрування, перевірені instruction/copy counters, корпус #6287, точні raw samples зі стенда.
