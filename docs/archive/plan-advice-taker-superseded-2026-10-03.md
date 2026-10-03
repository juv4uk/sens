# Активний план my-lisp

> **Статус:** активний roadmap.  
> **Оновлено:** 2026-09-10.  
> **Головна мета:** Advice Taker. `my-lisp` — мова й execution substrate, що служить цій меті.

Цей файл містить актуальний порядок пріоритетів і коротку карту вже
підтвердженого фундаменту. Завершені деталі живуть у git history, ADR,
conformance-тестах та evidence-документах, а не повертаються в backlog як
псевдо-задачі.

## Ієрархія планів

1. **`PLAN.md`** — єдиний активний порядок пріоритетів для `my-lisp`.
2. **`CLEAN_CODE_PLAN.md`** — domain-roadmap якості й API.
3. **`docs/ecosystem-roadmap.md`** — roadmap `my-lisp` / `cml` / `fpga-lisp`.
4. **ADR і language contract** — нормативні рішення; roadmap не може їх переписувати.
5. **Тести й CI** — доказ стану. Claim не може бути сильнішим за найсильніший експеримент.

## Правило пріоритету

Перед новою роботою:

1. Чи наближає це Advice Taker — reasoning, knowledge, explanation або NL bridge?
2. Якщо це ядро: чи усуває це реальну semantic dependency, яка заважає пункту 1?
3. Чи є негативний тест або інший спосіб спробувати зруйнувати твердження?

Якщо відповідь на перші два питання «ні», робота не є активним пріоритетом,
навіть якщо технічно цікава.

---

# A. Підтверджений фундамент — не розширювати без причини

## A1. Closed semantic core

- ✅ Canon 0: `()` як ground object.
- ✅ Закритий McCarthy-7 semantic operation set.
- ✅ `lambda` / `define` — evaluator capabilities, не primitive identities.
- ✅ Language-owned похідні операції не повинні тихо повертатися в Rust builtins.

## A2. Meta-evaluator ownership

Machine-readable evidence matrix `knowledge/meta-eval-evidence.lisp` є
авторитетом для parity-статусів; людська проєкція генерується з неї. На
2026-09-10 усі **34/34 required rows confirmed**.

Підтверджені main-path slices включають:

- ✅ lexical closures, nested capture і lexical shadowing;
- ✅ first-class builtins;
- ✅ macros і macro arity/error propagation;
- ✅ `def` / `define` top-level semantics;
- ✅ self recursion і dependency-aware finite mutual-recursion SCC;
- ✅ variadic і dotted lambda;
- ✅ shared top-level definition frame без dynamic scope;
- ✅ empty-program no-op semantics;
- ✅ application order і first-failure short-circuit;
- ✅ named error-kind correspondence та ратифікована diagnostic-detail boundary;
- ✅ registry-derived Canon / necessary-form surface identity у meta bootstrap.

Межі claim-а лишаються навмисно вужчими за список зелених тестів:

- `meta-eval` — explicit Lisp-owned self-hosting witness, не always-loaded runtime;
- 34/34 означає повноту **поточного required evidence scope**, а не доказ усіх
  можливих програм чи всіх майбутніх semantic extensions;
- `complete-self-hosting` не проголошується автоматично: силу такого claim-а
  окремо визначає claim vocabulary у machine evidence matrix.

Не повертати later-binding через dynamic-scope shortcut: чинний proof лишається
lexical і finite-data.

## A3. Advice Taker reasoning stability — B0/B1

Підтверджено 2026-09-07:

- ✅ `prove-goal` rule scan — tail-recursive accumulator + один `reverse`;
- ✅ 256-rule full scan проходить на ordinary test stack;
- ✅ result order не змінився;
- ✅ refreshed scale harness виконує N=100/500/1000 на ordinary stack;
- ✅ 5000/10000 лишені як explicit ignored/manual falsification profile;
- ✅ canonical data-only outcome algebra:

```lisp
(proved statement results)
(unknown subject)
(partial value bound)
(blocked reason)
(disputed evidence)
(invalid reason payload)
```

