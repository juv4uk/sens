; unify-observe-d1-witness — semantic/logic in binary SENS only.
; Axiom: width = address = identity. No Python. No Rust verdict.
;
; 1. D1:1 carrier is (010 (001 ()))
; 2. COND else discipline uses that carrier
; 3. failure atom is data (EQ), not host boolean
;
; Run under SENS / my-lisp fixture loader.

(load "lib/core.lisp")
(load "lib/unify-observe.lisp")

(0011 d1-true  (010 (001 ())))
(0011 d1-false (101 (001 (0)) (001 (1))))

; Local probe: else-branch of two-field COND must be exact D1:1
(0011 else-is-d1?
  (0010 ()
    (110
      ((101 (001 no) (001 yes)) d1-false)
      ((010 (001 ())) d1-true))))

(0011 unify-observe-d1-witness
  (0010 ()
    (110
      ((101 (else-is-d1?) d1-true)
       (001 (unify-observe-d1
              (status pass)
              (d1-true (010 (001 ())))
              (cond-else exact-d1)
              (unify surface once)
              (axiom width-equals-address))))
      ((010 (001 ()))
       (001 (unify-observe-d1 (status fail) (cond-else not-d1)))))))

(unify-observe-d1-witness)
