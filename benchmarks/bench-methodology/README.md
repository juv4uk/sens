# Бенчмарк-крило SENS: статистика без фальшивих перемог

## Межі конкурсу: Rust / Zig / SENS (28.10.2026)

| Острів | Власник | Бенчмарк | Заборонено |
|---|---|---|---|
| Механізм | Rust | Час, інструкції CPU, алокації, пам'ять, RAPL | Незалежний семантичний оракул |
| Коридор | Zig | Бітовий/тритовий round-trip, затримка, пропускна здатність | Визначення логіки SENS |
| Семантика й логіка | SENS | Нативні свідки, закони доменів, результати виконання | Підміна свідків Rust/Zig/Python |

Rust і Zig можуть запускати SENS та вимірювати його, але не задають очікуваних семантичних результатів. RAPL вимірює енергію CPU, а не правильність мови; package і cores не додаються як незалежні витрати.

Кожен вимір потребує SHA, обладнання, інструмента, повторів, сирих результатів та порівнюваного workload. Відсутність нативного свідка не є PASS.

Реліз s0.42.1: це документація наявних стендів, а не дозвіл додавати нові бенчмарки, тести, скрипти чи workflow до закриття P0.


**Поточний статус: методологічне дослідження.** Позитивні та негативні
свідки у `test_paired_effect.py` — **синтетичні**, не вимірювання
продуктивності SENS. Жодної семантичної ратифікації цей код не дає.

## Три незалежні осі

| Вісь | Інструмент | Що означає |
|---|---|---|
| Instruction counts | Чинний Cachegrind `benchmarks/physical-sens-runtime/irefs.py`; кандидат `iai-callgrind 0.16.1` | I refs на конкретному машинному шляху. Не час, не цикли |
| Wall time | Чинні парні T5 прогони; кандидат `criterion 0.8.2`, `hyperfine` для cold CLI | Затримка конкретного workload і мінливість середовища |
| Статистичний вердикт | `paired_effect.py` | Відношення середніх часів A/B та 95% двоступеневий парний bootstrap CI |

Версії `iai-callgrind` і `criterion` — **перевірені кандидати**,
але **не встановлені** цим PR у workspace. `iai-callgrind` потребує
Valgrind і runner, версія якого збігається з версією crate. Залучення
цих залежностей потребує окремої зміни `Cargo.lock` і Hosted CI після
stability window; `cargo --locked` не можна обходити.

## Як побудувати wall-time evidence

Приклад входу (показує **схему, не вимір**):

```json
{
  "schema": "sens-paired-wall/v1",
  "metric": "wall_ns",
  "sha": "ffffffffffffffffffffffffffffffffffffffff",
  "input_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "output_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "builds": [
    {
      "build_id": "independent-compilation-1",
      "binary_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "environment": {
        "cpu_model": "record real CPU",
        "rustc": "record actual compiler",
        "profile": "release",
        "cpu_governor": "record, or unknown",
        "turbo_state": "record, or unknown",
        "affinity": "record, or unknown"
      },
      "rounds": [
        {
          "order": "ABBA",
          "samples_ns": [100, 90, 91, 101],
          "outputs_sha256": [
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
          ]
        }
      ]
    }
  ]
}
```

`A` — baseline, `B` — candidate. Кожна четвірка є парною ABBA або
BAAB; порядок слід рандомізувати **до вимірювання**, журналювати seed
і не вибирати переможний порядок заднім числом. Файл у прикладі має
одну збірку та один раунд, тому результат **UNVERIFIED_MULTIBUILD**,
навіть якщо A повільніша.

```bash
python3 benchmarks/bench-methodology/paired_effect.py data.json --out verdict.json
python3 -m unittest discover -s benchmarks/bench-methodology -p 'test_paired_effect.py' -v
```

Мінімальні вимоги для статистичного вердикту: 3 **незалежні
компіляційні збірки** і 10 ABBA/BAAB четвірок на кожну. Це мінімальний
запобіжник, **не доказ достатньої потужності вибірки**. Кожен build
має бути реально незалежною компіляцією; інструмент не може сам
довести цього з рядка `build_id`.

