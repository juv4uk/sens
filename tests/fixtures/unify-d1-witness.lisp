; unify-d1-witness — semantic/logic, Ukrainian projection only.
; Axiom: width = address = identity. No Python. No Rust as meaning.
;
; 1. D1:1 is (атом? (як-є ()))
; 2. COND else uses that carrier
; 3. unify surfaces present

(load "lib/core.lisp")
(load "lib/unify.lisp")

(визначити d1-true (атом? (як-є ())))
(визначити d1-false (тотожне? (як-є (0)) (як-є (1))))

(визначити else-is-d1?
  (функція ()
    (за-умовою
      ((тотожне? (як-є no) (як-є yes)) d1-false)
      ((атом? (як-є ())) d1-true))))

(визначити unify-d1-witness
  (функція ()
    (за-умовою
      ((тотожне? (else-is-d1?) d1-true)
       (як-є (unify-d1
              (status pass)
              (d1-true (атом? (як-є ())))
              (cond-else exact-d1)
              (surfaces var? lookup-subst unify occurs-check)
              (axiom width-equals-address))))
      ((атом? (як-є ()))
       (як-є (unify-d1 (status fail) (cond-else not-d1)))))))

(unify-d1-witness)
