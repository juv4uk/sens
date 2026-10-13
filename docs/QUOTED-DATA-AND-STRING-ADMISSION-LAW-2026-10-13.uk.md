# Закон допустимості цитованих D2-даних і String-значень у T5-проєкції джерела

**Статус: ПРОПОЗИЦІЯ (PROPOSED). Ратифікація власником ще не надана.** Дата: 2026-10-13.

**Батьківський блокер:** [#5406](https://github.com/juv4uk/sens/issues/5406)
(`InvalidBinaryProjection` / змішане `file-authority.lisp` у фізичній файловій гвардії).

**Суміжні лейни, яких цей документ НЕ перехоплює:** [#3910](https://github.com/juv4uk/sens/issues/3910)
(Text7 identifier/binder framing law), [#4799](https://github.com/juv4uk/sens/pull/4799)
(MERGED, contextual Text7 binding), [#5689](https://github.com/juv4uk/sens/pull/5689)
(активний лейн `crates/sens/src/text7.rs`), [#4650](https://github.com/juv4uk/sens/pull/4650)
(machine-block parity).

## Навіщо цей документ

Мігратор `scripts/migrate-to-sens-codes.py` (маршрут `--binary-mirror`, функція
`binary_rewrite`) сьогодні fail-closed на двох класах:

- `UNADMITTED_TEXT7_CONTEXT '<atom>' … (quoted-data)` — atom у тілі `QUOTE`;
- `UNADMITTED_STRING_VALUE "<…>"` — String-значення.

Це не збій, а свідома відмова: `emit_text7_atom` дозволяє лише ролі
`{binder, reference, call-head}` і **навмисно** не має ролі даних. `AGENTS.md:77`
прямо забороняє непідтверджені скорочення для **quote**, three-field COND,
локальних Text7 binder та неявних literals. `docs/research/migration-blocker-backlog.md:40–57`
описує цитовані atomи як найвужчий вузол.

Блокер стає критичним для фізичної файлової гвардії (#5406):
`tools/important_file_guard.py::build_bundle` збирає **змішане** джерело
(`lib/core.lisp` + `knowledge/file-authority-policy.lisp` +
`knowledge/foreign-tools-census.lisp` + генеровані `*file-authority-source-status*` /
`*file-authority-input*` + `knowledge/file-authority-guard.lisp`) і передає його в
міграцію.

**Замірено на живому бандлі** (`head=1ef983409`, `base=5ec8f5840`;
`python3 tools/important_file_guard.py --base <ancestor> --output /tmp/fa.lisp`):

| джерело | QUOTE-форми `(001 …)` | String-літерали `"…"` |
|---|---|---|
| `lib/core.lisp` | 98 | 28 |
| `knowledge/file-authority-policy.lisp` | 1 | 22 |
| `knowledge/foreign-tools-census.lisp` | 1 | 18 |
| `knowledge/file-authority-guard.lisp` | 0 | 218 |
| **разом** | **100** | **~286** |

**Живий CI:** `important-file-guard.yml`, run `38373654903` (head `2c1262f5`) —
`SENS_FILE_AUTHORITY_MIGRATION_BLOCKED: UNADMITTED_TEXT7_CONTEXT 'binary' at 13:16 (quoted-data)`.

**Джерело найвужчого випадку** — `lib/core.lisp:11–13`
(`(DEFINE binary (LAMBDA (width) (LIST (QUOTE binary) width)))`, коміт `35922af12`),
що продукує фізичний формат `(binary <width>)`, який споживає
`tests/test_physical_t5_evidence_integrity.py:148`. Отже це не мертвий код, а
дескриптор фізичного формату.

## Чинні закони, на які спирається (не переглядаються)

- D3 `001` = `quote` (`lib/domains/d3.lisp`); D4 `0011`=`define`, `0010`=`lambda`,
  `1110`=`list` (`lib/domains/d4.lisp`).
- D9 `010111100` = `CANON-LAW-QUOTE-SUPPRESSES-EVALUATION`; D9 `110101100` = `SYMBOL?`
  (`lib/domains/d9.lisp`).
- D7 v2: `knowledge/d7-keyboard-v2-ratified.json` — `sens.d7.keyboard/v2`, ширина 7,
  128 клітинок (`docs/d7-keyboard-v2.uk.md`).
- D2-структура: `10`=open, `00`=separator, `01`=close, `11`=dot; D3 `000`=empty.

## Пропонований закон

1. **QUOTE як голова.** `QUOTE` (D3 `001`) — виконувана голова, що **пригнічує
   обчислення** свого тіла (D9 `010111100`). Тіло QUOTE — **дані**, не executable-код.
2. **Цитований atom.** Atom у тілі QUOTE кодується як D2-рамка з D7/W7
   spelling-клітинок з роллю **`quoted-datum`** (окремою від `reference`); він **не** є
   executable-посиланням і **не** потребує попереднього зв'язування.
3. **Цитований порожній список.** `(001 ())` → `001` + D3 `EMPTY = 000`.
4. **Цитований список.** `(001 (a b c))` → D2-структура; кожен елемент адмітується
   рекурсивно з роллю `quoted-datum`; голова списку **не** резолвиться як callable.
5. **Цитоване бітове слово.** `(001 <bits>)` → точне слово D1–D10 **як дані**, лише
   якщо ширина дорівнює ратифікованій ширині домену; інакше BLOCK.
6. **Самопосилання дескриптора.** `(DEFINE binary (LAMBDA (width) (LIST (QUOTE binary) width)))`
   допускається: `binary` у тілі QUOTE — дані, а не незв'язане посилання.
7. **String-значення — окремий закон.** `"…"` **не** зливається з символами.
   Пропозиція: per-character W7 у D2-рамці з роллю `string-datum`.
   **До окремої ратифікації String лишається BLOCK.**
8. **Fail-closed негативні контролі (мусять лишатися BLOCK):** backquote `` ` `` і
   splice `,@`; reader-скорочення `#'`; незв'язані executable-посилання
   (роль `unbound-reference`); числові літерали D24+ без доменного конверта;
   D2-маркери (`10/00/01/11`) у позиції даних.

## Відкриті вибори (потребують рішення власника)

- **(a)** Чи сама проєкція розрізняє `quoted-datum` vs `reference`, чи розрізнення
  живе лише в Rust-читачі (контекст після `001`)?
- **(b)** String: per-character W7, чи окремий String-конверт (довжина/рамка)?
- **(c)** Сфера: спершу лише бандл #5406, чи загальний закон для всього `binary-mirror`?

## Що НЕ є предметом цього закону

- Введення будь-яких нових callable-резидентів D7/D10.
- Зміна семантики `lib/core.lisp` чи самого дескриптора `binary`.
- Обхід інших open-лейнів (#3910, #4650, #5689).
- Ратифікація String (окремий акт).

## Відтворювані перевірки

- Замір бандла: `python3 tools/important_file_guard.py --base <ancestor> --output /tmp/fa.lisp`.
- Міграція: `python3 scripts/migrate-to-sens-codes.py /tmp/src --foundation knowledge/d1-d9-foundation.json --binary-mirror /tmp/out --report /tmp/report.json`.
- Негативні контролі лишаються зеленими: `python3 scripts/test-t5-migrator-contract-guard.py`
  (жоден наявний BLOCK цим документом не знімається).
- Позитивні контролі — додаються окремим кроком **після** ратифікації закону
  (quoted atom/list/empty/binary-word; String — окремо).

## Провенанс

- Запит власника 2026-10-13: «Визначити runtime-закон quoted/D7», далі «Контракт-first, потім поетапно».
- Рекон: `lib/core.lisp:11–13`; `scripts/migrate-to-sens-codes.py`
  (`binary_rewrite` 680+, `emit_text7_atom` 719–733, QUOTE-гілка 991–992, блокер 977–986);
  `docs/research/migration-blocker-backlog.md:40–57`.
- Цей документ є **тільки ПРОПОЗИЦІЄЮ** і не створює semantic authority до ратифікації.
