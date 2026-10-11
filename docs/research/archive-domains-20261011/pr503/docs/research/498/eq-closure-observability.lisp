; #498 bounded closure-identity observability without EQ
; Research-only. NOT semantic authority. NO production change.

(eq-closure-observability/2
  (issue 498)
  (parent 471)
  (grandparent 419)
  (role research-only)

  (witness-pair
    (left (lambda (x) x))
    (right (lambda (x) x))
    (allocation separately-created))

  (target-observed
    (reused-closure (identity-relation same))
    (fresh-left-vs-fresh-right (identity-relation distinct)))

  (lower-basis
    (allowed
      atom
      application
      quote
      eval
      write-to-string
      cons
      car
      cdr
      cond
      lambda/application)
    (forbidden
      eq
      eq-peer-surfaces
      semantic-registry-roundtrip
      host-Value-equality
      Rc::ptr_eq
      pointer-or-address-observation
      debug-identity))

  (authored-context-corpus
    (atom-classification
      (left (structural-kind atom))
      (right (structural-kind atom)))
    (application-radio
      (left radio)
      (right radio))
    (application-empty
      (left ())
      (right ()))
    (application-number
      (left 42)
      (right 42))
    (application-dotted-pair
      (left (radio . antenna))
      (right (radio . antenna)))
    (eval-pass-through-application
      (left radio)
      (right radio))
    (serialization
      (left "<lambda>")
      (right "<lambda>"))
    (cons-car-serialization
      (left "<lambda>")
      (right "<lambda>"))
    (cons-cdr
      (left tail-marker)
      (right tail-marker))
    (static-cond-lambda-datum
      (left no-static-match)
      (right no-static-match))
    (car-domain-error
      (left Type)
      (right Type)))

  (invalid-observer-run
    (verification-pr 499)
    (actions-run 35286512078)
    (verification-head "4f847743bc7d40b94d435a99513a742253de2bc0")
    (status invalid-observer)
    (reason
      "Temporary Rust expected strings containing serialized closures were malformed and the test did not compile; this run carries no semantic evidence."))

  (fresh-run
    (verification-pr 499)
    (actions-run 35286593748)
    (verification-head "72b90848dc4484a4eca97d2067435387e373ef06")
    (runner ubuntu-24.04)
    (observer temporary-integration-test-removed-before-diff-check)
    (tests 5)
    (passed 5)
    (failed 0)
    (mechanical-lower-source-guard "reject direct (eq ...)")
    (diff-check pass))

  (classification
    (result bounded-indistinguishability-witness)
    (basis authored-context-corpus))

  (classification-reason
    "Current EQ distinguishes one reused closure from two separately allocated but source-identical closures. Every authored lower context executed without direct EQ produced the same value or named error category for the fresh pair. The corpus covers structural classification, finite applications, eval pass-through, serialization, pair transport/projection, static COND, and CAR domain failure. This exhibits identity information not observed by this bounded basis.")

  (bounded-consequence
    "The tested lower contexts do not exhibit the closure-allocation identity observed by EQ. This strengthens basis-relative negative evidence around EQ but is not an exhaustive contextual-equivalence result.")

  (non-claims
    no-global-contextual-equivalence
    no-global-eq-irreducibility
    no-exhaustive-context-search
    untested-contexts-may-distinguish
    no-production-change-authorized))
