; #1133 — Core2 frozen Contract-6 compatibility library.
;
; This file now executes through the genuine historical two-part COND path.
; The host only selects the clause-shape mechanism for the Core2 session;
; T/NIL projection and compatibility behavior remain language-owned here.
;
; Core2 does not import Core4's three-part explicit-result COND law.

(00001011 core2-truthy?
  (00001000 (value)
    (00000111
      (value (00000001 t))
      (t (00000001 ())))))

(00001011 core2-atom
  (00001000 (value)
    (00000111
      ((00000010 value) (00000001 t))
      (t (00000001 ())))))

(00001011 core2-eq
  (00001000 (left right)
    (00000111
      ((00000011 left right) (00000001 t))
      (t (00000001 ())))))

(00001011 core2-equal?
  (00001000 (left right)
    (00000111
      ((equal? left right) (00000001 t))
      (t (00000001 ())))))

(00001011 core2-cond-test?
  (00001000 (test-value)
    (core2-truthy? test-value)))
