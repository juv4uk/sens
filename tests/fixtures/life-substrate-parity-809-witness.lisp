; Lisp-owned fail-closed witness for #809.

(def life-substrate-parity-schema
  (lambda () (car life-substrate-parity-document)))

(def life-substrate-parity-witness
  (lambda ()
    (cond
      ((eq (life-substrate-parity-schema) (quote life-substrate-parity/1))
       (identity-relation same)
       (list
         (quote life-substrate-parity-witness)
         (list (quote status) (quote pass))
         (list (quote detail) (quote awaiting-real-graal-evidence))))
      ((eq (life-substrate-parity-schema) (quote life-substrate-parity/1))
       (identity-relation distinct)
       (list
         (quote life-substrate-parity-witness)
         (list (quote status) (quote fail))
         (list (quote detail) (quote wrong-schema)))))))
