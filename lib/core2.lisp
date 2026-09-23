; #1133 — Core2 compatibility projection helpers.
;
; These definitions run on the current my-lisp mechanism while projecting
; selected observations into the frozen Contract-6 T/NIL result domain.
; They do NOT mutate Core4 law and they do NOT pretend that a function can
; replace profile-aware lazy COND syntax.
;
; Full native Core2 special-form selection remains an explicit integration
; boundary. See contracts/core2-profile-contract.lisp.

(def core2-truthy?
  (lambda (value)
    (cond
      ((atom value) (structural-kind empty-list) (quote ()))
      ((quote core2-fallback) core2-fallback (quote t)))))

(def core2-atom
  (lambda (value)
    (cond
      ((atom value) (structural-kind atom) (quote t))
      ((atom value) (structural-kind empty-list) (quote t))
      ((atom value) (structural-kind pair) (quote ())))))

(def core2-eq
  (lambda (left right)
    (cond
      ((eq left right) (identity-relation same) (quote t))
      ((eq left right) (identity-relation distinct) (quote ())))))

(def core2-equal?
  (lambda (left right)
    (cond
      ((equal? left right) (structural-relation same) (quote t))
      ((equal? left right) (structural-relation distinct) (quote ())))))

; A truth-domain helper used by profile-aware COND machinery.
; It only classifies an already evaluated test value; it does not evaluate
; branches and therefore does not fake special-form laziness.
(def core2-cond-test?
  (lambda (test-value)
    (core2-truthy? test-value)))