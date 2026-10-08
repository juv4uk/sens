  (00001000 (left right)
    (00000111
      ((machine-effect-u32-carrier? left)
       (00000111
         ((machine-effect-u32-carrier? right)
          (00100111 (00000001 bounded-u64-add) left right))
         (t (00000001 machine-effect-rejected))))
      (t (00000001 machine-effect-rejected)))))


; Shared exact non-negative u64 carrier for structural and later arithmetic
; effects. One owner avoids load-order redefinition between effect families.

(00001001 machine-effect-u64-carrier?
  (00001000 (value)
    (00000111
      ((machine-effect-exact-integer? value)
       (machine-effect-within-inclusive-integer-range?
         value 0 18446744073709551615))
      (t (00000001 ())))))