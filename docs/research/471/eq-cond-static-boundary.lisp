; #471 EQ vs canonical three-part COND
; Research-only. NOT semantic authority. NO production change.
;
; Question: can COND's explicit-result equality replace EQ's dynamic
; two-runtime-operand atomic identity relation?

(eq-cond-static-boundary/2
  (issue 471)
  (parent 419)
  (related 218)
  (role research-only)

  (eq-capability
    (operands left-runtime right-runtime)
    (input-domain (atom atom))
    (result-domain identity-relation)
    (results same distinct)
    (pair-outside-domain Type))

  (cond-capability
    (canonical-clause-shape (query expected-source-datum expression))
    (actual query-runtime-evaluated)
    (expected quoted-source-datum)
    (selection-rule actual==quoted-expected)
    (generic-truth-coercion forbidden))

  (hypothesis-under-test
    "Canonical COND may look like a hidden equality oracle, but its right-hand side is syntax/data, not a second runtime operand.")

  (predictions-and-observations
    (static-atom
      (source "(cond ((quote radio) radio (quote selected)) ((quote fallback) fallback (quote missed)))")
      (predicted selected)
      (observed selected))
    (static-pair
      (source "(cond ((quote (radio . antenna)) (radio . antenna) (quote selected)) ((quote fallback) fallback (quote missed)))")
      (predicted selected)
      (observed selected))
    (eq-pair
      (source "(eq (quote (radio . antenna)) (quote (radio . antenna)))")
      (predicted-error Type)
      (observed-error Type))
    (dynamic-same-false-negative
      (source "((lambda (left right) (cond (left right (quote same)) ((quote fallback) fallback (quote distinct)))) (quote radio) (quote radio))")
      (runtime-left radio)
      (runtime-right radio)
      (quoted-expected-datum right)
      (predicted distinct)
      (observed distinct))
    (dynamic-distinct-false-positive
      (source "((lambda (left right) (cond (left right (quote same)) ((quote fallback) fallback (quote distinct)))) (quote right) (quote radio))")
      (runtime-left right)
      (runtime-right radio)
      (quoted-expected-datum right)
      (predicted same)
      (observed same)))

  (fresh-run
    (verification-pr 488)
    (actions-run 35285533876)
    (verification-head "692f5f4bee9d15940e57b9509a63079830d64b58")
    (runner ubuntu-24.04)
    (observer temporary-integration-test-removed-before-diff-check)
    (tests 5)
    (passed 5)
    (failed 0)
    (diff-check pass))

  (classification
    (route COND-static-datum->EQ-dynamic-atom)
    (result route-falsified)
    (relationship capability-incomparable-under-tested-observations))

  (classification-reason
    "Canonical COND has broader static-data comparison reach: it selected a quoted pair datum even though EQ rejects pair operands. But COND's expected form is quoted source data, not a second evaluated runtime operand. Consequently, using a variable name as the expected form produced both a false-negative for equal runtime values and a false-positive for distinct runtime values. EQ therefore cannot be replaced by this COND capability without changing observable power.")

  (bounded-consequence
    "Under the executed route, COND is neither a strict lower implementation of EQ nor a simple superset. It exposes static-datum equality across a broader value shape, while EQ exposes dynamic two-operand identity on the atom domain.")

  (surviving-hypotheses
    (serialization-text-route
      "Still open: compare two runtime atoms through canonical serialization plus independently justified text equality, with collisions and non-serializable atom classes explicitly tested.")
    (other-weaker-dynamic-identity-observer
      "Still open only if it is independently admitted and does not simply rename EQ or host Value equality."))

  (non-claims
    no-global-eq-irreducibility-proof
    no-cond-reclassification
    no-canon-change-authorized
    no-production-change-authorized))
