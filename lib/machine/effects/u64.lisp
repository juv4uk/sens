; #4347 — first executable target-neutral machine effect.
;
; This file owns only a bounded carrier/mechanism fact. It contains no target
; register, instruction, mnemonic, encoding, feature, or calling-convention
; identity. Language arithmetic meaning remains upstream.
;
; First calibration slice:
;   exact non-negative u32 left/right
;   -> (bounded-u64-add left right)
;
; The u32 input bound is intentionally the same conservative rectangle already
; proved by the current exact-D5 PLUS native donor. It guarantees the mathematical
; sum fits u64 without making this effect a new arithmetic semantic primitive.

(00001001 machine-effect-wire-denominator-one?
  (00001000 (text)
    (00000111
      ((00111100 text) (00000001 ()))
      ((00000011 (00111111 text) "/")
       (10011100 ((rest (01000000 text)))
         (00000111
           ((00111100 rest) (00000001 ()))
           ((00000011 (00111111 rest) "1")
            (00000111
              ((00111100 (01000000 rest)) t)
              ((00000011 0 0) (00000001 ()))))
           ((00000011 0 0) (00000001 ())))))
      ((00000011 0 0)
       (machine-effect-wire-denominator-one? (01000000 text))))))

(00001001 machine-effect-exact-integer?
  (00001000 (value)
    (10011100 ((wire (01001100 value)))
      (00000111
        ((00111101 "#q2:" wire)
         (machine-effect-wire-denominator-one? wire))
        ((00000011 0 0) (00000001 ()))))))

(00001001 machine-effect-within-inclusive-integer-range?
  (00001000 (value lower upper)
    (00000111
      ((00011110 value lower) 1
       (00000111
         ((00011101 value upper) 1 t)
         ((00011101 value upper) 0 (00000001 ()))))
      ((00011110 value lower) 0 (00000001 ())))))

(00001001 machine-effect-u32-carrier?
  (00001000 (value)
    (00000111
      ((machine-effect-exact-integer? value)
       (machine-effect-within-inclusive-integer-range?
         value 0 4294967295))
      (t (00000001 ())))))

(00001001 machine-effect-bounded-u64-add-form?
  (00001000 (effect)
    (00000111
      ((00000010 effect) (00000001 ()))
      ((00100010 (00101000 effect) 3)
       (00000011 (00000101 effect) (00000001 bounded-u64-add)))
      (t (00000001 ())))))

(00001001 machine-effect-bounded-u64-add
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