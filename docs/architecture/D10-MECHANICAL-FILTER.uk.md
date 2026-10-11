# D10: механічний фільтр кандидатів (нормативний intake-контракт)

Дата: 2026-10-11. Директива рою: [#5601](https://github.com/juv4uk/sens/issues/5601).
Область: **тільки** дослідницький відбір. Жодних автоматичних змін D1–D9, ратифікації D10, кодування `.sens`, T5 або runtime.

## Джерело і повнота

Вхід: `knowledge/d10-filter/all-candidates.tsv`, зібраний із **усіх існуючих Git refs** (включно зі старими дослідними гілками), закритих/незлитих PR, `knowledge/` і `research/domain-archive/`, `knowledge/d10-proposal-ledger.tsv` та результатів усіх агентів.

Кандидат — семантичний закон, а не одна англійська назва, Git-файл чи запис функції. Зберігати всі повторні provenance як посилання на появи, без silent drops. Якщо historical refs/closed PR недоступні або census неповний, звіт `coverage_complete=false`; **не заявляти «всі»**.

Контракт вхідного TSV:
`candidate_id\tsemantic_name\tsemantic_law\tdonor_provenance\twitness_artifact\twitness_result_ref\tsemantic_equivalence_certificate\tsemantic_distinctness_certificate\trequested_coordinate\tsource_refs`.

Джерельні SHA, proof artifacts та outputs pin до коміту; формат входу й кодек мають бути детермінованими. Не виконувати довільних shell-команд, отриманих із TSV.

## Фільтр: суворий порядок перевірок

| Крок | Механічна умова | Результат при провалі |
|---|---|---|
| Ф1 | Існує перевірений донор: SHA + репозиторій + шлях + рядок (вміст збігається) або верифіковане першоджерело URL/видання/сторінка | `EXCLUDE_NO_PROVENANCE` |
| Ф2 | Є **успішно виконаний** witness на цьому зафіксованому джерелі з перевіреним exit status, tool/runtime версією, run ID, commit SHA і артефактним hash | `EXCLUDE_NO_WITNESS` |
| Ф3a | Порівняння поведінки довело еквівалентність із уже наявним семантичним ID | `EXCLUDE_DUP`, неодмінно `duplicate_of` |
| Ф3b | Якщо дубль НЕ доведений, існує окремий перевірний сертифікат відмінності за поведінкою від наявних D1–D9/D10 (або незалежний oracle і контрприклади) | `EXCLUDE_UNPROVEN_DISTINCTNESS` до підтвердження, **не** `EXCLUDE_DUP` |
| Ф4 | Перевірити фактичну колізію координат або суперечність ratified семантиці; свідок конфлікту потрібний | `ESCALATE_OWNER` із кодом, target ID, доказом |
| Пройдено все | Provenance, witness і семантична незалежність перевірені; немає конфліктів | `ACCEPT_PENDING_BULK_APPROVAL` |

Ф1–Ф3 не потребують вердикту власника, але **неможливість автоматичного доказу** не замінювати вигадкою. Оцінка текстової схожості, однакових назв чи гешу source **НЕ є** сертифікатом семантичної тотожності. Старі `dedup_check=NO-MATCH` в ledger без відтвореного oracle не є доказом.

Ф4: чинний інвентар D10 **не визначати за номером v1/v5 або записаною в документі кількістю**. Перед кожним запуском читати `knowledge/d10-current-inventory.json` → `canonical_current.path`, перевіряти `canonical_current.git_blob` за фактичним Git blob SHA, а `selected/placed/ratified` — за відповідним інвентарем. Усі `placed` research-координати захищені від повторного розміщення навіть без ratification. Ратифіковані D1–D9 чинні окремо; historical archives та попередні адресні черги — не чинний авторитет. Конфлікт **не вигадувати** з однієї лише назви. Контрольна точка 11.10.2026: canonical v6, 719 selected/placed, 0 ratified; ці числа **не** є константами фільтра.

## Вихід (рівно 3 TSV для рішень)

- `knowledge/d10-filter/accepted-queue.tsv`: `ACCEPT_PENDING_BULK_APPROVAL`; координата `NONE` до bulk approval.
- `knowledge/d10-filter/rejected.tsv`: усі `EXCLUDE_*`, коди причин, source і перелік відсутніх доказів, `duplicate_of` для `EXCLUDE_DUP`.
- `knowledge/d10-filter/escalated.tsv`: лише `ESCALATE_OWNER` + посилання на конфлікт/координату/фактичний witness.

Колонки для виходів: `candidate_id\tsemantic_name\tstatus\treason\tdonor_provenance\twitness_result_ref\tsemantic_proof_ref\tduplicate_of\tconflict_target\tcoordinate\tsource_refs`.

Вихідні рядки відсортовано стабільно за `candidate_id`; кожен ID входу рівно в одному TSV. Окремий read-only summary/census із `source_ref` і SHA-256 файлів: scanned ref heads, unique candidate IDs, source rows, accepted/rejected/escalated counts, excluded by reason, incomplete source families. Заборонити невідомі/порожні статуси.

## Реальний запуск інструмента трьох черг

Виконуваний intake/partitioner у `scripts/d10_filter_intake.py` (поточні
негативні регресії: `tests/test_d10_filter_intake.py`). Він **не завантажує
Git refs, не виконує довільний код із TSV і не перевіряє GitHub Actions через
мережу**. Ф1–Ф4 застосовуються **тільки до доказових записів, попередньо
перевірених незалежним агентом/CI**. Самопроголошені `PASS` або
`NO-MATCH` не замінюють реплей, а поле `bulk_ready` у цьому
локальному звіті свідомо дорівнює `false`.

```sh
python3 scripts/d10_filter_intake.py \
  --input knowledge/d10-filter/all-candidates.tsv \
  --evidence knowledge/d10-filter/verified-evidence.json \
  --census knowledge/d10-filter/coverage-manifest.json \
  --evidence-root . \
  --out-dir knowledge/d10-filter
python3 -m unittest discover -s tests -p test_d10_filter_intake.py -v
```

`verified-evidence.json` має ключі за `candidate_id`. Для кожного запису:
`provenance` — `verified, artifact, sha256, source_ref, content_sha256`;
`witness` — `verified, artifact, sha256, source_ref, run_commit,
result=PASS, exit_code=0, positive_pass, negative_pass, oracle_pass,
run_url, tool_version`; `semantic` — такий самий pinned
`artifact/sha256/verified`, `classification=duplicate|distinct`,
`duplicate_of` і `bidirectional` для дубля або
`counterexample_checked/lower_domain_review/current_d10_review`
для нового закону; `conflict` — `verified, artifact, sha256,
status=none|conflict, target`. Артефакт перевіряється за локальним SHA-256,
шляхи поза `--evidence-root` заборонені. Для git-донора witness
`run_commit` мусить збігатися з pinned donor SHA.

`coverage-manifest.json` передає `coverage_complete`,
`source_manifest_verified`, `unreadable_sources`, `candidate_count`.
Їх слід отримати **незалежним сканером усіх сторінок історії**,
а не проставляти вручну. Якщо покриття не підтверджене, інструмент
повертає код 3 і зберігає три часткові черги з явним
`coverage_complete=false`. Неправильна схема чи втрачений/дубльований
ID — код 2 без декларації про успіх. Тільки повний незалежний
witness/source-verifier і full-census CI можуть згодом підтвердити
підготовлену чергу до bulk-ухвали власника.

## Bulk-схвалення / розміщення

Власник переглядає тільки `accepted-queue.tsv`, дає один bulk-вердикт і може викреслити винятки; `escalated.tsv` проходить окремо. **Лише після явного схвалення** single-writer послідовно виділяє найменші вільні 10-бітні координати без повторів, проводить append-only зміну канонічного інвентарю, оновлює current-pointer/CI і запускає негативні перевірки. Жодне схвалення черги не означає автоматичну ратифікацію чи T5 runtime admission.

## Мінімальні негативні контролі CI

Відхиляти: непідтверджений donor URL; підроблений PASS; witness від іншого SHA; відсутній execution log; фальшивий semantic NO-MATCH; текстовий дубль замість семантичного сертифіката; несвідчену колізію; повторну координату; `python -O`, що обходить assert; незареєстрований Git ref чи загублений кандидат.

**Definition of done:** механічний runner відтворює три TSV із повного зведеного входу, має незалежні виконані witness/proofs, fail-closed негативні тести, 0 silent drops. Результати власникові для одного bulk-рішення. Нових гілок не створювати.
