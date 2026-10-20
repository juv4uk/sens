; unify-observe-d1-witness — semantic/logic, Ukrainian projection only.
; Axiom: width = address = identity. No Python. No Rust verdict.
;
; 1. D1:1 carrier is (атом? (як-є ()))
; 2. COND else discipline uses that carrier
; 3. failure atom is data (EQ), not host boolean

(load "lib/core.lisp")
(load "lib/unify-observe.lisp")

(визначити d1-true (атом? (як-є ())))
(визначити d1-false (тотожне? (як-є (0)) (як-є (1))))

(визначити else-is-d1?
  (функція ()
    (за-умовою
      ((тотожне? (як-є no) (як-є yes)) d1-false)
      ((атом? (як-є ())) d1-true))))

(визначити unify-observe-d1-witness
  (функція ()
    (за-умовою
      ((тотожне? (else-is-d1?) d1-true)
       (як-є (unify-observe-d1
              (status pass)
              (d1-true (атом? (як-є ())))
              (cond-else exact-d1)
              (unify surface once)
              (axiom width-equals-address))))
      ((атом? (як-є ()))
       (як-є (unify-observe-d1 (status fail) (cond-else not-d1)))))))

(unify-observe-d1-witness)
