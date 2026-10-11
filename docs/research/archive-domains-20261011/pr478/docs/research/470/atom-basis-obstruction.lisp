; #470 ATOM lower-basis falsification
; Research-only. NOT semantic authority. NO production change.
;
; Current authority stays in:
; - contracts/structural-observation-contract.lisp
; - contracts/answer-contract.lisp
; - tests/fixtures/structural-observation-v1.lisp
;
; This record exists only to make one derivation route falsifiable and to
; preserve the exact observed result after execution.

(atom-basis-obstruction/2
  (issue 470)
  (parent 419)
  (related 218 305)
  (role research-only)

  (target
    (identity "0002")
    (surface atom)
    (input-domain value)
    (result-domain structural-kind)
    (required-results
      (structural-kind empty-list)
      (structural-kind pair)
      (structural-kind atom))
    (total-over-current-value-domain t))

  (basis B470
    (admitted
      canon-zero
      quote
      eq
      cons
      car
      cdr
      cond
      lambda/application
      define)
    (excluded
      atom
      atom-peer-surfaces
      semantic-registry-roundtrip
      host-shape-tags
      Value::is_atom
      pair?
      shape-oracle
      error-catch
      error-recovery))

  (current-error-control-boundary
    (language-level-try/catch absent)
    (registry-surfaces catch absent)
    (registry-surfaces try absent)
    (registry-surfaces recover absent)
    (registry-surfaces handler absent))

  (candidate-route E-eq-zero
    (idea "Use EQ against Canon 0 to distinguish empty-list from an ordinary non-pair atom.")
    (predictions
      (empty-list (identity-relation same))
      (ordinary-atom (identity-relation distinct))
      (pair Type))
    (observed
      (empty-list (identity-relation same))
      (ordinary-atom (identity-relation distinct))
      (pair Type))
    (risk "EQ is atom-domain only; a pair reaches named Type before COND can branch."))

  (candidate-route P-projection-success
    (idea "Apply CAR, discard its coordinate, and return structural-kind pair on successful projection.")
    (shape
      ((lambda (x)
         ((lambda (ignored)
            (quote (structural-kind pair)))
          (car x)))
       INPUT))
    (predictions
      (pair (structural-kind pair))
      (ordinary-atom Type)
      (empty-list Type))
    (observed
      (pair (structural-kind pair))
      (ordinary-atom Type)
      (empty-list Type))
    (risk "CAR is pair-domain only; non-pairs fail before any fallback can run."))

  (composition-prediction
    (statement
      "With no admitted error recovery, E and P have complementary partial domains. E-first aborts on pair; P-first aborts on empty-list and ordinary atom. Neither ordering is predicted to produce a total three-way structural-kind result over ATOM's current domain."))

  (fresh-run
    (verification-pr 477)
    (actions-run 35284365924)
    (verification-head "552ed964711cca0d8a11c56f0ea454b70ac022c9")
    (runner ubuntu-24.04)
    (observer temporary-integration-test-removed-before-diff-check)
    (tests 5)
    (passed 5)
    (failed 0)
    (target-total-three-classes pass)
    (eq-zero-domain-boundary pass)
    (projection-success-domain-boundary pass)
    (eq-first-pair-abort pass)
    (projection-first-nonpair-abort pass)
    (diff-check pass))

  (classification
    (route eq-zero+projection-success)
    (result route-falsified-as-total-classifier)
    (reason
      "The two available structural observations have complementary partial domains, and current my-lisp admits no language-level error recovery that could turn their named domain failures into branchable data. EQ-first therefore aborts on pair; projection-first aborts on the two non-pair classes."))

  (bounded-consequence
    "Within B470, the executed decomposition does not reproduce ATOM's total three-way structural-kind observation. This is basis-relative negative evidence, not an absolute irreducibility theorem.")

  (surviving-hypotheses
    (weaker-total-pair-or-shape-observer
      "Still open only if independently admitted with strictly weaker laws than ATOM.")
    (generic-shape-case-eliminator
      "Must be classified as basis exchange unless its observable laws are strictly weaker than the three-way classifier.")
    (future-error-as-data
      "Would change the lower basis and requires a new experiment; it cannot be assumed retroactively."))

  (non-claims
    no-global-irreducibility-proof
    no-proof-against-future-weaker-total-shape-observer
    no-proof-against-future-error-as-data-basis
    no-canon-change-authorized
    no-rust-change-authorized))
