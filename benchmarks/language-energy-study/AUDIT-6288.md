# ENERGY-03 · фізичний аудит Python / C / Rust-пілоту

Дата аудиту: **2026-10-28**. Задача [#6288](https://github.com/juv4uk/sens/issues/6288), батьківська [#6285](https://github.com/juv4uk/sens/issues/6285). Це **exploratory** перевірка фізичного копіювання, а не SENS-закон і не confirmatory рейтинг мов.

## Межі та статуси доказів

| Питання | Підтверджено | Що залишається |
| --- | --- | --- |
| Функціональна одиниця | Точні bytes із `lib/core4.lisp`, заявлені 8192 повторів, кінцева `dest == source`; незалежне `PHYSICAL_COPY` expected | Один checksum і фінальна рівність не доводять, що **кожна** із 8192 копій реально виконана |
| C / компілятор | Для **точного blob** `copy.c@b9ab5c7cca448fb84199d16022ec065edb2acca5`, GCC 14.2.0 x86-64 `-O2`: виклик `memcpy@plt` у циклі зі зворотним `jne`; `memcmp@plt` після циклу | Без окремого дизасемблювання не переносити висновок на Clang, LTO, інші CPU/flags |
| Python | Для точного `copy.py@8b4e0b0fe039209aa469dd06d392f60cab4d0d8d` фізичний `dest[:] = source` у циклі; 8192 повторів дають очікуваний результат | CPU/allocations інтерпретатора — складові цього режиму, не «вартість одного memcpy» |
| Rust | `copy.rs` містить `black_box(&source)`, `dest.copy_from_slice`, спостереження байта й `black_box(&dest)` | У поточному локальному середовищі `rustc` відсутній; disassembly/instruction count Rust — **NOT_VERIFIED**, не PASS |
| Час | Новий процес для кожної проби, компіляція винесена за вікно; `time_boundary` окремий для host і meter | Host wall включає накладні Python `subprocess` та GNU `time`; RAPL timer — `Rust Instant` навколо GNU `time`. Значення не є тотожними межами; warmed filesystem ≠ cold machine |
| Peak RSS | GNU `/usr/bin/time %M` (KiB) для дочірнього запуску, не `tracemalloc`, не гарантована сума всіх процесів | Не трактувати як live heap, allocations або системну пам'ять |
| Енергія | Дозволено лише валідний `RUST_RAPL_PACKAGE` зі scope `whole_package_not_process`, узгодженими `energy_uj/energy_j`, `elapsed_ns/elapsed_s`, коректним `wrapped_once`, absolute `energy_uj` counter | Package включає фон/idle; meter калібрувати за #6289, не вважати процесним лічильником |
| Без сенсора | `ENERGY_NOT_MEASURED`, без нуля, TDP чи Дж/копію | На цьому локальному стенді реальних фізичних джоулів не виміряно |
| Статистика | У пілоті збалансований AB/BA та детермінований seed | «8 blocks» — суміжні запуски, **не** 8 незалежних машин/сесій. ДІ тільки exploratory; строгість/залежності — окрема #6290 |

## Первинний локальний контроль (не фінальний dataset)

Тестова платформа: Linux 6.18.55 x86_64, AMD EPYC 9V74, Debian GCC 14.2.0, Python 3.13.5; **без Rust і без перевіреного фізичного RAPL**. Ці короткі контрольні запуски не є міжмовним енергетичним бенчмарком і не мають значущих часових повторів.

- Файли `copy.c` і `copy.py` відтворені byte-exact: `git hash-object` збігся з наведеними вище GitHub blob SHA.
- Незалежний контрольний буфер: 128 байтів від 1 до 128; SHA-256 `bafa52e3c9b5c87242b6bb2ecb23976625fe469ac15670d22fb09b5be1111115`.
- Для `N=8192` очікуваний checksum `528384`; C і Python обидва надрукували `PHYSICAL_COPY bytes=128 copies=8192 observed=528384` (поля в реальному stdout розділені табуляціями).
- Обидва варіанти відхилили `COPIES=0` та `COPIES=8193bad` із кодом 2.
- `objdump -dr copy-c`: `call memcpy@plt` за адресою `0x1240`, `jne 0x1237` із кінця циклу, `call memcmp@plt` за `0x1268`. **Це спостереження конкретного GCC-бінарника, а не формальна гарантія для всіх компіляторів.**
- Локальна ізольована перевірка того самого `parse_rapl_record` (без sensor/mock false positives): один дійсний запис прийнято, **11 різних недійсних** відхилено; 2 unit-методи / 11 негативних підвипадків. Повний GitHub `test_study.py` та Rust disassembly у цьому локальному середовищі ще **НЕ виконані**.

## Відтворення на цільовій машині

```sh
python3 -m unittest discover -s benchmarks/language-energy-study -p test_study.py -v

# Без сенсора: тільки процесний час/RSS, не числові джоулі.
python3 benchmarks/language-energy-study/study.py --blocks 8 --pairs 4 \
  --copies 8192 --seed 20261028 --out /tmp/energy-6288

# Контроль компіляції/дизасемблювання для кожного toolchain:
cc -std=c11 -O2 -Wall -Wextra benchmarks/language-energy-study/copy.c -o /tmp/copy-c
objdump -dr /tmp/copy-c | grep -E 'memcpy|memcmp'
rustc --edition=2021 -O -C target-cpu=x86-64 benchmarks/language-energy-study/copy.rs -o /tmp/copy-rust
objdump -dr /tmp/copy-rust
```

**Застереження:** `grep memcpy` саме по собі не є доказом 8192 копій — потрібно підтвердити, що виклик у циклі, а в інших compiler configurations може бути inlining/vectorization. Не запускати ці команди на дорогих runners без дозволу.

Для спроби відтворення зберігати `provenance.json`, `raw-samples.json`, `paired-report.json`, `summary.md` з точним Git SHA; якщо метр відсутній — у звіті тільки `ENERGY_NOT_MEASURED`. Не перезаписувати негативи. Окремі первинні дані не замінювати підготовленою таблицею.

## Методологічна підстава (прочитані джерела)

1. Pereira et al. (SLE 2017), [doi:10.1145/3136014.3136031](https://doi.org/10.1145/3136014.3136031): порівняння енергії/часу/пам'яті для різних задач вимагає визначеного workload; **один byte-copy pilot не представляє мову в цілому**.
2. Pereira et al. (SCP 2021), [doi:10.1016/j.scico.2021.102609](https://doi.org/10.1016/j.scico.2021.102609), доступний [повний препринт](https://haslab.github.io/SAFER/scp21.pdf), секція вимірювань: компіляція/версії, output parity, запуск wrapper/RAPL, peak memory та обмеження overlay. Тому compiler flags, stdout parity і різні вимірювальні межі фіксуються явно.
3. Kalibera & Jones (ISMM 2013), [doi:10.1145/2464157.2464160](https://doi.org/10.1145/2464157.2464160), [авторська копія](https://kar.kent.ac.uk/33611/45/p63-kaliber.pdf), розділи 3–4: рівні варіації (компіляція, старт, ітерація) не можна змішувати; 8 суміжних блоків не доводять незалежності.
4. Wilkinson et al. (2016), [doi:10.1038/sdata.2016.18](https://doi.org/10.1038/sdata.2016.18), [доступний текст](https://pmc.ncbi.nlm.nih.gov/articles/PMC4792175/): FAIR вимагає машинно доступної provenance та сирих даних, а не лише висновків.
5. Green Software Foundation, [SCI](https://greensoftware.foundation/standards/sci/): функціональна одиниця є знаменником SCI, але для CO₂e потрібні ще `I` та `M`; тут їх немає, **SCI НЕ ОБЧИСЛЮВАЛИ**.

## Рішення аудиту

**Пілот придатний для обмежених фізичних exploratory smoke-checks**, але **NOT_READY_FOR_LANGUAGE_ENERGY_RANKING** без незалежної апаратної енергії, верифікації Rust/DCE на фактичній платформі, повних процесних boundaries, надійних сесій/калібрування та затвердженого #6286. Не видавати «Python/C/Rust швидший/зеленіший» за науковий результат із цього smoke.
