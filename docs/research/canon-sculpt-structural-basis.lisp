; #419 structural-basis research notes.
; Research data only; NOT semantic authority and NOT a proof of irreducibility.
;
; Purpose: turn vague "seems primitive" claims into explicit restricted-basis
; hypotheses that a future bounded term search or constructive derivation can
; falsify.

(canon-sculpt-structural-basis
  (schema-version 1)
  (base-main 04084f1003ebd78c946a4b135b8a9febfc7e040e)
  (status hypotheses-awaiting-bounded-search)

  ; These existing helpers are NOT lower alternatives: current source already
  ; defines them from the Canon operations named here.
  (derived-helper-dependencies
    (equal?
      (uses PRIM_ATOM PRIM_EQ PRIM_CAR PRIM_CDR PRIM_COND PRIM_QUOTE))
    (nth
      (uses PRIM_EQ PRIM_CAR PRIM_CDR PRIM_COND))
    (member?
      (uses PRIM_ATOM equal? PRIM_CAR PRIM_CDR PRIM_COND PRIM_QUOTE))
    (assoc
      (uses PRIM_ATOM equal? PRIM_CAR PRIM_CDR PRIM_COND PRIM_QUOTE))
    (symbol?
      (uses PRIM_ATOM PRIM_EQ PRIM_COND write-to-string string->symbol PRIM_QUOTE)))

  (hypothesis
    (candidate PRIM_CAR)
    (name same-tail-different-head)
    (restricted-basis PRIM_QUOTE PRIM_ATOM PRIM_EQ PRIM_CONS PRIM_CDR PRIM_COND lambda)
    (left-input  (cons (quote alpha) (quote tail)))
    (right-input (cons (quote beta)  (quote tail)))
    (shared-observations
      (PRIM_ATOM structural-kind-pair)
      (PRIM_CDR tail)
      (PRIM_EQ invalid-on-pairs))
    (required-distinction
      (PRIM_CAR left-input alpha)
      (PRIM_CAR right-input beta))
    (claim-under-test
      "Without a head observer or a stronger hidden pair destructor, the restricted basis cannot distinguish these inputs in the way car must."))

  (hypothesis
    (candidate PRIM_CDR)
    (name same-head-different-tail)
    (restricted-basis PRIM_QUOTE PRIM_ATOM PRIM_EQ PRIM_CONS PRIM_CAR PRIM_COND lambda)
    (left-input  (cons (quote head) (quote alpha)))
    (right-input (cons (quote head) (quote beta)))
    (shared-observations
      (PRIM_ATOM structural-kind-pair)
      (PRIM_CAR head)
      (PRIM_EQ invalid-on-pairs))
    (required-distinction
      (PRIM_CDR left-input alpha)
      (PRIM_CDR right-input beta))
    (claim-under-test
      "Without a tail observer or a stronger hidden pair destructor, the restricted basis cannot distinguish these inputs in the way cdr must."))

  (hypothesis
    (candidate PRIM_EQ)
    (name distinct-atoms-same-structural-kind)
    (restricted-basis PRIM_QUOTE PRIM_ATOM PRIM_CONS PRIM_CAR PRIM_CDR PRIM_COND lambda)
    (left-input  (quote radio))
    (right-input (quote antenna))
    (shared-observations
      (PRIM_ATOM structural-kind-atom)
      (PRIM_CAR invalid-on-atoms)
      (PRIM_CDR invalid-on-atoms))
    (required-distinction
      (PRIM_EQ radio radio identity-relation-same)
      (PRIM_EQ radio antenna identity-relation-distinct))
    (claim-under-test
      "A structure-only basis has no admitted atom-identity observer unless one is smuggled in through a richer library operation or host representation."))

  (hypothesis
    (candidate PRIM_ATOM)
    (name total-safe-structural-classification)
    (restricted-basis PRIM_QUOTE PRIM_EQ PRIM_CONS PRIM_CAR PRIM_CDR PRIM_COND lambda)
    (required-domain empty-list pair atom)
    (obstruction
      "car/cdr are partial and fail on non-pairs; eq is atom-only and fails on pairs; the basis has no error-catching or representation-tag observer declared lower than atom."))
    (claim-under-test
      "A total three-way structural classifier cannot be obtained from only partial destructors plus atom-only identity without another safe structural discriminator."))

  (hypothesis
    (candidate PRIM_CONS)
    (name dynamic-runtime-pair-construction)
    (restricted-basis PRIM_QUOTE PRIM_ATOM PRIM_EQ PRIM_CAR PRIM_CDR PRIM_COND lambda)
    (inputs runtime-left runtime-right)
    (required-result pair-containing-both-runtime-inputs)
    (obstruction
      "quote can provide only source-static structure; observers can only inspect existing values; lambda can package values as a closure but that value is not a pair under current observable structural laws."))
    (claim-under-test
      "Without a pair constructor or a stronger aggregate constructor, the restricted basis cannot create a fresh pair from arbitrary evaluated runtime values."))

  (rejected-shortcuts
    (pair? "no current my-lisp semantic surface found; adding it would merely introduce another structural classifier")
    (equal? "currently derived from atom/eq/car/cdr/cond, therefore circular as a lower witness")
    (nth "currently derived from eq/car/cdr/cond")
    (writer-or-string-roundtrip "richer presentation/conversion capability, not a lower structural basis")
    (vector-or-buffer "stronger aggregate domain; moving pair semantics into it is not subtraction unless that domain is independently lower")
    (host-value-tag "implementation representation cannot establish language semantics"))

  (falsification-plan
    (step 1 "Define an exact allowed-term grammar per hypothesis; do not permit higher helpers whose implementation already uses the candidate.")
    (step 2 "Enumerate closed terms up to increasing depth over two distinguished inputs and record observable outcomes/errors.")
    (step 3 "If a term realizes the candidate law, mark derivable-candidate and inspect it for hidden stronger mechanisms.")
    (step 4 "If no term is found, record only a bounded negative result; bounded search is not a mathematical impossibility proof.")
    (step 5 "Separately attempt a symbolic observational-equivalence proof before any 1.0 irreducibility claim.")))
