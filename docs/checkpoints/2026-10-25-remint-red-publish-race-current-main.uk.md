# 25.10.2026 · remint-drifted-pairs · першопричина гонки публікації

## Фізичний факт RED
Workflow `remint-drifted-pairs`, run 40150438937 на SHA `0ed9490c0cec888a35e3d22168c893a973fd76de`, job 121040694906, завершився `failure`:

- `REMINT_PUBLISH_RACE after 6 verified attempts; newer main must retry natively; no force push`.
- Після кожної спроби публікації `main` уже містив незалежні нові коміти, які потребували нового native mint.
- Окремо зафіксовано `REMINT_CURRENT_MAIN_NATIVE_FAILED` для конкурсних SENS джерел та `REMINT_CURRENT_MAIN_CONTEST_RED`. Це справжні незакриті RED, а не «flake».
- У тому самому логові: `total_lisp_files=2175`, `potential_program_files=2065`, `complete_triplets=1373`, `potential_program_missing_sens=692`, `semantic_runtime_proven=False`, `release_ready=False`.

## Адресний ремонт без підміни семантики

У `.github/workflows/remint-drifted-pairs.yml` `concurrency.cancel-in-progress` змінено з `false` на `true` для існуючої гілкозалежної групи `remint-queued-v2-${{ github.ref }}`.

Тільки **новіший виклик** замінює попередній застарілий: фізично перевіряти і публікувати треба актуальний коміт гілки. Без `force push`, повторного запуску вже червоного SHA, нового workflow, зміни виконуваних SENS законів чи хостового «PASS». `workflow_call` та `workflow_dispatch` збережено.

Це усуває надлишкове паралельне виконання застарілих remint, але **не гарантує**, що один із майбутніх native mint успішно завершиться або що всі програми отримають фізичну трійку. Перервана перевірка не стає зеленою.

## Статус доказів

- `REMINT_RACE_PREVENTION=CONFIGURED_NOT_RUNTIME_VERIFIED`.
- `NATIVE_SENS_ALL=NOT_VERIFIED`.
- `CONTEST_NATIVE=RED_ON_OBSERVED_SHA`.
- `TRIPLET_COMPLETE=FALSE_ON_OBSERVED_SHA`.
- `RELEASE=l0.42.0:NO-GO`.

## Наступному агенту

1. Перевірити лише новий природний push-цикл, що старі remint мають статус `cancelled`, новий `running/queued`, і немає повторного `REMINT_PUBLISH_RACE`; `cancelled` не дорівнює `success`.
2. Зібрати конкретні `REMINT_CURRENT_MAIN_NATIVE_FAILED` на актуальному SHA, згрупувати спільну першопричину замість повторювати мітку для кожного конкурсанта.
3. Зберегти реальне SENS/Zig T5M `mint → inverse → paired → standalone`, обов'язкове `SHA256` квитування і відмови Type. Оновлювати пару тільки після фізичного доказу.
4. Продовжити D6 NTH/MIN/MAX/MAPLIST/LET, D10 CLIPS, D11 FREQUENCIES за актуальними логами. Частину SENS змін уже внесли паралельні агенти; не перезаписувати їх.
5. Релізний GO належить тільки власнику після точного кандидата, без непарних і непідтверджених виконуваних файлів.