- ✅ `proved` зберігає всі alternatives;
- ✅ opposite proof ≠ absence of proof;
- ✅ both sides → `disputed`;
- ✅ malformed goal/module → `invalid`;
- ✅ legacy `reason` / `reason-in` backward-compatible;
- ✅ opt-in `reason-observe` / `reason-in-observe`.

Evidence: `reason_stack.rs`, `reason_scale.rs`, `result_status.rs`,
`reason_outcome_invalid.rs`, `reason_in_outcome_invalid.rs`, CI #1034.

## A4. Explanation + adversarial Advice Taker loop — B2/B3

- ✅ `narrate-outcome` зберігає distinction між `unknown`, `partial`, `blocked`,
  `disputed`, `invalid`;
- ✅ malformed/truncated tagged outcomes відхиляються як invalid presentation;
- ✅ `proved` presentation зберігає proof/provenance;
- ✅ 7-case end-to-end corpus: direct, multi-step, recursion, unknown, conflict,
  malformed advice, knowledge-package round-trip.

Evidence: `narrate_outcomes.rs`, `advice_corpus.rs`, CI #1020/#1030.

## A5. Portability / Guard / documentation hardening

- ✅ committed `core4.lisp.fasl` перевіряється exact source hash;
- ✅ semantic changes trigger WASM browser workflow;
- ✅ Chrome + Firefox пройшли після trigger expansion;
- ✅ Guard Rust boundary перевіряє exact `guard/1` structure, не rendered substring;
- ✅ nested `(decision allow)` spoof відхиляється;
- ✅ reasoning/narration sections у `FUNCTIONS.md` оновлені;
- ✅ documentation regression рахує live `(def ...)` імена для цих двох модулів.

## A6. Scoped host capabilities — embedding mechanism

Підтверджено CI #1038:

```text
process allowlist
filesystem read roots
filesystem write roots
tcp connect host/port ranges
tcp listen address/port ranges
```

- ✅ policy per-session і shared across lexical children;
- ✅ `None` = trusted unrestricted default, backward compatibility preserved;
- ✅ filesystem canonicalization/enforcement належить `my-lisp-host`, не core;
- ✅ `read-file`, byte read, `read-dir`, `load` obey read roots;
- ✅ writes obey separate write roots;
- ✅ symlink escape regression denied;
- ✅ connect/listen independently gated before OS operation.

Не заявляється повний sandbox. Public CLI flags ще не є ратифікованим contract;
див. `docs/host-capability-scoping-adr-2026-08-27.md`.

## A7. Lisp-owned external translation admission — B4 first milestone

Зовнішній translator більше не потребує й не отримує semantic authority.
Versioned protocol живе в `lib/translation.lisp`:

```lisp
(translation/1 candidate|ambiguous|rejected clause|batch|query source payload)
```

Підтверджена межа:

- ✅ `translation-review` структурно перевіряє protocol shell у Lisp;
- ✅ candidate clause/batch повторно проходить чинні knowledge validators і
  `advice-decision` / `advice-all-decision`;
- ✅ candidate query проходить `knowledge-goal-valid?`;
- ✅ review є pure щодо `*knowledge-journal*` — навіть `accepted` нічого не пише;
- ✅ лише accepted clause/batch відкриває `translation-admission-payload`;
- ✅ actual knowledge write лишається явним `advise` / `advise-all`;
- ✅ existing explicit opposite перемагає зовнішню candidate-пропозицію;
- ✅ ambiguous/rejected review може зберігатися як evidence, не knowledge;
- ✅ ambiguity вимагає щонайменше двох валідних alternatives;
- ✅ versioned data-only corpus покриває accepted/rejected/ambiguous та
  downstream `proved`/`unknown`/`not-run` modes.

Evidence: `translation_boundary.rs`, `translation-corpus-v1.lisp`; substantive
B4 tests/build/clippy пройшли в repair sequence #1050/#1051, final current-head
CI лишається authority перед сильнішим claim.

---

# B. Головний активний фронт — Advice Taker

## B4. Natural-language / external translator bridge — **BOUNDARY ESTABLISHED**