Оцінка `baseline / candidate` більше 1 означає перевагу candidate
лише на цій фазі; менше 1 — регресію. 95% інтервал отримано
hierarchical paired bootstrap (спочатку блоки збірок, потім парні
повтори). Це **практичний двоступеневий bootstrap, натхненний
Kalibera–Jones, але НЕ повний їхній random-effects estimator**.
Не переносити інтервал на інші машини, збірки чи workloads.
`unknown` governor/turbo/affinity дає `UNVERIFIED_ENVIRONMENT`,
одна компіляція — `UNVERIFIED_MULTIBUILD`, розбіжність байтів
результату — `BLOCKED`.

До повної зеленої стабілізації SENS відображає результати як
`RESEARCH` або `UNVERIFIED`, а не як release speedup. Апаратні
GPU-виміри, Cold CLI і гарячі phase-measurements мають різні набори
джерел і ніколи не об'єднуються в один рейтинг.

## Політика PERF-BUDGET — один CI, два незалежні докази

**Правильність** підтверджує тільки ратифікований двійковий SENS-свідок.
**Вартість** підтверджує окреме відтворюване вимірювання реалізації.
Rust, Python, Cachegrind і CI не визначають семантику функції.

**PERF-BUDGET-EXCEEDED** — блокувальна відмова тільки для вже
каліброваного бюджетного рядка з реальними вимірюваннями та чинним
власником бюджету. Кожен такий рядок мусить містити:

- `case_id`, фазу `parse/eval/encode/transport`, точно зафіксовану
  фізичну SENS-програму й SHA-256 її байтів, кількість викликів та
  спосіб віднімання стартових/контрольних інструкцій;
- цільовий модуль, тип механізму, профіль збірки, SHA виконуваного
  файла, SHA коміту, CPU, версію Valgrind, Guix channels SHA;
- `baseline_ir`, `candidate_ir`, `max_ir_per_op`, частку
  інструкцій на операцію, першу порушену координату/фазу (якщо відома),
  команду відтворення й посилання на доказ;
- названу причину зміни бюджету та окремий коміт для її підвищення.

Не порівнювати абсолютні I refs, отримані на різних середовищах.
Cachegrind рахує **виконані інструкції**, а не час чи джоулі.
Для CLI з холодним стартом не видавати загальнопроцесні I refs за
вартість однієї гарячої операції. Потрібні калібрований контроль,
реальна кількість викликів і точний експериментальний протокол.

**Стан без перевіреної бази — `PERF-UNMEASURED`, не вигаданий PASS
або PERF-BUDGET-EXCEEDED.** Синтетичні приклади з
`cachegrind-join/example` заборонено використовувати як вимір.

Канарейки відомих костилів: текстово-десятковий міст у гарячому
доменному шляху, лінійний обхід замість уже допущеної бітмапи,
необґрунтована алокація на виклик. Для кожної — точний call-path
і мінімальний фізичний SENS-свідок. Сама наявність `format` або
`parse` у проєкті ще не доказ порушення: дозволені D24+
людські проєкції повинні відокремлюватися від машинної семантики.

**Тільки один автоматичний GitHub Actions `ci.yml`.** Він лишається
вузьким і не запускає повні бенчмарки чи нічний рій.
Дешеву калібровану канарейку можна додати як окремий *крок існуючого
job* після доказу її вимірювальної стабільності, не через новий
workflow. Поки такого доказу немає, повне Cachegrind вимірювання
та парні wall-time тести — **локальні/ручні**, без `schedule`,
`pull_request` чи нових автоматичних workflow.

Wall-time вердикт регресії вимагає зафіксованого effect size,
достатньої кількості незалежних збірок і довірчого інтервалу, що
виключає обраний поріг; без цього — `INCONCLUSIVE`, а не RED.
Існуючий `paired_effect.py` є статистичним інструментом, не
SENS-оракулом. Метрику сумарного боргу дозволено рахувати лише
по зіставних вимірюваннях; прогалини показувати як UNKNOWN.
