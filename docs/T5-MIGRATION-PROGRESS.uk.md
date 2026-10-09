# Зведений прогрес міграції `.lisp → .sens` без самообману

**2026-10-08 · issue #4449 · механічний облік, НЕ семантичний оракул.**

Наша мова — двійкова; `path/name.lisp` стає `path/name.sens` у фізичному T5: 5 тритів на байт, транспортна `2` **лише між** точними доменними словами; EOF — довжина файла без `22`; 0–4 фінальних pad-трити. Вміст `.sens` не є текстом із нулів та одиниць.

У репозиторії **вже були** два незалежні чесні аудити:
- `scripts/audit_t5_file_pairs.py`: перевіряє **кожний відстежуваний файл .sens** і однойменний `.lisp`, фізичний T5, хеші й точні доменні ширини.
- `scripts/migration-readiness-census.py`: у **трьох окремих режимах** (AUTO, historical, current) інвентаризує **оригінальні `.lisp` без .sens** і розрізняє історичні причини BLOCK та лише механічну готовність.

Новий `scripts/report_t5_migration_progress.py` **не пише власного парсера, не конвертує і не створює .sens**. Він бере два результати та незалежний `git ls-files '*.lisp'`, перевіряє:
- усі відстежувані `.lisp` присутні **рівно один раз** або у файлі з парою, або в черзі;
- усі фізичні файли отримали **однойменний** `.lisp` (не файл без розширення);
- жодна пара не потрапила водночас у чергу «без пари»;
- жодне поле `would-write` не стало `semantic_admitted=true`;
- старі, дубльовані, незафіксовані або втрачені шляхи — **BLOCKED_DISCREPANCY**, не успішний реліз;
- зберігаються SHA джерела, SHA фізичних байтів, SHA typed-width identity і перша причина блокування, якщо є.

Файл дає класи `PHYSICAL_T5_PAIR_PENDING_INDEPENDENT_ORACLE`, `PHYSICAL_T5_PAIR_BLOCKED`, `UNPAIRED_SOURCE_BLOCKED`, `MECHANICAL_CANDIDATE_NEEDS_ORACLE`, `NONPROGRAM_ARCHIVED_NO_EXECUTABLE_T5`. Це **класи обліку, не статуси дозволу на виконання**.

## Відтворення

```sh
python3 scripts/audit_t5_file_pairs.py . --output /tmp/t5-pairs.json
python3 scripts/migration-readiness-census.py --out /tmp/t5-readiness.json
python3 scripts/report_t5_migration_progress.py \
  --root . --pairs /tmp/t5-pairs.json --readiness /tmp/t5-readiness.json \
  --out /tmp/t5-progress.json
python3 -m unittest discover -s tests -p 'test_report_t5_migration_progress.py' -v
```

Підключений CI `report-t5-migration-progress` публікує JSON-артефакти й короткий підсумок. Відсутність жодної пари, зниклий файл у ledger, зайва публікація чи вигаданий статус — не можуть називатися `100% migrated`.

**Релізний доказ окремо:** обов’язкові оригінальний pinned source SHA, canonical Rust D2-парсер, незалежний source/current semantic observer oracle і тільки після цього прийняття виконуваної програми. Цей облік **не послаблює** механізми `guard_original_sens_admission.py`, `admit-t5-migration.py` чи ratified D1–D9.

## Поділ агентів

Скрипт працює після злиття без зміни чужих корпусів. Кожний агент бере лише свої `.lisp` шляхи (див. #4449), а наступний CI-звіт показує, чи файл став перевіреною фізичною парою, чи залишається в черзі, і що саме блокує його перехід. **Кількість фізичних пар не дорівнює кількості семантично перевірених програм.**
