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

Ф4: поточний canonical D10 v5 містить 715 selected із зайнятими research-координатами, 0 ratified; ratified D1–D9 чинні окремо. Усі 715 research-координат захищені від повторного розміщення навіть без ratification. Попередні черги адрес — не авторитет канонічного коду. Конфлікт **не вигадувати** з однієї лише назви.

## Вихід (рівно 3 TSV для рішень)

- `knowledge/d10-filter/accepted-queue.tsv`: `ACCEPT_PENDING_BULK_APPROVAL`; координата `NONE` до bulk approval.
- `knowledge/d10-filter/rejected.tsv`: усі `EXCLUDE_*`, коди причин, source і перелік відсутніх доказів, `duplicate_of` для `EXCLUDE_DUP`.
- `knowledge/d10-filter/escalated.tsv`: лише `ESCALATE_OWNER` + посилання на конфлікт/координату/фактичний witness.

Колонки для виходів: `candidate_id\tsemantic_name\tstatus\treason\tdonor_provenance\twitness_result_ref\tsemantic_proof_ref\tduplicate_of\tconflict_target\tcoordinate\tsource_refs`.

Вихідні рядки відсортовано стабільно за `candidate_id`; кожен ID входу рівно в одному TSV. Окремий read-only summary/census із `source_ref` і SHA-256 файлів: scanned ref heads, unique candidate IDs, source rows, accepted/rejected/escalated counts, excluded by reason, incomplete source families. Заборонити невідомі/порожні статуси.

## Bulk-схвалення / розміщення

Власник переглядає тільки `accepted-queue.tsv`, дає один bulk-вердикт і може викреслити винятки; `escalated.tsv` проходить окремо. **Лише після явного схвалення** single-writer послідовно виділяє найменші вільні 10-бітні координати без повторів, проводить append-only зміну канонічного інвентарю, оновлює current-pointer/CI і запускає негативні перевірки. Жодне схвалення черги не означає автоматичну ратифікацію чи T5 runtime admission.

## Мінімальні негативні контролі CI

Відхиляти: непідтверджений donor URL; підроблений PASS; witness від іншого SHA; відсутній execution log; фальшивий semantic NO-MATCH; текстовий дубль замість семантичного сертифіката; несвідчену колізію; повторну координату; `python -O`, що обходить assert; незареєстрований Git ref чи загублений кандидат.

**Definition of done:** механічний runner відтворює три TSV із повного зведеного входу, має незалежні виконані witness/proofs, fail-closed негативні тести, 0 silent drops. Результати власникові для одного bulk-рішення. Нових гілок не створювати.
