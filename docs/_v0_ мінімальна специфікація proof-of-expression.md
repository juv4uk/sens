# `lib/epistemic.lisp` v0: мінімальна специфікація proof-of-expression

**Статус:** пропозиція для library-first experiment  
**Не є:** зміною Rust evaluator, новим primitive, scheduler-ом, effect system або новим World contract.  
**Мета:** перевірити, чи current `my-lisp` здатний виразити епістемічні data shapes, explicit intent і evidence relations як звичайні S-expressions.

## Рішення, яке уточнює початкову пропозицію

Уточнення про `artifact-digest` правильне: **digest не має бути обов’язковим полем evidence**. Не кожне доказове відношення посилається на файл або content-addressed artifact. Proof tree, named test, structured observation і digest — різні види джерела.

Тому v0 має не `artifact-digest`, а обов’язковий **`source-ref`**, який є tagged data. Це зберігає provenance boundary, не перетворюючи digest на фальшиву універсальну абстракцію.

> **Evidence без source reference — це лише твердження про evidence. Evidence із tagged `source-ref` уже можна перевірити, відобразити й посилити в наступних версіях.**

## 1. Межа v0

`epistemic.lisp` визначає лише конструктори, predicates, accessors та small validators. Він не виконує intent, не викликає network/process, не записує в World, не приймає claim як fact і не змінює existing `reason`/`forward` return values.

```text
ordinary my-lisp values
       ↓
epistemic constructors/validators
       ↓
candidate data
       ↓
existing review / advise-all-world ingress
       ↓
knowledge World only if separately admitted
```

## 2. Мінімальні canonical data shapes

### Observation

```lisp
(observation
  (source <source-ref>)
  (statement <datum>))
```

Observation фіксує, що declared source подало datum. Він не стверджує істинність datum.

### Claim

```lisp
(claim
  (statement <datum>)
  (source <source-ref>)
  (review <proposed|reviewed|rejected>))
```

Claim є об’єктом review, а не result status. `reviewed` означає, що хтось переглянув claim за зовнішньою policy; це не еквівалент `proved`.

### Evidence

```lisp
(evidence
  (claim-ref <claim-ref>)
  (method <symbol>)
  (outcome <supports|contradicts|inconclusive>)
  (source-ref <source-ref>))
```

`method` залишається простим symbolic name у v0, наприклад `reasoning-proof`, `live-test`, `document-review` або `human-observation`. V0 only checks that it is a symbol; registry methods і їхня semantics — майбутня, окрема задача.

### Intent

```lisp
(intent
  (goal <datum>)
  (requires <proper-list-of-capability-symbols>)
  (stop-on <datum>)
  (produces <datum>))
```

Intent — declarative datum. It is neither plan nor command. У v0 `requires` — саме proper list capability symbols, наприклад `(process:cargo tcp-client)`, а не довільні tagged requirements. `intent-capabilities-satisfied?` can only compare it to an explicit **effective capability snapshot** supplied from outside; it cannot grant authority.

## 3. `source-ref`: чотири v0 variants

```lisp
(digest <canonical-content-address>)
(proof <proof-reference>)
(test <test-reference>)
(observation <observation-reference>)
```

| Variant | Що означає | Приклад | Canonical-safe за умови |
|---|---|---|---|
| `digest` | Evidence спирається на fixed content artifact. | `(digest "sha256:...")` або `(digest <world-content-address>)` | Address/digest стабільний і не містить runtime path. |
| `proof` | Evidence спирається на reasoning proof або його deterministic reference. | `(proof (goal (ancestor alice dana)) (world <address>))` | Proof source/goal описані структурно. |
| `test` | Evidence спирається на named reproducible test assertion. | `(test (fixture conformance.lisp) (case exact-rational-division))` | Fixture/case name та expected semantic claim стабільні. |
| `observation` | Evidence посилається на конкретну attributed observation. | `(observation host-capabilities-v1)` | Reference має локальну або package-level identity. |

У v0 validator має бути **структурно суворим, семантично слабким**: tag мусить бути одним із чотирьох, payload — nonempty proper data shape. Сильніша перевірка кожного variant — наприклад, чи digest криптографічно валідний, чи proof належить певному World, чи test реально існує — має з’явитися тільки з real consumer.

## 4. Claim reference у v0

`claim-ref` не повинен одразу вимагати глобального identity system. Для локального experiment достатньо explicit symbolic reference:

```lisp
(claim-ref cml-build-available)
```

або structural reference, якщо claim живе всередині одного enclosing package:

```lisp
(claim-ref
  (claim
    (statement (build cml succeeds))
    (source (observation local-run))
    (review proposed)))
```

Надалі можна ввести canonical claim address через `write-to-string` або package identity. Не роби цього requirement v0: інакше experiment непомітно перетвориться на identity subsystem.

