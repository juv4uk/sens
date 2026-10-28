# ENERGY-06 · відтворюваний пакет доказів (підготовчий шар)

Пов'язано з [#6291](https://github.com/juv4uk/sens/issues/6291) та [#6285](https://github.com/juv4uk/sens/issues/6285). Це **не окремий реєстр дослідів**, не публікація і не самостійна незалежна реплікація #131. Шар лише перевіряє цілісність уже зібраних фізичних доказів пілоту `benchmarks/language-energy-study/study.py` (Python/C/Rust). Повну ENERGY-06 можна завершити **лише після #6286–#6290 і стороннього відтворення**.

**Обмеження сумісності (перевірено 28.10.2026):** поточний `main`-пілот `benchmarks/language-energy-study/study.py` ще **не** генерує сумісний пакет: у сирих пробах відсутнє `time_boundary`, а статус звіту без датчика — `NOT_MEASURED`, не `ENERGY_NOT_MEASURED`. Валідатор **навмисно повертає `ARTIFACT_INTEGRITY_BLOCKED`**, а не підставляє незафіксовані метадані чи вигадані джоулі. Це статус **`SCHEMA_COMPATIBILITY_BLOCKED`**, не доказ неправильної енергії. PR #6295/#6296 у #6288 мають узгодити один контракт із цим інструментом перед реальним end-to-end тестом. `counter` і `wrapped_once` допускаються лише за наявності апаратного сенсора, з `scope=whole_package_not_process`. До того часу можна зливати **лише ізольовану реалізацію валідатора** як research-only код, але не стверджувати, що пакет пілоту пройшов FAIR чи що дослід незалежно відтворений.

## Чітка межа

- Підтверджений результат валідатора: структура, точний Git SHA і побайтові SHA-256 чотирьох файлів; фізична узгодженість raw-метрик зі статусом сенсора; **повні парні запуски** Rust–C та Rust–Python із записаною чергою AB/BA, неперервними індексами та зіставленням кількості пар зі звітом.
- **Не підтверджує:** виконання кожного `memcpy`, незалежність повторів, справжність сенсора, зовнішню реплікацію, еквівалентність мов SENS, правильність p-value чи наукову значущість.
- Стан `ENERGY_NOT_MEASURED` означає *відсутність фізичних джоулів*, а не `0`. `MEASURED` приймає тільки позитивні `energy_uj` з `scope=whole_package_not_process`, реальною назвою energy counter і записом межі метра. Пакет CPU включає фон і **не** дорівнює енергії процесу.
- Значення `independent_reproduction` у цьому пакеті **завжди** `NOT_REPRODUCED`: лише стороння реплікація в #131/#6291 може породити окремий reviewed proof. Зміна цього поля вручну блокується.

## Структура одного пакета

Скопіюйте з фактичного `--out` чинного пілоту (без синтетичних даних):

```text
/tmp/energy-study-evidence/
  provenance.json          # exact SHA, toolchains, CPU, scope
  raw-samples.json         # кожен запуск і негативи збережено
  paired-report.json       # статистичні висновки / inconclusive
  summary.md               # людський огляд, не заміна raw
  manifest.json            # власний SHA та SHA-256 чотирьох файлів
```

Створіть `manifest.json` тільки **після** фактичного запуску: цей приклад формує метадані із наявних файлів; він **не створює проб**.

```sh
cd /tmp/energy-study-evidence
python3 - <<'PY'
import hashlib, json
from pathlib import Path
base = Path(".")
source = json.loads((base/"provenance.json").read_text())
names = {
    "raw_samples": "raw-samples.json",
    "provenance": "provenance.json",
    "paired_report": "paired-report.json",
    "summary": "summary.md",
}
status = ("MEASURED" if source.get("energy_sensor") == "RAPL_AVAILABLE"
          else "ENERGY_NOT_MEASURED")
manifest = {
    "schema": "sens-energy-artifact/pilot-v1",
    "source_sha": source["git_sha"],
    "energy_status": status,
    "independent_reproduction": "NOT_REPRODUCED",
    "files": {
        key: {"path": name, "sha256": hashlib.sha256((base/name).read_bytes()).hexdigest()}
        for key, name in names.items()
    },
}
(base/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
PY

# У checkout тієї самої гілки/коміту:
cd /absolute/path/to/juv4uk-sens
python3 artifact/energy-study/validate_manifest.py /tmp/energy-study-evidence/manifest.json
```

