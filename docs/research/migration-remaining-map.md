# Карта міграції SENS: блокер → доказ → admission

**Оновлено:** 2026-10-09
**Аудований main:** `ae3bd10d3d1fce677a11de5835ea3fc5c2068eb6`
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

Його історичні/current **TEXT** observables мають звіт 9/9, але точна фізична картина тепер звузилася: latest #4799 head `0e6ba1ef…` пройшов фізичний пустий-block виклик **1/1**, тоді як вісім інших cases зупиняються на quoted machine-symbol data (`mov`, `r1`, `branch`, labels). Job лог прямо каже `QUOTED_SYMBOL_DATA=BLOCKED_WITH_REASON`, `ORIGINAL_REPOSITORY_WRITTEN=false`, `RELEASE_ADMITTED=false`. Це корисний фізичний піддоказ, не admission.

### Поточні proof lanes

| Ланка | Стан на 2026-10-09 | Наступна дія |
|---|---|---|
| [#4799 Text7 binder + physical probe](https://github.com/juv4uk/sens/pull/4799) | Latest fetched HEAD `0e6ba1ef…`; binding, D2/W7, exact AST, codec/triple and source-integrity focused checks are green. The independent physical Rust witness now executes the original-only T5 for the empty-block case (**1/1**), but blocks when the probe includes quoted symbol data; the full Hosted CI remains IN_PROGRESS. The separate admission workflow still writes only the test canary. | Keep current binder fixes. Implement the reversible quoted-datum law in the existing D2/Text7/value reader/runtime lane: do not heuristically convert every W7 list into text, and do not add D10 identities. Then rerun all 9 physical cases, not merely source-text parity. |
| [#4789 explicit Core4](https://github.com/juv4uk/sens/pull/4789) | Head `8dfe0f0c…`: current focused `Physical T5 explicit Core4 oracle` PASS; triple projection, D2/W7, syntax, Compiler role та W9 carrier PASS. Full Hosted CI був IN_PROGRESS на останній poll. | Після Text7 binder law звести на один актуальний main head й повторити full Hosted. Bare `eval` лишається без Core4, `eval-core4` явно завантажує Lisp-owned `lib/core4.lisp`. Не дублювати LIST/APPEND у Rust. |
| [#4803 shared Clippy repair](https://github.com/juv4uk/sens/pull/4803) | Latest head `ccfe6779…`: **strict Clippy + library tests PASS** (run `37861897700`), English identity/CLI ratchet PASS (`37861897654`), T5 syntax, triple projection, historical/current observer and incremental ratchet also PASS. Full Hosted and several cross-repo gates remain IN_PROGRESS; not merged. The ratchet false-positive was fixed by constructing its negative `car` input at runtime. | Wait for full Hosted and remaining independent gates, then coordinate common-base replay with #4789 / #4799; do not merge on focused CI alone. |
| [#4797 public CLI proof](https://github.com/juv4uk/sens/pull/4797) | Відкритий stacked PR на старішому #4789 head `0a7e6de…`; попередні CLI/Hosted runs RED і branch не перебазований. | Після #4799/#4789 стабілізації перенести CLI proof на один current-head parent й перевірити окремі `sens-trit` процеси з фізичними байтами. |
| [#4650 source-pinned admission](https://github.com/juv4uk/sens/issues/4650) | The 9/9 source-text comparison passes, physical T5 is only 1/1 for the empty-block call; the other eight are blocked on symbol datum `mov` (reported around word 551). No original repository file written and release admission remains false. Closed unmerged #4774 gives no credit. | Owner-approved quote datum representation → original blob → physical T5 → Rust `open/eval-core4` → 9/9 OLD↔CURRENT physical observables → canonical Ukrainian `.lisp` / physical `.sens` / extensionless view + hashes + no-clobber receipt. |

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
| D2 control / quoted structure | D2 — єдина структурна authority. The quote-data gap is now concrete: source atom `mov` must survive as a value while ordinary quoted lists (including shapes resembling W7 frames) remain structural. Add a bijective tagged/context-explicit datum encoding in the current D2/Text7/value lane; fail closed on malformed/unrepresentable data. No D10 workaround. |
| PRINT та інші host effects | Власне host/island capability + observable-effect oracle; не виносити до D10 заради зняття блокера. |
| Declarative/data/archive `.lisp` | SHA-grounded classification і schema/data contract; не видавати за executable programs. |
| Транспорт / view / Core4 / CLI / Clippy | Інфраструктурні ворота; не нові мовні значення і не D10-residents. |

## D10: паралельне дослідження, не міграційний обхід

Канонічний inventory стан на останньому перевіреному main: **625 selected / 1024**, **399 remaining**, **369 selected-but-unplaced**, **256 law-forced**, **0 ratified**. Після #4804 `knowledge/d10-library-harvest-v1.json` зберігає свої **39** уже розібраних research rows; **102 сирі donor-symbol names** лежать окремо в `knowledge/d10-library-source-symbols-v1.json`. Вони `research-unratified` та **не додаються до 625**. Вісім Flavors/restart proposals із #4800 — окремий ledger, теж поза selected count; #4013 має source-pinned HOLD для `NARRATE-ANSWER` та новий [HOLD для `SCIENTIFIC-CONSTANT-CLAUSE-PROJECTION`](https://github.com/juv4uk/sens/issues/4013#issuecomment-6071596836), який перевіряє семиклаузну проєкцію SI-запису зі збереженням одиниць і provenance. Обидва — +0 до selected; у другого explicit `HOLD-COMPOSITION-TEST`, `coordinate=null`, поки не доведено залишковий закон понад композицію.

Пріоритет D10 — кандидати з новим універсальним observable law, а не ще одна назва для механізму. Для кожного потрібні immutable source blob + line, arity/type/preconditions, позитивні/негативні falsifiers, dedup проти всіх D1–D9 і 625 already-selected candidates, derivability analysis, cross-substrate ownership та явний owner review. `coordinate=null`, доки позицію не виведено/ратифіковано.

**Заборонено лікувати через D10:** D2 framing/control, Text7/Local binders, W8 source era, T5 encoding/decoding, extensionless view, Core4 bootstrap, Rust CLI, Clippy або host I/O. Це власні блокери своїх шарів.

## Остання координаційна поправка — 2026-10-09

- [#4799](https://github.com/juv4uk/sens/pull/4799) current head `48c3ffaf…` isolates the global/local binding fixtures from newline-token leakage; current-head CI is freshly queued/in progress. Treat as NOT YET GREEN until the corrected focused tests plus complete Hosted/physical oracle gates finish.
- [#4789](https://github.com/juv4uk/sens/pull/4789) physical Core4 focused oracle passed; full Hosted remains IN_PROGRESS. [#4803](https://github.com/juv4uk/sens/pull/4803) strict Clippy/library tests and English identity ratchet now PASS; full Hosted and several independent gates remain IN_PROGRESS, so do not merge yet.
- [#4805](https://github.com/juv4uk/sens/pull/4805) is this doc, OPEN/unmerged. D10 comment [NARRATE-ANSWER](https://github.com/juv4uk/sens/issues/4013#issuecomment-6071302444) remains HOLD, 0 coordinates/ratifications; inventory 625 unchanged. #4804 preserved 39 reviewed candidate rows and moved 102 raw names to the separate source-symbol file.

## Координаційне правило

Один файл/власник/branch/PR на шляхову область. Не створювати конкуруючих parser/converter/runtime implementations. Спочатку завершити та перевірити один original vertical slice; потім узагальнювати його доказовий pipeline на інші cohorts. Не змінювати production pins чи публікацію `master`, доки exact-source admission і release Hosted gate не GREEN.
