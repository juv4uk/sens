; #211 — replaceability witness.
; CI runs this after physically moving lib/machine out of the checkout.
; The expected answers live here in Lisp; the shell observes only the named
; pass envelope. Removing a backend may remove execution capability, never
; the meaning of these already-ratified language forms.

(load "lib/core.lisp")

(00001001 machine-replaceability-rows
  (00000001
    ((add
       (00001100 2 3)
       5)
     (eq-cond
       (00000111
         ((00000011 2 2)
          111)
         ((00000010 (00000001 ()))
          222))
       111)
     (car-cons
       (00000101 (00000100 2 3))
       2))))

(00001001 machine-replaceability-run
  (00001000 (rows)
    (00000111
      ((00000010 rows)
       (00000111
         ((00000011 rows (00000001 ()))
          (00000001 (machine-replaceability-witness (status pass))))
         ((00000010 (00000001 ()))
          (00100111
            (00000001 machine-replaceability-witness)
            (00000001 (status fail))
            (00100111 (00000001 case) (00000001 malformed-row-tail))))))
      ((00000010 (00000001 ()))
       (10011101 ((row (00000101 rows))
              (name (00000101 row))
              (actual (01001101 (00101111 row)))
              (expected (00110000 row)))
         (00000111
           ((00100010 actual expected)
            (machine-replaceability-run (00000110 rows)))
           ((00000010 (00000001 ()))
            (00100111
              (00000001 machine-replaceability-witness)
              (00000001 (status fail))
              (00100111 (00000001 case) name)
              (00100111 (00000001 expected) expected)
              (00100111 (00000001 actual) actual)))))))))

(machine-replaceability-run machine-replaceability-rows)
