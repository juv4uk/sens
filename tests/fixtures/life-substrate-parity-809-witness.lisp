; Lisp-owned fail-closed witness for #809.

(визначити life-substrate-parity-schema
  (функція () (перше life-substrate-parity-document)))

(визначити life-substrate-parity-witness
  (функція ()
    (за-умовою
      ((тотожне? (life-substrate-parity-schema) (як-є life-substrate-parity/1))
       (identity-relation same)
       (список
         (як-є life-substrate-parity-witness)
         (список (як-є status) (як-є pass))
         (список (як-є detail) (як-є awaiting-real-graal-evidence))))
      ((тотожне? (life-substrate-parity-schema) (як-є life-substrate-parity/1))
       (identity-relation distinct)
       (список
         (як-є life-substrate-parity-witness)
         (список (як-є status) (як-є fail))
         (список (як-є detail) (як-є wrong-schema)))))))
