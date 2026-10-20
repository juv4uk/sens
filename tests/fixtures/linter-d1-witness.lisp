; linter-d1-witness — semantic/logic, Ukrainian projection only.
; Axiom: width = address = identity. No Python. No Rust as meaning.
;
; 1. D1:1 is (атом? (як-є ()))
; 2. COND else uses that carrier
; 3. lint-form-head / lint-head surface present

(load "lib/core.lisp")
(load "lib/linter.lisp")

(визначити d1-true (атом? (як-є ())))
(визначити d1-false (тотожне? (як-є (0)) (як-є (1))))

(визначити else-is-d1?
  (функція ()
    (за-умовою
      ((тотожне? (як-є no) (як-є yes)) d1-false)
      ((атом? (як-є ())) d1-true))))

(визначити linter-d1-witness
  (функція ()
    (за-умовою
      ((тотожне? (else-is-d1?) d1-true)
       (як-є (linter-d1
              (status pass)
              (d1-true (атом? (як-є ())))
              (cond-else exact-d1)
              (surfaces lint-form-head lint-head lint-size)
              (axiom width-equals-address))))
      ((атом? (як-є ()))
       (як-є (linter-d1 (status fail) (cond-else not-d1)))))))

(linter-d1-witness)
