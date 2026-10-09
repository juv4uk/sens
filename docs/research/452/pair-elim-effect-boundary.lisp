; #452 pair-elim effect/evaluation-order boundary
; Research-only. NOT semantic authority. NO production change.
;
; Parent result #451 is intentionally preserved:
; pure extensional selector model => basis-exchange-only.
;
; This slice asks whether effectful selector *expressions* distinguish an
; ordinary callable eliminator from a stronger delayed-selector special form.

(pair-elim-effect-boundary
  (schema-version 4)
  (issue 452)
  (role research-only)

  (current-evaluator-order
    (operator-before-ordinary-arguments t)
    (ordinary-arguments left-to-right)
    (first-failure-stops-later-arguments t)
    (source docs/adr/ADR-010-EVALUATOR-OUTCOME-PROVENANCE.md))

  (two-candidate-interpretations
    (ordinary-callable
      (surface-shape (pair-elim pair selector-expression))
      (evaluation "pair argument and selector-expression are evaluated left-to-right before pair-elim body runs")
      (consequence "selector-expression effects can occur even when the pair value later fails admission"))
    (delayed-selector-form
      (surface-shape (pair-elim pair selector-source))
      (evaluation "pair is admitted before selector source is evaluated")
      (consequence "requires non-eager evaluation-control power beyond ordinary function application")))

  (exact-reverse-derivation
    (shape
      (lambda (p selector)
        (selector (car p) (cdr p))))
    (outer-application-order pair-expression selector-expression)
    (body-order car-projection cdr-projection selector-body)
    (nonpair-boundary
      "both outer arguments are already evaluated before the closure body reaches CAR failure"))

  (preliminary-effect-run
    (verification-pr 453)
    (actions-run 35282403011)
    (verification-head "d1f3b0ade20fb8d6deadcc0202425f5a79296af8")
    (merge-test-sha "ac46c0744d4b7ed744f526891d8fd1bca2dd847b")
    (runner ubuntu-24.04)
    (observer temporary-integration-test-removed-before-diff-check)
    (observer-tests 3)
    (observer-passed 3)
    (observer-failed 0)
    (ordinary-callable selector-expression-effect-before-body-domain-failure)
    (direct-selector-route selector-expression-effect-before-car-failure)
    (valid-direct-route selector-body-effect-exactly-once)
    (status supporting-not-final-shape)
    (diff-check pass))

  (observer-correction
    (first-run 35282247688)
    (status invalid-observer)
    (reason "CLI error path did not expose the Session output buffer, so absence of printed marker in process output was not semantic evidence")
    (correction "temporary Rust integration observer read Session.environment.output_snapshot() after eval_program returned Err; no production Rust was committed"))

  (exact-reverse-run
    (verification-pr 460)
    (actions-run 35283084878)
    (verification-head "0b5602e4d5ffc6b61591ce19edc553d66e249f55")
    (runner ubuntu-24.04)
    (observer temporary-integration-test-removed-before-diff-check)
    (observer-tests 3)
    (observer-passed 3)
    (observer-failed 0)
    (valid-pair
      (effect-order pair-expression-effect selector-expression-effect selector-body-effect)
      (result fresh-left))
    (nonpair
      (effect-order pair-expression-effect selector-expression-effect)
      (selector-body-effect suppressed)
      (failure car-type-error))
    (selector-body-failure
      (effect-order pair-expression-effect selector-expression-effect selector-body-effect)
      (failure selector-body-type-error))
    (diff-check pass))

  (language-visible-resource-boundary
    (mechanism Environment::with_cons_limit)
    (observable-failure OutOfMemory)
    (scope "counts semantic CONS allocation only; does not expose generic host/Rc/environment allocation"))

  (cons-budget-run
    (verification-pr 462)
    (actions-run 35283288785)
    (verification-head "dffb0f0bc44a6cbead94cb4676e5236f7f7f0cc8")
    (runner ubuntu-24.04)
    (observer temporary-integration-test-removed-before-diff-check)
    (observer-tests 3)
    (observer-passed 3)
    (observer-failed 0)
    (zero-cons-budget-valid-pair
      (result fresh-left)
      (outcome no-OutOfMemory))
    (zero-cons-budget-nonpair
      (failure type-error)
      (outcome no-OutOfMemory))
    (zero-cons-budget-selector-cons
      (failure OutOfMemory))
    (diff-check pass))

  (classification
    (ordinary-callable pure-basis-exchange-extends-to-selector-expression-effects)
    (delayed-selector-form callback-candidate-observably-stronger)
    (language-visible-cons-budget reverse-derivation-requires-zero-cons-allocations))

  (classification-reason
    "The exact reverse derivation evaluates pair-expression, then selector-expression, then enters the closure body; on an admitted pair the selector body runs after CAR/CDR projection, while on a non-pair CAR fails only after both outer effects have already occurred. That is the same eager outer-argument envelope required of an ordinary callable pair-elim. A candidate that instead suppresses selector-expression evaluation until after pair admission differs observably and therefore carries additional non-eager evaluation-control power. Under the existing opt-in CONS resource guard, the reverse derivation itself succeeds with zero CONS budget; only an explicit CONS in the selector body consumes that budget.")

  (candidate-constraint
    "Any future ordinary pair-elim candidate that consumes language-visible CONS budget merely to perform pair elimination would differ from the current reverse derivation under Environment::with_cons_limit(0).")

  (non-claims
    all-effect-kinds-not-exhausted
    generic-host-allocation-not-language-observable-here
    asynchronous-or-external-host-effects-not-measured
    candidate-abi-not-proposed
    canon-change-not-authorized)

  (next-falsification
    "Do not invent stronger resource observables. Further equivalence work needs either a concrete candidate implementation or an already-ratified language-visible resource/effect mechanism; until then generic host allocation differences remain mechanism, not semantic evidence.")

  (claim-boundary
    "Suppressing evaluation of the selector expression on non-pair input is not a free implementation detail, and consuming observable CONS budget merely to eliminate a pair is not free either; both would differ from the executed reverse derivation."))
