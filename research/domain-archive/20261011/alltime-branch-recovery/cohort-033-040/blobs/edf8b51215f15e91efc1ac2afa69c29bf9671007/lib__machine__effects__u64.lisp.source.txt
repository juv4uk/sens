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


; #4358 — extend the calibrated target-neutral arithmetic effect seam.
; These effects preserve the already-proved current D5 bounded rectangles:
;   DIFFERENCE: exact non-negative u64 inputs with left >= right;
;   TIMES: exact non-negative u32 inputs, whose product is guaranteed u64.
; They are mechanism requests only; exact D5 arithmetic meaning remains upstream.

(00001001 machine-effect-u64-carrier?
  (00001000 (value)
    (00000111
      ((machine-effect-exact-integer? value)
       (machine-effect-within-inclusive-integer-range?
         value 0 18446744073709551615))
      (t (00000001 ())))))

(00001001 machine-effect-bounded-u64-sub-form?
  (00001000 (effect)
    (00000111
      ((00000010 effect) (00000001 ()))
      ((00100010 (00101000 effect) 3)
       (00000011 (00000101 effect) (00000001 bounded-u64-sub)))
      (t (00000001 ())))))

(00001001 machine-effect-bounded-u64-mul-form?
  (00001000 (effect)
    (00000111
      ((00000010 effect) (00000001 ()))
      ((00100010 (00101000 effect) 3)
       (00000011 (00000101 effect) (00000001 bounded-u64-mul)))
      (t (00000001 ())))))

(00001001 machine-effect-bounded-u64-sub
  (00001000 (left right)
    (00000111
      ((machine-effect-u64-carrier? left)
       (00000111
         ((machine-effect-u64-carrier? right)
          (00000111
            ((00011110 left right) 1
             (00100111 (00000001 bounded-u64-sub) left right))
            ((00011110 left right) 0
             (00000001 machine-effect-rejected))))
         (t (00000001 machine-effect-rejected))))
      (t (00000001 machine-effect-rejected)))))

(00001001 machine-effect-bounded-u64-mul
  (00001000 (left right)
    (00000111
      ((machine-effect-u32-carrier? left)
       (00000111
         ((machine-effect-u32-carrier? right)
          (00100111 (00000001 bounded-u64-mul) left right))
         (t (00000001 machine-effect-rejected))))
      (t (00000001 machine-effect-rejected)))))

; Exact DomainIdentity selection above any target projection. Width and packed
; bits are passed separately from the already-lowered DomainCall; no surface
; spelling or historical packed byte participates.
(00001001 machine-effect-current-domain-key?
  (00001000 (width bits expected-width expected-bits)
    (00000111
      ((00100010 width expected-width)
       (00100010 bits expected-bits))
      (t (00000001 ())))))

(00001001 machine-effect-lower-current-binary-u64
  (00001000 (width bits left right)
    (00000111
      ((machine-effect-current-domain-key? width bits 5 10)
       (machine-effect-bounded-u64-add left right))
      ((machine-effect-current-domain-key? width bits 5 11)
       (machine-effect-bounded-u64-sub left right))
      ((machine-effect-current-domain-key? width bits 5 22)
       (machine-effect-bounded-u64-mul left right))
      (t (00000001 machine-effect-not-applicable)))))
