; domain-bitness-witness — exact-width domain tables, Ukrainian projection.
;
; Axiom: the binary key width IS the domain address.
; D1 has 2^1 rows of 1-bit keys; D2 has 2^2 of 2-bit; ... D10 has 2^10 of 10-bit.
; Semantics owned by SENS. No Python oracle for this claim.

(load "lib/core.lisp")

(визначити d1-true (атом? (як-є ())))
(визначити d1-false (тотожне? (як-є (0)) (як-є (1))))

; D1 table: keys 0 and 1 — width 1, exactly 2 rows.
(визначити d1-keys
  (як-є ((0) (1))))

(визначити d1-key-width-ok?
  (функція (keys)
    (за-умовою
      ((атом? keys) d1-true)
      (так
       (за-умовою
         ((тотожне? (перше (перше keys)) (як-є 0))
          (d1-key-width-ok? (решта keys)))
         ((тотожне? (перше (перше keys)) (як-є 1))
          (d1-key-width-ok? (решта keys)))
         ((атом? (як-є ())) d1-false))))))

; D2 keys: 00 01 10 11 — width 2, exactly 4 rows.
(визначити d2-keys
  (як-є ((00) (01) (10) (11))))

(визначити domain-bitness-witness
  (функція ()
    (за-умовою
      ((тотожне? (d1-key-width-ok? d1-keys) d1-true)
       (як-є (domain-bitness
               (status pass)
               (d1-width 1)
               (d1-rows 2)
               (d2-width 2)
               (d2-rows 4)
               (axiom width-equals-address))))
      ((атом? (як-є ()))
       (як-є (domain-bitness (status fail) (d1-width mismatch)))))))

(domain-bitness-witness)
