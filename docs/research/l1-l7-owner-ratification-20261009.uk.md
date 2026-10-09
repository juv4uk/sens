# Ратифікація власника: L1–L7 — спадкова форма → канон

**Дата:** 2026-10-09. **Нормативна семантика — тільки рішення власника L1–L7.**
Механіка: scripts/ratified_l1_l7_migrate.py. Існуючі reader і
фізичний T5 codec повторно використовуються; паралельного reader немає.

| Правило | Закон власника | Механічна реалізація / жорстка межа |
|---|---|---|
| L1 | COND: тільки exact PredicateBit 1 або 0; вичерпання → structural () | Статично допускаються лише явні D1 1/0 і ратифіковані predicate-head. Жодного truthiness, ніякого автоматичного видалення (0)/(1) у legacy три-членних клаузах. Вичерпання не замінюємо вигаданою else-клаузою; runtime parity має довести структурне (). |
| L2 | (t expression) → (1 expression); t не спецформа | Замінюється лише тест двочленної COND-клаузи. Виклик (t ...) поза нею — BLOCK. |
| L3 | Імена викликів → лише ратифікована D1–D10 координата | Точні координати читаються з поточних канонічних D3–D6/D8/D9 таблиць. D7 текстовий, D1 — результат, D2 — структура; це не callable slots. D10-інвентар зараз не має ратифікованих координат: невідоме/неоднозначне ім'я → BLOCK + D10 proposal у звіті. |
| L4 | equal?, null — ратифікований D8 resident або похідна D3 | Існуючий D8 equal? → 11110111. Для незнайденого резидента — BLOCK до появи незалежно доведеної, згенерованої D3 розгортки; не вбудовувати формули вручну. |
| L5 | Retired structural-kind/identity-relation → поза корпусом; зберегти археологію | Розпізнана спадкова executable-конструкція блокується. Видалення тільки з окремим архівним provenance, не через сліпе in-place редагування. |
| L6 | Старі fixtures перегенерувати канонічним тулом | Вхідний шлях з fixtures → BLOCK до окремого канонічного генератора; не підміняти тестову істину ручними патчами. |
| L7 | Source, який не читається, — не чіпати | Parse/Unicode failures у звіт BLOCK; оригінальний файл незмінений, рішення за власником. |

## Протокол

1. Reader: виклик чинного migrate-three-pass.py parser (strip_comments + tokenize + Parser).
2. L1–L7: AST-тріаж executable head/COND без переписування quoted data й без ототожнення історичного SID8 з поточним D8. Default source-era auto блокує вісім бітів у head; current — лише за явного provenance.
3. Emit: тільки доказові binary-domain atoms і структурні D2 слова → наявний sens_t5_codec; decoding/typed-word digest must match. Text7 local variable/binder frames не вгадуються.
4. **Семантичний оракул обов'язковий для --apply.** Зовнішня незалежна програма повинна прийняти SOURCE.lisp і тимчасовий candidate.sens, повернути JSON із двома однаковими 64-hex SHA-256 з полями source_semantic_sha256 і candidate_semantic_sha256. typed_word_sha256 у звіті — лише доказ транспорту, **не** доказ семантики.
5. Лише після oracle PASS — створення без перезапису і новий .sens у *окремому* каталозі. Без оракула — read-only dry-run; BLOCK → жодного вихідного файлу.

Приклад аудиту без редагування:

    python3 scripts/ratified_l1_l7_migrate.py lib/some.lisp --report /tmp/l1-l7.json

Приклад дозволеного стадіювання (після незалежної реалізації oracle):

    python3 scripts/ratified_l1_l7_migrate.py lib/some.lisp --source-era current --apply --out /tmp/sens-candidates --oracle-bin /path/to/independent-semantic-oracle

**Не виконувати масову міграцію та не зливати в main за одними unit-тестами цього скрипту.**
Потрібні окремі позитивні/негативні runtime-оракули, D1/D3 truth/COND polarity,
повний Hosted CI, леджер origin SHA та green main.