Валідатор припиняє роботу з ненульовим кодом при зміні SHA, невідповідності provenance, неіснуючому/пов'язаному симлінком/занадто великому файлі, пустому raw, неприйнятному RSS, фальшивих джоулях або неправдивому `REPRODUCED`. Успіх означає тільки `ARTIFACT_INTEGRITY=PASS`, **не** `SCIENCE_RESULT=PASS`.

**Цілісність парного досліду.** `raw-samples.json` має містити два сусідні записи однієї пари у заявленій черзі: `AB` = Rust, потім кандидат; `BA` = кандидат, потім Rust. Для кожного блока потрібні **обидва** кандидати `python` та `c`, однакова кількість щонайменше чотирьох пар, послідовні індекси `1..N` та чергування AB/BA. `paired-report.json` має містити `wall_time_ns.pairs` та `peak_rss_kib.pairs`, що точно збігаються з кількістю сирих пар кожного кандидата. Пропущений запуск, підмінений порядок або розбіжність із парним звітом → **BLOCKED**, не PASS. **Це контроль структури спостережень, а не доказ статистичної незалежності блоків:** її перевіряє #6290 за Kalibera–Jones.

## Самоперевірка (без дорогих runners)

```sh
cd artifact/energy-study
python3 -m unittest -v test_validate_manifest.py
```

На 2026-10-28, локальна Python 3.13.5: **17/17 синтетичних тестів PASS**; `git hash-object` локальних файлів тесту та валідатора збігається з GitHub blob SHA `b49b1ba54f70b28501cad7eda3ceb4bac2f51c6a` і `e428bb60f53c15e00eeacc361463de6540ac31fd`. Це лише доказ правильної поведінки валідатора на синтетичних fixture. Жодних реальних енергетичних даних, сторонньої машини/DOI або авторитетного висновку тут немає.

## Джерела й конкретні рішення

- [Wilkinson et al., FAIR (2016)](https://doi.org/10.1038/sdata.2016.18), [повний відкритий текст](https://pmc.ncbi.nlm.nih.gov/articles/PMC4792175/): знаходжуваність, доступність, сумісність і повторне використання стосуються **і даних, і кодів/воркфлоу** → зв'язуємо raw/provenance/summary/SHA без прихованих артефактів.
- [Pereira et al., SLE 2017](https://doi.org/10.1145/3136014.3136031): енергія, час і пам'ять — **окремі** метрики різних навантажень; один фізичний byte-copy не характеризує всі мови.
- [Pereira et al., SCP 2021](https://doi.org/10.1016/j.scico.2021.102609), [авторський препринт](https://haslab.github.io/SAFER/scp21.pdf), методологія: зберігаємо output validation, build/runner versions та raw вимірювання; не вигадуємо атрибуцію CPU package окремому процесу.
- [Kalibera & Jones, ISMM 2013](https://doi.org/10.1145/2464157.2464160), [авторська копія](https://kar.kent.ac.uk/33611/45/p63-kaliber.pdf): компіляція, процес і ітерація є різними рівнями варіації → маніфест не робить CI-повтори незалежними сесіями.
- [Green Software Foundation SCI](https://greensoftware.foundation/standards/sci/): `E × I + M` на функціональну одиницю; тут `I` та `M` не вимірювалися, тому **не** рахуємо CO₂e чи SCI.

## Залежності, які ще блокують фінальну #6291

Prospective заморожений протокол #6286; 8–10 порівнюваних задач #6287; аудит/фізичні RAW #6288–#6289; статистична перевірка #6290; незалежна чиста машина/інший виконавець #131; рішення власника щодо архівації, ліцензії, DOI. До їх наявності — `NOT_REPRODUCED`, не фальшивий «artifact certified».
