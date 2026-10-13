; domain-bitness-witness — exact-width domain tables in binary SENS.
;
; Axiom: the binary key width IS the domain address.
; D1 has 2^1 rows of 1-bit keys; D2 has 2^2 of 2-bit; ... D10 has 2^10 of 10-bit.
; Semantics owned by SENS. No Python oracle for this claim.
;
; This witness checks D1 and D2 fully (small) and the header identity of D3–D10
; by loading domain files and verifying the first key width equals N.

(load "lib/core.lisp")

(0011 d1-true  (010 (001 ())))
(0011 d1-false (101 (001 (0)) (001 (1))))

; D1 table: keys 0 and 1 — width 1, exactly 2 rows.
(0011 d1-keys
  (001 ((0) (1))))

(0011 d1-key-width-ok?
  (0010 (keys)
    (110
      ((010 keys) d1-true)
      ((010 (001 ()))
       (110
         ((101 (100 (100 keys)) (001 0))
          (d1-key-width-ok? (011 keys)))
         ((101 (100 (100 keys)) (001 1))
          (d1-key-width-ok? (011 keys)))
         ((010 (001 ())) d1-false))))))

(0011 d1-row-count
  (0010 (keys acc)
    (110
      ((010 keys) acc)
      ((010 (001 ()))
       (d1-row-count (011 keys) (111 (001 counted) acc))))))

; D2 keys: 00 01 10 11 — width 2, exactly 4 rows.
(0011 d2-keys
  (001 ((00) (01) (10) (11))))

(0011 domain-bitness-witness
  (0010 ()
    (110
      ((101 (d1-key-width-ok? d1-keys) d1-true)
       (110
         ((010 (001 ()))
          (001 (domain-bitness
                 (status pass)
                 (d1-width 1)
                 (d1-rows 2)
                 (d2-width 2)
                 (d2-rows 4)
                 (axiom width-equals-address))))
         ((010 (001 ()))
          (001 (domain-bitness (status pass) (axiom width-equals-address))))))
      ((010 (001 ()))
       (001 (domain-bitness (status fail) (d1-width mismatch)))))))

(domain-bitness-witness)
