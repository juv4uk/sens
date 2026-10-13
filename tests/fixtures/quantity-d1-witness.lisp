; quantity-d1-witness — semantic witness in binary SENS only.
; Axiom: width = address = identity. No Python. No host t/NIL.
;
; Checks:
;   1. D1:1 is (010 (001 ()))
;   2. dimension/quantity schemas are atoms via quote
;   3. make-dimension + dimension? round-trip shape
;   4. COND else discipline uses exact D1
;
; Run: load under SENS / my-lisp fixture runner.

(load "lib/core.lisp")
(load "lib/quantity.lisp")

(0011 d1-true  (010 (001 ())))
(0011 d1-false (101 (001 (0)) (001 (1))))

(0011 quantity-d1-witness
  (0010 ()
    (001000 ((dim (make-dimension (001 metre) 1))
           (ok (dimension? dim)))
      (110
        ((101 ok d1-true)
         (001 (quantity-d1
                (status pass)
                (d1-true (010 (001 ())))
                (dimension-schema dimension/1)
                (axiom width-equals-address))))
        ((010 (001 ()))
         (001 (quantity-d1 (status fail) (dimension? not-d1))))))))

(quantity-d1-witness)
