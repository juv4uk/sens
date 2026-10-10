# Бенчмарк-крило SENS: статистика без фальшивих перемог

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
