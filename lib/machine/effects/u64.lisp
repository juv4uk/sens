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

; Exact-width structural false, not historical W8 zero:
; ATOM(QUOTE(one-element list)) is always D1:0, independently of the
; quoted element. Thirteen old 8-bit data words were replaced by D3:000;
; 13*(8-3)=65 source identity bits saved. D3:000 stays structural empty;
; it is NOT D1:0. The evaluated predicate still returns D1:0.
; Executable binary SENS laws and an exact one-bit negative mutant:
; tests/semantic/machine-effect-d3-false-{law,mutant}.{bits,sens}.
; No W8->D8 reinterpretation, no new primitive, no arithmetic-law change.

(0011 machine-effect-wire-denominator-one?
  (0010 (text)
    (110
      ((110011100 text) (010 (001 (000))))
      ((тотожне? (110101011 text) "/")
       (001000 ((rest (110011101 text)))
         (110
           ((110011100 rest) (010 (001 (000))))
           ((тотожне? (110101011 rest) "1")
            (110
              ((110011100 (110011101 rest)) (010 (001 ())))
              ((010 (001 ())) (010 (001 (000))))))
           ((010 (001 ())) (010 (001 (000)))))))
      ((010 (001 ()))
       (machine-effect-wire-denominator-one? (110011101 text))))))

(0011 machine-effect-exact-integer?
  (0010 (value)
    (001000 ((wire (11110100 value)))
      (110
        ((110101010 "#q2:" wire)
         (machine-effect-wire-denominator-one? wire))
        ((010 (001 ())) (010 (001 (000))))))))

(0011 machine-effect-within-inclusive-integer-range?
  (0010 (value lower upper)
    (110
      ((менше? value lower) (менше? 1 0))
      ((менше? upper value) (менше? 1 0))
      ((атом? ()) (менше? 0 1)))))

(0011 machine-effect-u32-carrier?
  (0010 (value)
    (110
      ((machine-effect-exact-integer? value)
       (machine-effect-within-inclusive-integer-range?
         value 0 4294967295))
      ((010 (001 ()))
       (010 (001 (000)))))))

(0011 machine-effect-bounded-u64-add-form?
  (0010 (effect)
    (110
      ((010 effect) (010 (001 (000))))
      ((тотожне? (000000 effect) 3)
       (тотожне? (100 effect) (001 bounded-u64-add)))
      ((010 (001 ()))
       (010 (001 (000)))))))

(0011 machine-effect-bounded-u64-add
  (0010 (left right)
    (110
      ((machine-effect-u32-carrier? left)
       (110
         ((machine-effect-u32-carrier? right)
          (1110 (001 bounded-u64-add) left right))
         ((010 (001 ())) (001 machine-effect-rejected))))
      ((010 (001 ())) (001 machine-effect-rejected)))))

; #4358 replay — target-neutral bounded DIFFERENCE/TIMES mechanism requests.
;
; These constructors preserve the already-proved bounded rectangles:
;   DIFFERENCE: exact non-negative u64 inputs with left >= right;
;   TIMES: exact non-negative u32 inputs, whose product is guaranteed u64.
;
; No target, ISA, register, flag, encoding, surface spelling, or domain
; coordinate belongs in this generic effect-definition module.

(0011 machine-effect-u64-carrier?
  (0010 (value)
    (110
      ((machine-effect-exact-integer? value)
       (machine-effect-within-inclusive-integer-range?
         value 0 18446744073709551615))
      ((010 (001 ()))
       (010 (001 (000)))))))

(0011 machine-effect-bounded-u64-sub-form?
  (0010 (effect)
    (110
      ((010 effect) (010 (001 (000))))
      ((тотожне? (000000 effect) 3)
       (тотожне? (100 effect) (001 bounded-u64-sub)))
      ((010 (001 ()))
       (010 (001 (000)))))))

(0011 machine-effect-bounded-u64-mul-form?
  (0010 (effect)
    (110
      ((010 effect) (010 (001 (000))))
      ((тотожне? (000000 effect) 3)
       (тотожне? (100 effect) (001 bounded-u64-mul)))
      ((010 (001 ()))
       (010 (001 (000)))))))

; Застосовувати лише точні предикати D5/D6 як тести D3 COND.
; Історичні W8 числові порівняння не є D1 PredicateBit.
(0011 machine-effect-bounded-u64-sub
  (0010 (left right)
    (110
      ((machine-effect-u64-carrier? left)
       (110
         ((machine-effect-u64-carrier? right)
          (110
            ((менше? left right)
             (001 machine-effect-rejected))
            ((атом? ())
             (1110 (001 bounded-u64-sub) left right))))
         ((010 (001 ())) (001 machine-effect-rejected))))
      ((010 (001 ())) (001 machine-effect-rejected)))))

(0011 machine-effect-bounded-u64-mul
  (0010 (left right)
    (110
      ((machine-effect-u32-carrier? left)
       (110
         ((machine-effect-u32-carrier? right)
          (1110 (001 bounded-u64-mul) left right))
         ((010 (001 ())) (001 machine-effect-rejected))))
      ((010 (001 ())) (001 machine-effect-rejected)))))

