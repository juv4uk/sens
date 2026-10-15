# Brief для `lib/epistemic.lisp` v0

**Статус:** готовий вузький implementation brief.  
**Commit/push:** не робити без окремого review.

## Завдання

Реалізуй `lib/epistemic.lisp` v0 як **opt-in pure data experiment** поверх поточного `my-lisp`. Його ціль — перевірити, чи мова вже здатна виразити claim/evidence/intent structures без жодної зміни kernel.

## Межі, яких не можна перетинати

Не змінюй Rust evaluator, kernel semantics, README, World contract, existing `reason`/`forward` results, scheduler/effect system, CML або `fpga-lisp`. Не додавай primitive, registry, hash primitive, automatic agent import чи auto-execution.

## Реалізувати

| Категорія | Мінімум |
|---|---|
| Constructors | `make-observation`, `make-claim`, `make-evidence`, `make-intent`. |
| Predicates | `observation?`, `claim?`, `evidence?`, `intent?`, `source-ref?`. |
| Accessors | Claim statement/review, evidence outcome/source-ref, intent goal. |
| Narrow relation | `evidence-supports?`. |
| Capability check | `intent-capabilities-satisfied?`. |
| Validation | Structural validation, malformed-shape rejection, no silent coercion. |

### Required canonical shapes

```lisp
(observation (source <source-ref>) (statement <datum>))

(claim
  (statement <datum>)
  (source <source-ref>)
  (review <proposed|reviewed|rejected>))

(evidence
  (claim-ref <claim-ref>)
  (method <symbol>)
  (outcome <supports|contradicts|inconclusive>)
  (source-ref <source-ref>))

(intent
  (goal <datum>)
  (requires <proper-list-of-capability-symbols>)
  (stop-on <datum>)
  (produces <datum>))
```

### Required `source-ref` variants

```lisp
(digest <nonempty-payload>)
(proof <nonempty-payload>)
(test <nonempty-payload>)
(observation <nonempty-payload>)
```

`source-ref?` must be **structurally strict and semantically weak**. It checks only a recognized tag and a nonempty payload. It must not pretend to know whether a digest is real, a proof belongs to a World, or a test exists.

For v0, `requires` is strictly a proper list of capability symbols such as `(process:cargo tcp-client)`. Do not introduce generic tagged requirements until a real consumer needs them.

### Critical naming rule

```lisp
(intent-capabilities-satisfied? intent effective-capabilities)
```

This function checks only whether each declared requirement appears in the explicit effective capability snapshot. It is **not** authorization, plan validation, evidence validation, input/revision validation, a scheduler decision or a guarantee that intent can execute.

## Malformed-shape convention

Do not create an `epistemic-error` type or a new result protocol. Boolean predicates/validators return `t` for a valid shape and `()` for malformed data. If a caller already belongs to the existing knowledge/World ingestion boundary and needs an explanatory outcome, reuse its established `(rejected (reason invalid-... ) (input ...))` vocabulary rather than creating a second one.

## Five required fixtures

| Fixture | Expected property |
|---|---|
| CML build () | Missing `process:cargo` yields false capability-satisfaction; existing `make-blocked` may describe the result outside this predicate. |
| Sarvam transcript proposal | A machine output is a `proposed` claim/observation with external receipt; it does not enter World automatically. |
| Host observation | Effective host snapshot remains distinct from an agent’s self-declaration. |
| Reasoning proof | `evidence` accepts `(proof ...)` source-ref without forcing a digest. |
| Knowledge import | Only separately reviewed/validated data goes through existing guarded World/data-only import. |

## Tests

Add tests for valid shapes, malformed shapes returning `()`, all four `source-ref` tags, unknown tags returning `()`, missing payloads returning `()`, capability membership and canonical round trips.

Every canonical v0 value must satisfy:

```text
read(write-to-string(value)) = value
```

## Stop condition

If any requirement cannot be expressed with the current language/library surface, stop implementation and report only:

```text
exact missing capability:
...

minimal witness:
...

why existing primitives cannot express it:
...

candidate minimal extension:
...
```

Do not add a feature merely because it would be convenient.

## Completion report

After implementation, report: changed files, added tests, pass/fail status for all five fixtures, round-trip result, and whether any kernel change was needed. Do not commit or push.
