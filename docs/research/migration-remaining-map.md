# Карта міграції SENS: блокер → доказ → admission

**Оновлено:** 2026-10-09
**Аудований main:** `d0ef7de69b61b5a7e8c65e5f3284eefac0426562`
**Нормативні власники:** [#4449](https://github.com/juv4uk/sens/issues/4449), [#4430](https://github.com/juv4uk/sens/issues/4430), [#4250](https://github.com/juv4uk/sens/issues/4250)

> **Облікова норма:** physical file, generated view, fixture, source-only AST cutover або успішний окремий CI job ≠ completed original migration.

## Перевірений облік

| Метрика | Поточне значення | Як трактувати |
|---|---:|---|
| Відстежувані оригінальні `.lisp` | 503 | Повний audited census |
| Наявні same-stem фізичні `.sens` | 13 | Переважно fixture/canary, не 13 міграцій |
| Наявні generated extensionless views | 13 | Текстові read-only views, не machine files |
| Оригінали без фізичної пари | 490 | Не всі є програмами |
| SHA-reviewed NONPROGRAM | 92 | Класифікація, не executable migration |
| Archived NONPROGRAM | 119 | Архів, не executable migration |
| Active або unclassified | 279 | Черга triage; не стверджувати, що всі 279 — програми |
| Повністю сертифіковані original executable migrations | **0** | Єдиний release/admission лічильник |
| Реальні source-level exact-domain cutovers | 1 файл | `lib/compiler-nucleus.lisp` (#4752); це не physical-T5 admission |

На `lib/**/*.lisp` припадає 128 файлів. Попередній запис “ADMITTED 1/128” був надто сильним: механічна придатність або наявність `.sens` не доводять незалежної семантичної parity. Для `lib/machine/block.lisp` доказ досі не охоплює всі дев'ять історичних спостережень через physical T5 у сучасному Rust runtime.

## Головна стратегія: один golden vertical slice, не масовий rewrite

Перший цільовий файл — незмінений historical `lib/machine/block.lisp`, source blob:

`200201b741787c4e144ad4194848acf51d7b439e`

Його історичні/current **TEXT** observables уже мають звіт 9/9, але той самий звіт прямо ставить `PHYSICAL_T5_ORACLE=NOT_VERIFIED`. Попередній кандидат на 459 bytes / 466 typed words мав `SYNTAX_ONLY_UNVERIFIED`, `files_written=0`, `oracle=NOT_VERIFIED`. Це не admission.

### Поточні proof lanes

| Ланка | Стан на 2026-10-09 | Наступна дія |
|---|---|---|
| [#4799 Text7 binder replay](https://github.com/juv4uk/sens/pull/4799) | Head рухався під час цього triage; останній відомий `581bb2d8…`, свіжі CI переважно QUEUED. На попередньому head `226ce156…` дві нові негативні рамкові перевірки стали RED: global DEFINE target ↔ callable-head identity та локальне затінення binder/reference. Це не T5 packing failure; розв'язати зв'язність кадрів, не послаблюючи очікувань. Окремий Hosted blocker `convertible=311` також вимагає parser/lowering gate, а не повернення Ukrainian heads у SID8. | Перевірити фактичну послідовність декодованих W7 кадрів для DEFINE target, global call, LAMBDA binder та shadowed local call; поправити генератор/role routing і додати exact negative witnesses. Далі замінити legacy sens-to-sens census на parser/lowering proof. Unknown/ambiguous W8 мусить BLOCK; не виключати compiler-nucleus і не рахувати TEXT parity як physical admission. |
| [#4789 explicit Core4](https://github.com/juv4uk/sens/pull/4789) | Head `8dfe0f0c…`: current focused `Physical T5 explicit Core4 oracle` PASS; triple projection, D2/W7, syntax, Compiler role та W9 carrier PASS. Full Hosted CI був IN_PROGRESS на останній poll. | Після Text7 binder law звести на один актуальний main head й повторити full Hosted. Bare `eval` лишається без Core4, `eval-core4` явно завантажує Lisp-owned `lib/core4.lisp`. Не дублювати LIST/APPEND у Rust. |
| [#4803 shared Clippy repair](https://github.com/juv4uk/sens/pull/4803) | Семантично нейтральні mainline lint repairs у head `d5f88ac6…`; strict Clippy / Hosted новий run QUEUED. Ще не merged. | Чекати strict Clippy + full Hosted GREEN; потім упорядкувати merge/replay так, щоб #4789 і #4799 не втратили branch-specific proof. Не оголошувати CI GREEN лише на основі попереднього набору lint-ів. |
| [#4797 public CLI proof](https://github.com/juv4uk/sens/pull/4797) | Відкритий stacked PR на старішому #4789 head `0a7e6de…`; попередні CLI/Hosted runs RED і branch не перебазований. | Після #4799/#4789 стабілізації перенести CLI proof на один current-head parent й перевірити окремі `sens-trit` процеси з фізичними байтами. |
| [#4650 source-pinned admission](https://github.com/juv4uk/sens/issues/4650) | Потрібен фінальний source-specific доказ. Закритий без merge #4774 не дає credit. | Оригінальний blob → canonical Ukrainian parse/lowering → physical T5 → Rust `open/eval-core4` → 9/9 OLD↔CURRENT physical observables → triple + hashes + no-clobber receipt. |

### Acceptance для переходу 0 → 1

1. **Provenance:** перевірений оригінальний Git blob SHA і pass-ledger; файл-джерело не переписується.
2. **Семантика:** current Ukrainian heads lower у точні ратифіковані D1–D9 identities; D2 володіє структурою; Text7 binder правильно зберігає global/local scope і quoted data. Ніяких здогаданих SID8/W8 переходів.
3. **Фізична форма:** `path/name.sens` — реальні packed T5 bytes; EOF задає довжина файла, `2` лише транспортний роздільник/padding. Перевірити `decode(encode(words))`, `encode(decode(bytes))` і canonical padding.
4. **Повне виконання:** фактичний Rust `sens-trit open` + явний `sens-trit eval-core4` над байтами `.sens` підтверджує **всі 9** названих old/current спостережень, а не лише source-text або окремий LIST/APPEND canary.
5. **Три проєкції:** `.lisp` (канонічна українська `ук`), same-stem physical `.sens`, extensionless spaced-bit generated view узгоджені й обернені на допущеному корпусі.
6. **Receipt:** source SHA, exact typed-word digest, physical-byte SHA256, view digest, tamper/no-overwrite negative tests, independent oracle result і main CI GREEN.

Лише тоді один незмінений historical source отримує **+1 certified admission**. Після цього саме цей receipt/driver перетворюється на cohort template; кожен інший оригінал або отримує такий доказ, або конкретний BLOCK reason. Не прогнозувати completion за кількістю механічних candidate writes.

## Класи блокерів і важелі

Класи можуть перекриватися; числа нижче — діагностичні зрізи, їх **не можна підсумовувати**.

| Клас | Рішення |
|---|---|
| Контекстні global/local імена (Text7 + Local) | Єдиний binder law #3910/#3135, потім parser-aware source proof у #4799. Не вважати один merge автоматично +67 certified migrations. |
| Історичні W8/SID8 голови | Прив'язати кожний original до immutable era/provenance; неоднозначний `auto` BLOCK, не вгадувати D8 successor. |
| D2 control / quoted structure | D2 — єдина структурна authority; позитивні та негативні parser/runtime cases. |
| PRINT та інші host effects | Власне host/island capability + observable-effect oracle; не виносити до D10 заради зняття блокера. |
| Declarative/data/archive `.lisp` | SHA-grounded classification і schema/data contract; не видавати за executable programs. |
| Транспорт / view / Core4 / CLI / Clippy | Інфраструктурні ворота; не нові мовні значення і не D10-residents. |

## D10: паралельне дослідження, не міграційний обхід

Канонічні machine files на current main: **625 selected / 1024**, **399 remaining**, **369 selected-but-unplaced**, **256 law-forced**, **0 ratified**. Новий `knowledge/d10-library-harvest-v1.json` має 102 source-grounded research rows (quantity/translation/SI), але вони `research-unratified` і **не додаються автоматично до 625**. Вісім Flavors/restart proposals із #4800 — окремий ledger, теж поза selected count; #4013 отримав окремий HOLD для `NARRATE-ANSWER` із `lib/narrate.lisp` source/line, поведінковими falsifiers та dedup-застереженням.

Пріоритет D10 — кандидати з новим універсальним observable law, а не ще одна назва для механізму. Для кожного потрібні immutable source blob + line, arity/type/preconditions, позитивні/негативні falsifiers, dedup проти всіх D1–D9 і 625 already-selected candidates, derivability analysis, cross-substrate ownership та явний owner review. `coordinate=null`, доки позицію не виведено/ратифіковано.

**Заборонено лікувати через D10:** D2 framing/control, Text7/Local binders, W8 source era, T5 encoding/decoding, extensionless view, Core4 bootstrap, Rust CLI, Clippy або host I/O. Це власні блокери своїх шарів.

## Остання координаційна поправка — 2026-10-09

- [#4799](https://github.com/juv4uk/sens/pull/4799) зараз рухає HEAD і перезапускає перевірки після двох знайдених глобальних/локальних Text7 frame-coherence контрприкладів на попередньому head. Не приймати попередні 9/9 TEXT або canary gate за physical admission.
- [#4789](https://github.com/juv4uk/sens/pull/4789) physical Core4 focused oracle пройшов; full Hosted ще не підтверджено GREEN. [#4803](https://github.com/juv4uk/sens/pull/4803) окремо закриває повторно виявлені mainline/test-only Clippy лінти — суворі job і Hosted ще QUEUED на останньому poll.
- [#4805](https://github.com/juv4uk/sens/pull/4805) — саме цей документ; OPEN, не змержений. D10 comment [NARRATE-ANSWER](https://github.com/juv4uk/sens/issues/4013#issuecomment-6071302444) також лише HOLD; inventory 625 без змін.

## Координаційне правило

Один файл/власник/branch/PR на шляхову область. Не створювати конкуруючих parser/converter/runtime implementations. Спочатку завершити та перевірити один original vertical slice; потім узагальнювати його доказовий pipeline на інші cohorts. Не змінювати production pins чи публікацію `master`, доки exact-source admission і release Hosted gate не GREEN.
