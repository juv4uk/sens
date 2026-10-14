# Zig — стерильний коридор між Rust і SENS · 14.10.2026

**Статус:** дослідна реалізація в `zig-codecs-t5-f3c-bench-20261014`; не новий закон SENS, не самостійне схвалення релізу. Основна робота: [#5779](https://github.com/juv4uk/sens/issues/5779); бітовий закон: [#4367](https://github.com/juv4uk/sens/issues/4367); публікація/ера: [#5778](https://github.com/juv4uk/sens/issues/5778).

## Конституційна межа

> Zig знає лише фізичну драбину точних доменних бітностей. Rust і зовнішні перекладачі можуть знати історію; Zig не може отримати історичне ім’я як тип, і не може встановити семантику програми.

Технічно це **три окремі докази**, а не один:

1. **Стерильність коду:** `research/zig-codecs/t5/sterile/domain_word.zig` визначає `DomainWord(comptime width)`, з незалежними типами для різних ширин. `scripts/check-zig-cleanroom.py` сканує **кожний tracked `.zig`**, включно з коментарями, відхиляє старі імена/десяткових посередників, імпорти поза Zig-коридором, а також складені `@import` / `@embedFile` вирази. Сканер працює в **єдиному центральному CI на кожний push/PR**, а не лише на Zig-дослідній гілці. Компільований негативний тест різних ширин зберігається окремо.
2. **Стерильність фізики:** `research/zig-codecs/t5/sterile/physical_cycle.zig` виконує `decode → SHA-256 → encode → exact bytes` і повертає `semantic_status=NOT_VERIFIED`. Навіть `0x35` — фізично коректний одиничний CLOSE — повертається побайтово, але *не стає* допустимою програмою SENS. `transport.zig` використовує цей цикл для нових фізичних файлів; Zig не знає, яким історичним шляхом вони з'явилися.
3. **Зовнішня допускова квитанція:** `scripts/verify_zig_publication_candidate.py` — **CI_GLUE_NO_SEMANTICS, поза Zig**. Для *кандидата*, але не для релізу, вимагає явний `source_era=current|translated`, точні SHA-256 джерела, фізичного `.sens`, Zig виконуваного файла та нативного `sens-trit`; для перекладеного джерела — окремий закріплений квитанцією файл із походженням. Фактично виконує Zig `t5-roundtrip` із перевіркою **байт-у-байт**, **SENS `encode` на незмінному знімку переданого канонічного джерела → незалежну точну рівність з кандидатом**, і `sens-trit eval` із порівнянням stdout SHA до незалежно заданого очікування. Два правильних, але не пов'язаних між собою SHA відтепер недостатні.

```text
історія і мігратор (ПОЗА Zig) ─→ source sha + explicit era + translation receipt
                                             │
                          owner-approved SENS law / expected native witness
                                             │
host Rust I/O ── bytes/bit widths ── Zig чиста кімната ──> SENS native reader/eval
                                       │                    │
                            byte replay + SHA         actual stdout SHA
                                       └──── candidate preflight ────┘
```

## Маніфест кандидата

Зберігається ПОЗА Zig. Поля:
```json
{
  "schema": "sens-zig-publication-candidate/v1",
  "source_era": "current",
  "source_sha256": "<64 lowercase hex>",
  "physical_sha256": "<64 lowercase hex>",
  "zig_executor_sha256": "<64 lowercase hex>",
  "sens_executor_sha256": "<64 lowercase hex>",
  "expected_native_stdout_sha256": "<64 lowercase hex>"
}
```

Для `source_era=translated` обов'язкове поле `translation_receipt: {"path": "<absolute path>", "sha256": "<64 lowercase hex>"}`. Поле `--source` в обох режимах — **канонічна двійкова `.lisp`-проєкція після допуску**, а не довільний старий текст. Історичний вхід і журнал перетворення живуть тільки у зовнішній `translation_receipt`; Zig нічого не знає про ери. Відсутній результат `sens-trit encode`, невдалій код чи несумісний фізичний файл → негайний RED до `eval`. `auto`, невизначена епоха, невірний SHA, відсутній доказ, недійсний T5, вихід Rust fallback, модифікований файл, негативний/хибний SENS execution — `RED`. Результат успіху називається **`CANDIDATE_VERIFIED_NOT_PUBLISHED`**, не `SEMANTIC_PASS`.

### Команда окремої перевірки

```sh
python3 scripts/verify_zig_publication_candidate.py \
  --candidate /absolute/path/program.sens \
  --source /absolute/path/source.lisp \
  --receipt /absolute/path/owner-controlled-provenance.json \
  --zig /absolute/path/sens-zig-transport \
  --sens /absolute/path/sens-trit
```

Засвідчено тестами `tests/test_zig_publication_candidate.py`, негативними варіантами та єдиним `.github/workflows/ci.yml`. У Zig-дослідному CI додатково є реальний SENS+Zig smoke-кандидат із заздалегідь відомим результатом `QUOTE ()`; **не** вважати його підтвердженням незалежності семантики від Rust або релізної готовності.

## Обмеження й наступне злиття

- Однакові фізичні біти двох епох **інформаційно нерозрізненні без зовнішнього provenance**. Навіть типова драбина й SHA-256 не доводять джерело; без довіреного власницького маніфесту/підпису видавець не повинен робити публікацію. Цей скрипт **перевіряє узгодженість** квитанцій, але не їхню криптографічну автентичність.
- `SENS_RELEASE_GO_SHA` і політика реального релізу — окремий власницький дозвіл. Новий інструмент нічого не створює у світі, не змінює `main`, не позначає semantic law ратифікованим.
- Тип `DomainWord` не замінює SENS семантику й не робить runtime фізичну пару `(width,bits)` автоматично callable; це лише механічний компіляційний захист.
- Hosted ABI `std.heap.c_allocator`, E1/E2/E3, freestanding ESP32 і повне відділення Rust evaluator залишаються окремими пунктами #5779/#5775/#5776/#5772.


## Реальна публікація: окремий власницький дозвіл і доказ перекладу

`scripts/verify-zig-publication.py` **створює фізичний артефакт**, на відміну від read-only `verify_zig_publication_candidate.py`. Тому він тепер fail-closed, якщо немає `--owner-approved-provenance-sha256` — SHA-256 *сирих байтів усього* маніфесту `sens-publication-provenance/v1`, ухваленого та закріпленого **ПОЗА** публікатором в окремому довіреному контексті. Значення, щойно обчислене самим автором кандидата із власного JSON і підставлене в ту саму команду, не є незалежним дозволом власника. Перевірка хешу — контроль цілісності обраного довіреного входу, **не криптографічна автентифікація особи й не електронний підпис**. Без достовірного зовнішнього джерела дозволу випускати артефакт не можна.

Для `source_era=legacy` потрібна **зовнішня** `translation_receipt` у маніфесті із абсолютним `path` та SHA-256 її JSON. Вона зберігається тільки поза Zig, має `schema=sens-translation-receipt/v1`, `source_era=legacy` і прив'язує `source_sha256`, `physical_sha256`, `canonical_source_sha256` (вихід Zig `open`/чинного SENS D2 reader). Публікатор порівнює всі три фактичні величини й повторно читає обидві квитанції перед атомарним записом. Історичний `source_era=auto`, відсутня чи змінена квитанція, помилковий SHA або mismatched canonical projection — відмова **до** створення виходу.

Виклик у довіреному релізному середовищі (значення PIN має надійти з незалежного рішення власника, не від неперевіреного файла):

```bash
python3 scripts/verify-zig-publication.py \
  --input /approved/candidate.sens \
  --source-file /approved/source.lisp \
  --provenance /approved/provenance.json \
  --owner-approved-provenance-sha256 "$OWNER_APPROVED_PROVENANCE_SHA256" \
  --zig-runner /pinned/sens-trit \
  --zig-runner-sha256 "$ZIG_RUNNER_SHA256" \
  --sens-executor /pinned/sens-executor \
  --sens-executor-sha256 "$SENS_EXECUTOR_SHA256" \
  --expected-output-sha256 "$OWNER_APPROVED_OUTPUT_SHA256" \
  --out /publish/candidate.sens
```

Тести механіки `tests/test_verify_zig_publication.py` використовують несправжні локальні executable-фікстури **лише для перевірки відмов на межі**; вони не засвідчують правильність SENS-обчислення. Реальний публікаційний дозвіл потребує окремого незалежного власницького рішення, реального нативного SENS свідка й пінованого Zig runner. На відміну від фізичного SHA, жоден із цих доказів не може бути виведений із самих бітів T5.
