; #1133 — Core2 frozen Contract-6 compatibility library.
;
; This file now executes through the genuine historical two-part COND path.
; The host only selects the clause-shape mechanism for the Core2 session;
; T/NIL projection and compatibility behavior remain language-owned here.
;
; Core2 does not import Core4's three-part explicit-result COND law.

(def core2-truthy?
  (lambda (value)
    (cond
      (value (quote t))
      (t (quote ())))))

(def core2-atom
  (lambda (value)
    (cond
      ((atom value) (quote t))
      (t (quote ())))))

(def core2-eq
  (lambda (left right)
    (cond
      ((eq left right) (quote t))
      (t (quote ())))))

(def core2-equal?
  (lambda (left right)
    (cond
      ((equal? left right) (quote t))
      (t (quote ())))))

(def core2-cond-test?
  (lambda (test-value)
    (core2-truthy? test-value)))
