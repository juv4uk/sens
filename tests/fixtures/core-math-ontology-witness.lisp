; core-math-ontology-witness — semantic witness in binary SENS.
;
; Axiom: width = address = identity.
; Same bits in different domains do NOT share meaning.
; A bit pattern without a proved law is not a Core-Math law.
; Semantics owned by SENS, not Python / not Rust harness.
;
; Witnesses:
;   1. D1 PredicateBit carriers exact.
;   2. Domain tag is part of the semantic object (pair bits+domain).
;   3. Equal bit-strings under unequal domains are not EQ as semantic objects.
;   4. No executable law claimed — status is ontology-only until #2425.
;
; Run under my-lisp / SENS fixture loader.

(load "lib/core.lisp")
(load "lib/core-math.lisp")

(0011 d1-true  (010 (001 ())))
(0011 d1-false (101 (001 (0)) (001 (1))))

; Semantic object skeleton: (bits domain) — domain is exact-width address.
(0011 make-math-object
  (0010 (bits domain)
    (1110 (001 core-math-object) bits domain)))

; Two objects with identical bits but different domain tags.
(0011 obj-d1-zero (make-math-object (001 0) (001 d1)))
(0011 obj-d2-zero (make-math-object (001 0) (001 d2)))

; Structural EQ of full objects — domains differ => not equal.
(0011 same-semantic-object?
  (0010 (a b)
    (110
      ((101 a b) d1-true)
      ((010 (001 ())) d1-false))))

; Bits-only projection (lab tool, not Core-Math meaning).
(0011 math-object-bits
  (0010 (obj)
    (1001 obj)))

(0011 math-object-domain
  (0010 (obj)
    (10011 obj)))

(0011 core-math-ontology-witness
  (0010 ()
    (110
      ; identical bits under d1 vs d2 must not collapse to one meaning
      ((101 (same-semantic-object? obj-d1-zero obj-d2-zero) d1-false)
       (110
         ; bits projection may match while domain differs
         ((101 (math-object-bits obj-d1-zero) (math-object-bits obj-d2-zero))
          (110
            ((101 (math-object-domain obj-d1-zero) (001 d1))
             (110
               ((101 (math-object-domain obj-d2-zero) (001 d2))
                (001 (core-math-ontology
                       (status pass)
                       (same-bits-different-domain not-eq)
                       (executable-laws none-until-2425)
                       (axiom width-equals-address))))
               ((010 (001 ()))
                (001 (core-math-ontology
                       (status fail) (d2-domain mismatch))))))
            ((010 (001 ()))
             (001 (core-math-ontology
                    (status fail) (d1-domain mismatch))))))
         ((010 (001 ()))
          (001 (core-math-ontology
                 (status fail) (bits-projection mismatch))))))
      ((010 (001 ()))
       (001 (core-math-ontology
              (status fail) (cross-domain-collapse)))))))

(core-math-ontology-witness)
