# ENERGY-03 · аудит пілоту Python / C / Rust

**Дата:** 2026-10-28. **Issue:** [#6288](https://github.com/juv4uk/sens/issues/6288). **Базовий зріз:** `main@b6a3254b625332613325fddfbfd027c8e71bbd2b`.
**Класифікація:** exploratory / фізичний експеримент, **не мовна семантика SENS**.
Цей аудит не затверджує рейтингу, доки не доведено еквівалентність роботи, відсутність DCE та належні незалежні повтори.

## Фактична робота, яку намагається виміряти пілот

- Функціональна одиниця: один запуск процесу з (N=8192) копіюваннями байтів одного й того самого `lib/core4.lisp` із `source` у `dest`. Компіляція виконується **поза** вимірюваним процесом; процесний запуск і читання файлу **включені**.
- Спільна відповідь: `PHYSICAL_COPY<TAB>bytes=B<TAB>copies=N<TAB>observed=S`, де `S=sum(source[i % B] for i in range(N))`. Після циклу всі три реалізації перевіряють `dest == source`.
- `copy.py`: `dest[:] = source` у кожній ітерації, потім читає одну вибрану комірку.
- `copy.c`: `memcpy(dest,source,size)` у кожній ітерації; volatile-читання **одного** байта dest; наприкінці один `memcmp`.
- `copy.rs`: `dest.copy_from_slice(black_box(&source))`; `black_box` на вибраному байті та `dest`, одна кінцева перевірка всіх байтів.
- Стартовий компіляторний контракт: `rustc --edition=2021 -O -C target-cpu=x86-64` та `cc -std=c11 -O2 -Wall -Wextra`. Точна версія компілятора пишеться у provenance. Різні стартові витрати інтерпретатора/бінарника **не відділено** від загального wall-time, і цей показник не є чистим `memcpy` throughput.

### Критичний незакритий доказ: оптимізатор / DCE

**Статус: NOT_VERIFIED.** Незалежна перевірка кінцевого буфера та суми одного вибраного байта **не доводить**, що оптимізований C/Rust виконує повне копіювання кожної з 8192 ітерацій. Результат може бути тим самим, якщо реалізація залишить тільки потрібні спостереження та фінальну копію. `black_box` і volatile-читання зменшують свободу оптимізації, але без дизасемблера і контрольованого експерименту не є фізичним доказом обсягу трафіку.

Для закриття необхідно на **тому самому SHA/CPU/compiler** зберегти оптимізовані бінарники й дизасемблер (`objdump -drwC` / `llvm-objdump -d`), перевірити шлях копіювання і його виклики в циклі; незалежно зіставити трафік на масштабах N=1024/4096/8192. Дані CPU perf/cache counters — допоміжні, **не** заміна доведення джерела та виходу. До закриття цього пункту метрики є `EXPLORATORY_ONLY`, а не міжмовний висновок. Негативний контроль: програма, яка просто друкує очікуваний рядок, могла б пройти тільки stdout-check; це доводить обмеженість parity, а не правильність такої програми.

## Межі та відмови

| Канал | Що дійсно спостерігається | Невідоме / коли відмовити |
| --- | --- | --- |
| Output parity | Точно один `PHYSICAL_COPY` з очікуваним B,N,S; сторонні рядки відхиляються | Не доводить фізичних копій усередині циклу; mismatch → `PHYSICAL_PARITY_MISMATCH` |
| Wall time без датчика | Python `perf_counter_ns` навколо `subprocess.run` + `/usr/bin/time` і child | Включає wrapper overhead, startup, файловий кеш; це не виключно CPU compute |
| Wall time з RAPL | `elapsed_ns` Rust-meter для `/usr/bin/time` + child; окремо записано зовнішній `host_wrapper_wall_ns` | **Інша межа часу**: два режими заборонено змішувати в одному твердженні |
| Peak RSS | GNU time `%M`, Linux max resident set процесу в KiB | Не сума пам'яті всієї системи, не heap-only, не пік групи довільних фон. процесів; ≤0 або некоректний рядок → BLOCKED |
| Energy | Опційний фізичний `energy_uj` RAPL CPU package | CPU package містить idle/background, **не** J окремого Python/C/Rust процесу і **не** wall energy. Без сенсора → `ENERGY_NOT_MEASURED`; недійсний, нульовий або неоднозначний лічильник → BLOCKED |
| Обчислення | Повторні запуски процесів у попарних AB/BA усередині `block` | Вісім блоків **не є доведеними незалежними лабораторними сесіями**: один CI-host і температурний дрейф. Звітний bootstrap ≠ exact Kalibera–Jones |

## Конкретні негативні контролі (виконувані unit-тести)

`python3 -m unittest discover -s benchmarks/language-energy-study -p 'test_study.py' -v`

- Невірний/подвоєний/сторонній фізичний stdout → BLOCKED.
- `RUST_RAPL_PACKAGE` із дубльованими полями, `NaN`, нулем, невідомим `scope` або статусом → BLOCKED.
- Відсутній чи нульовий RSS → BLOCKED.
- Child із від'ємним кодом завершення (signal) → BLOCKED.
- Немає `meter` → `energy_uj=None`, report status `ENERGY_NOT_MEASURED` (ніколи `0 J`).
- Збалансований порядок AB/BA не замінює незалежних сесій і не доводить фізичного трафіку.

## Збір даних для подальшого аудиту

Ручний обмежений пілот за **попередньо записаним** seed; 8 блоків × 4 пари для кожного з двох порівнянь:

```sh
python3 -m unittest discover -s benchmarks/language-energy-study -p 'test_study.py' -v
python3 benchmarks/language-energy-study/study.py \
  --blocks 8 --pairs 4 --copies 8192 --seed 20261028 --out /tmp/sens-energy03-exploratory
```

Зберегти `provenance.json`, `raw-samples.json`, `paired-report.json`, `summary.md`, вихідні коди, stdout/stderr і `git rev-parse HEAD`; не конвертувати ці файли в статтю без перевірки DCE, окремих сесій та апаратного сенсора. **Цей PR не заявляє фізичних raw samples**: якщо обмежений пілот не запускався, raw data = NOT_COLLECTED; якщо немає RAPL, energy = ENERGY_NOT_MEASURED.

## Наукові підстави (читані джерела)

- **Pereira et al., SLE 2017**, [DOI](https://doi.org/10.1145/3136014.3136031): зіставлення часу/пам'яті/енергії для 27 мов і 10 різних задач; тому цей byte-copy пілот **не** характеризує всю мову.
- **Pereira et al., SCP 2021**, [доступний рукопис](https://haslab.github.io/SAFER/scp21.pdf), [DOI](https://doi.org/10.1016/j.scico.2021.102609): порівнювані вхідні/вихідні контракти і різні ранги за різними метриками; потреба розрізняти algorithm/runtime/environment confounds.
- **Kalibera & Jones, ISMM 2013**, [рукопис](https://kar.kent.ac.uk/33611/45/p63-kaliber.pdf), [DOI](https://doi.org/10.1145/2464157.2464160): ієрархія збірка/виконання/ітерація й довірчі інтервали; незалежну реплікацію не підміняють сусідні цикли.
- **Wilkinson et al., FAIR 2016**, [DOI](https://doi.org/10.1038/sdata.2016.18): фіксація provenance, raw samples, точного SHA, доступність повторного аналізу.
- **Green Software Foundation SCI**, [специфікація](https://greensoftware.foundation/standards/sci/): functional unit `R` та системна межа; **ніякого SCI/CO₂e** без незалежних E/I/M.

**Висновок:** аудит виявив невизначеність збереження роботи компілятором; вимірювач посилено на вхідні докази, але пілот залишається дослідницьким, не confirmatory. Для claim-ready порівняння потрібна #6286, DCE-доказ, #6289 і #6290.