## 5. Semantic evidence та operational receipt

Цей поділ лишається обов’язковим.

| Рівень | Приклад полів | Може бути частиною canonical data package/World? |
|---|---|---|
| **Semantic evidence** | `claim-ref`, `method`, `outcome`, structural `source-ref`. | Так, після review/validation. |
| **Operational receipt** | timestamp, provider request ID, local path, retry count, cost, agent session ID. | Ні; це audit record. |

Наприклад, Sarvam transcription receipt може мати exact request ID і local file path. Але semantic evidence має посилатися лише на reviewed transcript/observation або stable digest, а не на transient provider session.

## 6. Мінімальний API

```lisp
;; Constructors
(make-observation source statement)
(make-claim statement source review)
(make-evidence claim-ref method outcome source-ref)
(make-intent goal requirements stop-condition produces)

;; Shape predicates
(observation? value)
(claim? value)
(evidence? value)
(intent? value)
(source-ref? value)

;; Projections
(claim-statement claim)
(claim-review claim)
(evidence-outcome evidence)
(evidence-source-ref evidence)
(intent-goal intent)

;; Narrow relations
(evidence-supports? evidence claim-ref)
(intent-capabilities-satisfied? intent effective-capabilities)
```

`intent-capabilities-satisfied?` у v0 не мусить розуміти всі future capability formats. Він відповідає **лише** на питання membership: чи кожна declared requirement присутня в explicit snapshot. Він не означає authorization, plan validity, input/revision validity, evidence sufficiency або guaranteed execution. Достатньо support формату:

```lisp
(effective-capabilities process:git process:cargo tcp-client)
```

### Malformed shapes у v0

V0 не заводить нового `epistemic-error` або незалежної системи rejected results. Predicates і boolean validators повертають `t` або `()`, тож malformed shape просто не проходить `observation?`, `claim?`, `evidence?`, `intent?` або `source-ref?`. Там, де caller already works у чинному knowledge/World boundary й потребує пояснення, він може перевикористати наявний tagged vocabulary на кшталт `(rejected (reason invalid-... ) (input ...))`; сам `epistemic.lisp` не мусить винаходити другу envelope convention.

і exact membership checks against `(requires ...)`. Snapshot is input, not a primitive-derived source of power.

## 7. Five fixtures and expected outcomes

| Fixture | Minimum expression | Expected result |
|---|---|---|
| CML build () | Intent requires `process:cargo`; snapshot lacks it. | `intent-capabilities-satisfied?` повертає `()`; caller, за потреби, може побудувати `(blocked missing-capability)` через existing `result-status.lisp`. |
| Sarvam transcript | Observation references selected audio/transcript; claim is `proposed`. | No direct World ingestion; receipt remains external. |
| Host observation | Host capability snapshot is stored as `observation`, separate from agent declaration. | `declares` and `effective` cannot be conflated. |
| Reasoning proof | Evidence uses `(proof ...)`, not an invented digest. | Existing `reason-explain`/provenance remains source engine. |
| Knowledge import | Reviewed data converts to existing valid knowledge package and uses guarded World import. | Rejected/conflict returns old World; received data is never evaluated. |

## 8. V0 success and failure criteria

The experiment succeeds if all shapes are expressible, predicates return `()` for malformed forms, and five fixtures pass without changing core. Additionally, every canonical v0 value must satisfy:

```text
read(write-to-string(value)) = value
```

The experiment fails productively if a fixture cannot be expressed. The failure report must have exactly this form:

```text
exact missing capability:
<one concrete operation>

minimal witness:
<smallest my-lisp program/data shape that requires it>

why existing primitives cannot express it:
<argument against current kernel/library surface>

candidate minimal extension:
<one narrowly scoped proposal, not a feature family>
```

This is the critical discipline: **a missing convenience is not a missing semantic capability.**

## 9. Explicit non-goals

V0 deliberately does not introduce a scheduler, task executor, new effect system, global claim registry, cryptographic hash primitive, auto-import agent outputs, universal provenance ontology, purity checker, macro-level pattern matching or a World merge policy.

Those may become legitimate later. None is necessary to answer the first question: *can `my-lisp` already express an honest epistemic/intention layer as data?*

## Final direction

The provided refinement makes the original plan better. The right next instruction is now precise:

> **Не чіпай kernel. Реалізуй `lib/epistemic.lisp` як opt-in data layer. Evidence має required tagged `source-ref`, але не required digest. `intent-capabilities-satisfied?` перевіряє тільки capability membership. Проганяй п’ять real fixtures. Primitive пропонуй лише через exact missing capability + minimal witness.**

This is small enough to be an experiment, strong enough to test the paradigm, and aligned with the existing `my-lisp` distinction between core semantics and Tier-3 ecosystem capabilities.
