; #447 single pair-eliminator research model
; Research-only data. NOT semantic authority. NO Canon/runtime change.
;
; Question:
;   Does replacing independent CAR/CDR primitives with one product eliminator
;   remove semantic power, or only choose an equivalent basis?
;
; The candidate is intentionally abstract and has no proposed public spelling,
; semantic ID, ABI, implementation, or ratification status.

(pair-elim-research
  (schema-version 2)
  (issue 447)
  (role research-only)
  (production-change none)

  (existing-basis
    (pair-construction cons)
    (pair-elimination (car cdr))
    (function-capability (lambda application)))

  (candidate-basis
    (pair-construction cons)
    (pair-elimination pair-elim)
    (function-capability (lambda application)))

  (candidate-law
    (pair-elim (pair left right) selector)
    (result (selector left right))
    (non-pair named-type-failure)
    (selector-evaluated-only-after-pair-admission t))

  (candidate-to-current
    (car-derived
      (lambda (p)
        (pair-elim p (lambda (left right) left))))
    (cdr-derived
      (lambda (p)
        (pair-elim p (lambda (left right) right)))))

  (current-to-candidate
    (pair-elim-derived
      (lambda (p selector)
        (selector (car p) (cdr p)))))

  (falsification-corpus
    (ordinary-pair (a . b))
    (improper-pair (a . b))
    (proper-list-like (a b c))
    (nested-pair ((a . b) . (c . d)))
    (fresh-left (fresh-left . stable-right))
    (fresh-right (stable-left . fresh-right))
    (non-pair () atom-value string-value number-value))

  (required-observations
    (derived-car equals-current-car-on-admitted-pairs)
    (derived-cdr equals-current-cdr-on-admitted-pairs)
    (derived-car preserves-left-fresh-payload)
    (derived-cdr preserves-right-fresh-payload)
    (candidate-non-pair-failure matches-projector-domain-boundary)
    (reverse-derivation reproduces-candidate-on-tested-selector-corpus))

  (circularity-guards
    (candidate-definition may-not-use car cdr)
    (derived-car may-use pair-elim but-not car cdr peer-surfaces registry-roundtrip host-destructuring backend-load)
    (derived-cdr may-use pair-elim but-not car cdr peer-surfaces registry-roundtrip host-destructuring backend-load)
    (reverse-derivation explicitly-uses-current-projectors-for-equivalence-test-only))

  (fresh-run
    (verification-pr 449)
    (actions-run 35281848959)
    (merge-test-sha "407bd5e8abf97daa9450bcbe738d1ef8804b00e4")
    (candidate-head "026b48d5321df2fcada4c1f4fb9557d276b3e533")
    (runner ubuntu-24.04)
    (live-current-car-nonpair named-type-failure-pass)
    (live-current-cdr-nonpair named-type-failure-pass)
    (candidate-to-current pass)
    (current-to-candidate pass)
    (fresh-payload pass)
    (non-pair-boundary pass)
    (selector-corpus (left right re-pair swap constant nested))
    (diff-check pass))

  (power-accounting
    (before "two primitive projection entry points expose left/right coordinates")
    (after "one eliminator exposes both coordinates to an already-existing two-argument function application")
    (bidirectional-definability observed-on-research-model)
    (expressive-closure observed-bidirectional-on-declared-corpus)
    (primitive-entry-count 2-to-1)
    (semantic-power-removal not-observed))

  (classification basis-exchange-only)
  (classification-reason
    "The candidate derives both projectors, while the existing two projectors plus already-existing function application derive the candidate on the declared corpus. The experiment therefore observes a smaller primitive entry count but no loss of expressive structural-elimination power.")

  (non-claims
    universal-equivalence-for-all-effectful-selector-semantics-not-proven
    backend-cost-equivalence-not-measured
    allocation-or-callback-cost-not-measured
    canon-change-not-authorized
    public-car-cdr-identities-not-removed)

  (next-falsification
    "A genuine strict-compression candidate must be weaker than full pair-elim yet still derive both CAR and CDR observable laws; otherwise it is another equivalent basis or a stronger hidden primitive.")

  (claim-boundary
    "A one-name primitive set is not automatically a smaller semantic basis. This run supports basis exchange, not semantic-power reduction."))
