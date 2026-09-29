; Core2 compatibility/study profile on the shared SENS predicate foundation.
;
; Historical Contract-6 T/NIL truthiness is provenance only. Active Core2 uses
; the same exact one-bit predicate result and two-part COND as Core1/Core3/Core4.
;
; Predicate constants below are produced by ATOM itself:
;   (00000010 '())          -> PredicateBit YES
;   (00000010 '(00000000))  -> PredicateBit NO
; They are not Number 1/0, T/NIL, or source predicate literals.

; Compatibility spelling retained, but the operation is now strict:
; it accepts only a PredicateBit because COND rejects every other test domain.
; The result is the same exact predicate bit.
(00001011 core2-truthy?
  (00001000 (value)
    (00000111
      (value (00000010 (00000001 ())))
      ((00000010 (00000001 ()))
       (00000010 (00000001 (00000000)))))))

; Shared foundation predicates are not profile projections anymore.
(00001011 core2-atom
  (00001000 (value)
    (00000010 value)))

(00001011 core2-eq
  (00001000 (left right)
    (00000011 left right)))

; Deep equality remains a separate operation from EQ. Its result-domain
; migration is owned independently; Core2 adds no truthiness wrapper here.
(00001011 core2-equal?
  (00001000 (left right)
    (00100010 left right)))

(00001011 core2-cond-test?
  (00001000 (test-value)
    (core2-truthy? test-value)))
