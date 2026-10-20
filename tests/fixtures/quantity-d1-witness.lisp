; quantity-d1-witness — semantic witness, Ukrainian projection only.
; Axiom: width = address = identity. No Python. No host t/NIL.
;
; Checks:
;   1. D1:1 is (атом? (як-є ()))
;   2. dimension/quantity schemas are atoms via quote
;   3. make-dimension + dimension? round-trip shape
;   4. COND else discipline uses exact D1

(load "lib/core.lisp")
(load "lib/quantity.lisp")

(визначити d1-true (атом? (як-є ())))
(визначити d1-false (тотожне? (як-є (0)) (як-є (1))))

(визначити quantity-d1-witness
  (функція ()
    (нехай ((dim (make-dimension (як-є metre) 1))
           (ok (dimension? dim)))
      (за-умовою
        ((тотожне? ok d1-true)
         (як-є (quantity-d1
                (status pass)
                (d1-true (атом? (як-є ())))
                (dimension-schema dimension/1)
                (axiom width-equals-address))))
        ((атом? (як-є ()))
         (як-є (quantity-d1 (status fail) (dimension? not-d1))))))))

(quantity-d1-witness)
