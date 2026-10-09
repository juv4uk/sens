; #419 PRE-1.0 Canon sculpture audit — integrated research snapshot
; Base main: 04084f1003ebd78c946a4b135b8a9febfc7e040e
; Research data only. This file is NOT semantic authority and does not change language behavior.

(canon-sculpt-audit
  (schema-version 4)
  (base-main 04084f1003ebd78c946a4b135b8a9febfc7e040e)
  (freeze-status pre-1.0-unfrozen)
  (role research-only)
  (principle "minimum independent semantic concepts, not minimum lines of code")

  (classification-vocabulary
    (ground-value
     syntax-rule-candidate
     irreducible-candidate
     derivable-candidate
     value-domain
     insufficient-evidence))

  (current-observations
    (canon-runtime-kinds
      (CANON_EMPTY_LIST ground-value)
      (PRIM_QUOTE special-form)
      (PRIM_ATOM value-primitive)
      (PRIM_EQ value-primitive)
      (PRIM_CONS value-primitive)
      (PRIM_CAR value-primitive)
      (PRIM_CDR value-primitive)
      (PRIM_COND special-form))
    (surface-registry
      (quote 0001)
      (atom 0002)
      (eq 0003)
      (cons 0004)
      (car 0005)
      (cdr 0006)
      (cond 0007)
      (if absent))
    (cond-current-canonical-path
      (source tests/fixtures/control-dispatch-v1.lisp)
      (clause-shape (query expected-result expression))
      (selection exact-value-equality)
      (expected-result quoted-data)
      (evaluation only-selected-consequent)
      (truth-coercion none)
      (empty-list may-be-explicit-match-data)
      (arbitrary-nonempty-data not-implicit-yes)
      (no-match canon-empty-list))
    (cond-migration-path
      (clause-shape (test expression))
      (status compatibility-only)
      (note "temporary truthiness bridge is explicitly not canonical semantics"))
    (library-dependency
      (and derives-through-cond)
      (or derives-through-cond)
      (assoc derives-through-cond)))

  ; Current evaluator inventory: every path that sees source Expr before
  ; ordinary eager argument evaluation. This is a dependency map, not proof
  ; that the list is globally minimal.
  (evaluation-delay-mechanism-inventory
    (quote
      (mechanism canonical-special-form)
      (raw-source-access yes)
      (status candidate-under-test))
    (cond
      (mechanism canonical-special-form)
      (raw-source-access yes)
      (status candidate-under-test))
    (lambda
      (mechanism necessary-form)
      (raw-source-access body-only)
      (ordinary-arguments eager)
      (closure-body-introspection no-language-operation)
      (status not-general-source-to-data-or-runtime-selector))
    (define
      (mechanism necessary-form)
      (rhs evaluated)
      (status not-delay-candidate))
    (macro-application
      (mechanism macro-dispatch)
      (raw-source-access yes)
      (implementation-dependency "apply_macro calls quoted(argument) directly")
      (bootstrap-dependency "lib/macro.lisp itself uses quote and cond")
      (status circular-for-quote-or-cond-reduction-today))
    (eval
      (mechanism value-level-callable)
      (ordinary-argument eager)
      (then data-to-code yes)
      (status stronger-evaluator-not-source-delay))
    (read
      (mechanism value-level-callable)
      (input string)
      (implementation-dependency "reader result converted to data with quoted helper")
      (status representation-conversion-not-source-delay))
    (read-all
      (mechanism value-level-callable)
      (input string)
      (implementation-dependency "parsed expressions converted with quoted helper")
      (status representation-conversion-not-source-delay))
    (host-capability-dispatch
      (mechanism external-host-special-form-registry)
      (raw-source-access yes)
      (core-installed-capabilities zero)
      (status rejected-as-lower-language-semantics))
    (ordinary-callable
      (mechanism eager-application)
      (raw-source-access no)
      (status falsification-target)))

  (candidate
    (identity CANON_EMPTY_LIST)
    (category ground-value)
    (classification ground-value)
    (observable-laws
      (ground-object)
      (proper-list-terminator)
      (unspecialized-no-answer-where-explicitly-contracted))
    (falsification-question
      "Can every required role of Canon 0 be represented without introducing another equally fundamental ground identity?"))

  (candidate
    (identity PRIM_QUOTE)
    (category evaluation-control)
    (classification syntax-rule-candidate)
    (observable-laws
      (return-source-form-without-ordinary-evaluation)
      (syntax-only-not-callable))
    (experiment
      (hypothesis ordinary-eager-function-derivation)
      (fixture docs/research/canon-sculpt-probes/quote-ordinary-function-red.lisp)
      (predicted-result red)
      (meaning "ordinary eager function application cannot explain suppression of argument evaluation"))
    (current-reduction-rejections
      (macro "macro application already receives arguments through the same quoted source-to-data mechanism")
      (read "requires explicit string representation and itself uses quoted conversion")
      (eval "receives an already evaluated datum and is at least evaluator-strength, not source capture")
      (host-capability "external optional host mechanism; capability-free core installs none")
      (lambda "can delay a body but cannot expose that body as data through a language operation"))
    (remaining-question
      "Is source-form capture without evaluation an irreducible concept, or can it be obtained from a strictly smaller mechanism that does not already contain quote-equivalent power?"))

  (candidate
    (identity PRIM_COND)
    (category evaluation-control)
    (classification syntax-rule-candidate)
    (observable-laws
      (ordered-clause-selection)
      (query-evaluated-before-match)
      (expected-result-is-data)
      (evaluate-selected-consequent-only)
      (no-value-to-bool-on-canonical-path))
    (negative-evidence
      (if-semantic-identity absent)
      (ordinary-library-and-or-depend-on-cond)
      (machine-lowering-is-not-semantic-derivation))
    (experiment
      (hypothesis ordinary-eager-function-can-supply-selective-evaluation)
      (fixture docs/research/canon-sculpt-probes/selective-evaluation-ordinary-function-red.lisp)
      (predicted-result red)
      (meaning "ordinary eager application evaluates an ignored branch before entering the function body"))
    (current-reduction-rejections
      (macro "current macro bootstrap and expansion machinery already depend on quote/cond-strength non-evaluation; no smaller runtime selector identified")
      (eval "using the full evaluator as branch machinery is a stronger-hidden-primitive unless eval is independently reduced below cond")
      (host-capability "external optional raw-Expr hook cannot define capability-free core semantics")
      (lambda "thunks can delay branch bodies, but current arbitrary-data query matching still needs a selector to choose which thunk to invoke"))
    (lower-bound-hypothesis
      "Some runtime selective-evaluation power must remain unless a non-eager lower mechanism is exhibited; replacing cond with if/select/branch without reducing that power is renaming, not sculpture."))
    (remaining-question
      "Can canonical three-part cond be derived from a strictly smaller declared selector while preserving arbitrary-value result matching and skipped-branch non-evaluation?"))

  (candidate
    (identity PRIM_ATOM)
    (category structural-observation)
    (classification insufficient-evidence)
    (observable-laws
      ((atom ()) (structural-kind empty-list))
      ((atom pair) (structural-kind pair))
      ((atom non-pair-non-empty) (structural-kind atom)))
    (falsification-question
      "Can structural-kind be derived without atom, an alias/registry round-trip, host representation tags, or a stronger hidden structural classifier?"))

  (candidate
    (identity PRIM_EQ)
    (category identity-observation)
    (classification insufficient-evidence)
    (observable-laws (returns-identity-relation-not-generic-truth))
    (falsification-question
      "Can identity-relation be derived without eq, pointer/host equality, alias round-trip, or a stronger hidden equality primitive?"))

  (candidate
    (identity PRIM_CONS)
    (category structure-construction)
    (classification irreducible-candidate)
    (falsification-question
      "Can pair construction be derived without already possessing pair construction or a stronger aggregate constructor?"))

  (candidate
    (identity PRIM_CAR)
    (category structure-observation)
    (classification insufficient-evidence)
    (falsification-question
      "Can first-component observation be derived without pair destructuring hidden in another operation or substrate load?"))

  (candidate
    (identity PRIM_CDR)
    (category structure-observation)
    (classification insufficient-evidence)
    (falsification-question
      "Can second-component observation be derived without pair destructuring hidden in another operation or substrate load?"))

  (circularity-traps
    direct-self-call
    surface-alias-self-call
    registry-roundtrip-self-call
    host-representation-oracle
    stronger-hidden-primitive
    backend-only-proof)

  (witness-navigation
    (PRIM_QUOTE tests/fixtures/conformance.lisp)
    (PRIM_QUOTE-CROSS-SUBSTRATE docs/cross-substrate-evidence-matrix.md)
    (PRIM_ATOM tests/fixtures/structural-observation-v1.lisp)
    (PRIM_EQ tests/fixtures/structural-observation-v1.lisp)
    (PRIM_CONS tests/fixtures/conformance.lisp)
    (PRIM_CAR tests/fixtures/conformance.lisp)
    (PRIM_CDR tests/fixtures/conformance.lisp)
    (PRIM_COND tests/fixtures/control-dispatch-v1.lisp)
    (PRIM_QUOTE-RED docs/research/canon-sculpt-probes/quote-ordinary-function-red.lisp)
    (SELECTIVE-EVALUATION-RED docs/research/canon-sculpt-probes/selective-evaluation-ordinary-function-red.lisp))

  (backend-discipline
    (law "lowering proves an implementation path, not semantic derivability")
    (native harness-covered)
    (meta fixture-tagged-where-present)
    (cml harness-coverage-not-fresh-run)
    (fpga milestone-equivalent-not-current-hardware-proof)
    (x86-machine partial-mechanism-evidence))

  (coordination
    (merged-neighbor 392)
    (active-neighbors
      421
      422 418 410 406 396
      427
      328
      402 403
      409 424 426 428 429
      317)
    (rule "do not edit their owned production/test routing files from #419"))

  (deletion-gate
    independent-lisp-owned-law-preservation
    explicit-lower-concept-closure
    negative-circularity-proof
    relevant-cross-backend-parity
    owner-review-separate-change
    zero-new-host-semantic-authority)

  (audit-law
    (name no-historical-privilege)
    (statement "Earlier primitive status is evidence to inspect, not proof of irreducibility."))
  (audit-law
    (name no-computational-universality-cheat)
    (statement "A richer library feature that can simulate control does not count as a reduction unless its own semantics are independently lower and non-circular."))
  (audit-law
    (name uncertainty-wins)
    (statement "If derivability or circularity cannot be demonstrated mechanically, retain insufficient-evidence."))
  (audit-law
    (name preserve-before-delete)
    (statement "No semantic identity is removed in this audit branch.")))