Перший milestone виконаний: існують versioned candidate data, Lisp-owned
validation/review, accepted/rejected/ambiguous distinction та evidence path.
Зовнішній provider/LLM adapter, якщо його додавати, повинен лише породжувати
`translation/1` data і не отримує API прямого запису knowledge state.

Нормативний pipeline:

```text
external translator
        ↓
(translation/1 ...) data
        ↓
translation-review          ← Lisp semantic authority
        ↓
accepted knowledge candidate?
        ├── no  → evidence only
        └── yes → explicit advise / advise-all
                         ↓
                  reason-in-observe
                         ↓
                  canonical outcome
                         ↓
                   narrate-outcome
```

Наступний B4 крок потрібен лише разом із конкретним зовнішнім translator:
adapter має пройти той самий versioned corpus і не мати bypass до knowledge
journal. Не будувати provider-specific semantic layer наперед.

## B5. Reasoning performance — **IMMUTABLE INDEX REUSE CONFIRMED**

Stack-safety і N=100/500/1000 ordinary-stack completion підтверджені.
Predicate/head indexing є finite Lisp data з exact linear fallback для
небезпечних/неіндексованих форм і має прямий same-corpus A/B proof.

CI #1151 diagnostic profile, debug build, 3-sample median:

```text
clauses   indexed reason   forced-linear   linear/indexed
103       ~0.129 s         ~0.368 s        2.85x
503       ~0.585 s         ~1.769 s        3.03x
1003      ~1.148 s         ~3.551 s        3.09x
```

Repeated-query public-path profile на одному незмінному 503-clause module:

```text
6 distinct goals
public reason-in-observe batch         ~3.823 s
prepared reason-observe + one index    ~1.092 s
public/prepared                         3.50x
6 repeated module projections          ~0.443 s
6 repeated index builds                ~2.332 s
```

Ці wall-clock числа — evidence конкретного CI run, не performance contract.
Стабільні claims вужчі:

- ✅ indexed і forced-linear paths виконують той самий realistic mixed-predicate corpus;
- ✅ `reason_index.rs` доводить exact proof/result parity, source rule order,
  recursion/negation parity і safe fallback;
- ✅ на виміряному corpus indexing дає приблизно 3x виграш;
- ✅ recursive proof goals reuse один finite index;
- ✅ `reason-observe` reuse-ить один index для goal та explicit opposite;
- ✅ repeated-query corpus має 6 різних goals і exact public-path outcome/proof
  parity перед будь-яким timing;
- ✅ repeated work домінується `reason-make-index`, а не knowledge projection;
- ✅ public `reason` приймає або historical rules list, або готовий
  `reason-index/1` без зміни результату;
- ✅ public `reason-observe` так само приймає rules або готовий index snapshot;
- ✅ готовий index є явним immutable snapshot: пізніше додані rules не
  з'являються в старому snapshot, але видимі після explicit rebuild;
- ✅ немає global mutable cache, прихованої invalidation або нового runtime
  representation;
- ✅ caller сам вирішує, коли reuse-ити snapshot і коли побудувати новий.

Таким чином measured B5 bottleneck закритий найвужчим механізмом, який уже був
виражений у мові. Не проектувати cache/invalidation layer поверх цього без нового
реального workload, який доведе, що explicit immutable index reuse недостатній.
Manual 5k/10k profile лишається falsification gate перед наступною
indexing/representation зміною, а не автоматичним active milestone.

Evidence: `reason_index.rs`, `reason_advice_scale.rs`, `result_status.rs`,
CI #1151 + WASM #88; commits `0493beb`, `70269c3`, `c5605f7`, `9f1b6f1`,
`84d882b`.

---

# C. Підтримувальний фронт — ядро, embedding, self-hosting

## C1. Не продовжувати механічний каталог evaluator errors

Після `UnknownSymbol` / `Type` / `Arity` / `InvalidForm` наступний class беремо
лише якщо він потрібен Advice Taker, знаходить реальну native/meta divergence
або є conformance requirement.

## C2. Meta-evaluator claim discipline

