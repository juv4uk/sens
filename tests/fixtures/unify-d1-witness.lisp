; unify-d1-witness — semantic/logic in binary SENS only.
; Axiom: width = address = identity. No Python. No Rust as meaning.
;
; 1. D1:1 is (010 (001 ()))
; 2. COND else uses that carrier
; 3. fail is data atom, not host boolean
;
; Run under SENS / my-lisp fixture loader.

(load "lib/core.lisp")
(load "lib/unify.lisp")

(0011 d1-true  (010 (001 ())))
(0011 d1-false (101 (001 (0)) (001 (1))))

(0011 else-is-d1?
  (0010 ()
    (110
      ((101 (001 no) (001 yes)) d1-false)
      ((010 (001 ())) d1-true))))

(0011 unify-d1-witness
  (0010 ()
    (110
      ((101 (else-is-d1?) d1-true)
       (001 (unify-d1
              (status pass)
              (d1-true (010 (001 ())))
              (cond-else exact-d1)
              (surfaces var? lookup-subst unify occurs-check)
              (axiom width-equals-address))))
      ((010 (001 ()))
       (001 (unify-d1 (status fail) (cond-else not-d1)))))))

(unify-d1-witness)
