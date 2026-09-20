# План реалізації Canon Laws V2

## Українська

**Мета:** повернути `lib/canon.lisp` у повну відповідність із уже ратифікованими #217/#218/#244: явний контроль, структурні результати `atom/eq` і канон() як `()`, а не FALSE.

**Архітектура:** ідентичності канон()+7 та їхні peer surfaces залишаються незмінними. Історичні T/NIL-вердикти замінюються явними Lisp-даними. Окрема Canon-law повертає `(canon-law-result <law> satisfied|violated)`, а агрегований результат — `(canon-conformance satisfied|violated)`. Канонічний трикомпонентний `cond` робить явне зіставлення результату. Host-тести лише транспортують фактичний результат у вже наявний Lisp-owned witness protocol.

### Крок 1 — RED executable witness для Canon V2

Файли:
- створити `tests/fixtures/canon-laws-v2-v1.lisp`;
- створити `crates/my-lisp/tests/canon_laws_v2_contract.rs`;
- додати observer у `scripts/test-current-semantic-slice.sh`;
- класифікувати observer у authority inventory.

Дії:
1. Зафіксувати Lisp-owned очікування для канон(), `atom/eq`, `car/cdr`, quote suppression, explicit-control short-circuit, symbolic peer surface та aggregate conformance.
2. Очікувані результати — явні Canon records, ніколи не `t/()` як pass/fail.
3. Rust observer завантажує core + `lib/canon.lisp`, виконує рядки і передає actual у `witness-verdict`/`witness-status`.
4. Спочатку довести RED на поточному історичному Canon.

### Крок 2 — GREEN: канон() + structure + structural observation + control

1. Зберегти `canon-empty-list` буквально як структурне `()`.
2. Додати Canon-owned record constructors зі звичайних Lisp-даних.
3. Переписати laws під ратифіковані #218 результати: `atom -> (structural-kind ...)`, `eq -> (identity-relation ...)`.
4. Увесь Canon-control перевести на #217 трикомпонентні clauses `(query expected-datum expression)`.
5. Зберегти short-circuit/evaluation suppression witnesses.
6. Переписати symbolic `?:/.?/=?/:/:п/:р/'` witness без T/NIL truthiness.
7. Агрегувати список law-results рекурсивно без generic truth coercion.
8. Прогнати focused semantic lane та authority guards.

### Крок 3 — межі цього slice

Не робити тут:
- runtime-активацію #216 exact-Q — цінність `feat/binary-math-216` буде зібрана окремо після актуалізації Canon;
- redesign richer reasoning;
- глобальне видалення migration-only двокомпонентного `cond`;
- зміну semantic IDs або peer surfaces;
- machine/CML lowering до окремого replay.

### Крок 4 — збереження цінних гілок

До будь-якого cleanup зберегти/переграти:
- `feat/binary-math-216` — 3 унікальні коміти з executable #216 fixtures/tests;
- `research/223-many-valued-logic` — 7 унікальних комітів, research corpus + Lisp-прототип Belnap FOUR;
- PR #208 — цінний bounded `COND + CAR(CONS)` machine composition, але semantic witness треба осучаснити;
- PR #173 — one-Lisp-truth native/meta/CML, replay на новий witness protocol;
- PR #248/#249 — reasoning slices, replay на current `main`;
- PR #252 — залишити RED до root-cause authority/Windows/WASM failures;
- #172/#164 — RED historical probes, не видаляти до повного harvest #173.

**Правило перевірки:** гілка не вважається disposable лише через вік. Її можна прибирати тільки якщо `main...branch` має `ahead_by=0` або вся унікальна цінність явно перенесена в актуальну гілку/issue.

## English

**Goal:** bring `lib/canon.lisp` back into semantic authority after #217/#218/#244 changed control, structural observation, and canon() semantics.

**Architecture:** keep canon()+7 identities and surfaces immutable. Replace historical T/NIL conformance verdicts with explicit Lisp data. Individual laws return `(canon-law-result <law> satisfied|violated)`; aggregate conformance returns `(canon-conformance satisfied|violated)`. Canonical three-part `cond` performs explicit result matching. Host tests only transport outcomes into the existing Lisp-owned witness protocol.

Implementation order: RED Lisp-owned Canon V2 witness → GREEN canon()/structure/atom/eq/control rewrite → focused semantic verification → separate harvest of #216/research/open-PR branch value. No branch is deleted until its unique commits are proven merged or explicitly harvested.