Arbitrary later-binding visibility більше не є відкритим gap: shared definition
frame підтверджений paired evidence без dynamic scope і без cyclic mutable host
environment.

Наступну self-hosting роботу відкривати лише якщо вона:

- знаходить нову executable native/meta divergence поза чинними 34 required rows;
- потрібна Advice Taker або новому ратифікованому semantic extension;
- або формально змінює scope/силу self-hosting claim-а окремим рішенням.

Не розширювати matrix лише заради більшого числа тестів.

## C3. Shrink Rust, grow Lisp

Переносимо semantic policy з Rust лише коли це зменшує duplicate authority,
має parity/conformance evidence і реально допомагає reasoning/portability.
Це не line-count contest.

## C4. Host capability scoping — user-facing migration remainder

Programmatic embedding enforcement уже confirmed. Залишилися окремі operational
рішення, які не маскуємо під невиправлений primitive:

- чи потрібні native CLI flags `--allow-fs-read`, `--allow-fs-write`,
  `--allow-tcp-connect`, `--allow-tcp-listen`;
- чи вони обмежують local session, TCP/oracle sessions або обидва;
- exact CLI syntax для IPv6/port ranges;
- чи unauthenticated TCP/oracle має перейти до stricter default policy.

До рішення trusted local CLI залишається backward-compatible unrestricted.

## C5. Swarm two-plane migration

Нормативний напрям:

```text
:9999 my-lisp semantic oracle
          ≠
:910x swarm-node coordination plane
```

Підтверджено:

- ✅ `docs/swarm-mesh-v2.md` має operational onboarding evidence;
- ✅ machine-readable deprecation: `knowledge/swarm-legacy-deprecation.lisp`;
- ✅ replacement mapping + two-plane migration regression;
- ✅ `AGENTS.md` більше не навчає legacy `:9999` coordination як first-class path.

Залишок перед фізичним видаленням legacy coordination code:

1. довести відсутність живих callers legacy ops (`no-live-callers`);
2. лише тоді видалити broker/claims/presence/task coordination з `:9999`;
3. regression має довести, що `eval` / `parse` / `diagnose` semantic oracle не
   змінилися.

---

# D. Екосистема й FPGA

Пріоритет вертикалі:

1. source semantics + Advice Taker correctness;
2. portable conformance observations;
3. CML/FPGA execution реально корисного subset;
4. hardware surface тільки після доказу потреби.

Найцінніший hardware proof — поступове виконання
`core.lisp → unify.lisp → reason.lisp` на незалежному backend.

---

# E. Clean Code

`CLEAN_CODE_PLAN.md` виконуємо між semantic milestones або коли quality debt
блокує B4/B5. Clean Code не створює нову semantic authority «про запас».

---

# Поточний порядок робіт

```text
1. B4 external-provider adapter лише разом із конкретним translator і corpus proof
2. swarm — no-live-callers proof, потім physical legacy removal
3. CLI host-scope surface лише після explicit operational decision
4. later-binding / deeper self-hosting proof, якщо Advice Taker його потребує
5. CML/FPGA subset за реальною цінністю для reasoning
6. B5 performance — повертатися лише при новому measured workload/bottleneck
```

## Стоп-умови

Не рухаємося до наступного semantic milestone, якщо:

- CI червоний;
- новий claim не має executable evidence;
- failure mode прихований human-readable string замість stable data;
- `unknown` використовується як synonym для false / invalid / blocked / disputed;
- новий primitive пропонується до перевірки, чи це можна виразити бібліотекою;
- зовнішній translator може обійти `translation-review` / `advise` і прямо писати knowledge;
- security mechanism декларується без adversarial bypass test;
- робота розширює систему до спроби зруйнувати поточну.

---

# Епістемічний статус

- **confirmed** — claim має актуальний executable proof;
- **partial** — механізм працює, але coverage/operational contract неповний;
- **broken** — експеримент спростував claim;
- **unknown** — ще немає достатнього експерименту.

Ні кількість тестів, ні красивий architecture diagram самі по собі не доводять
повноту. Назва явища не може бути сильнішою за найсильніший експеримент, який
його підтримує.