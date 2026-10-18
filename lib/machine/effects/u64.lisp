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

(визначити machine-effect-wire-denominator-one?
  (функція (text)
    (за-умовою
      ((110011100 text) (010 (001 (000))))
      ((тотожне? (рядок-перший text) "/")
       (нехай ((rest (рядок-решта text)))
         (за-умовою
           ((110011100 rest) (010 (001 (000))))
           ((тотожне? (рядок-перший rest) "1")
            (за-умовою
              ((рядок-порожній? (рядок-решта rest)) (атом? (як-є ())))
              ((010 (001 ())) (010 (001 (000))))))
           ((010 (001 ())) (010 (001 (000)))))))
      ((атом? (як-є ()))
       (machine-effect-wire-denominator-one? (рядок-решта text))))))

(визначити machine-effect-exact-integer?
  (функція (value)
    (нехай ((wire (значення-у-текст value)))
      (за-умовою
        ((рядок-префікс? "#q2:" wire)
         (machine-effect-wire-denominator-one? wire))
        ((010 (001 ())) (010 (001 (000))))))))

(визначити machine-effect-within-inclusive-integer-range?
  (функція (value lower upper)
    (за-умовою
      ((менше? value lower) (менше? 1 0))
      ((менше? upper value) (менше? 1 0))
      ((атом? ()) (менше? 0 1)))))

(визначити machine-effect-u32-carrier?
  (функція (value)
    (за-умовою
      ((machine-effect-exact-integer? value)
       (machine-effect-within-inclusive-integer-range?
         value 0 4294967295))
      ((атом? (як-є ()))
       (010 (001 (000)))))))

(визначити machine-effect-bounded-u64-add-form?
  (функція (effect)
    (за-умовою
      ((010 effect) (010 (001 (000))))
      ((тотожне? (довжина effect) 3)
       (тотожне? (перше effect) (як-є bounded-u64-add)))
      ((атом? (як-є ()))
       (010 (001 (000)))))))

(визначити machine-effect-bounded-u64-add
  (функція (left right)
    (за-умовою
      ((machine-effect-u32-carrier? left)
       (за-умовою
         ((machine-effect-u32-carrier? right)
          (список (як-є bounded-u64-add) left right))
         ((атом? (як-є ())) (як-є machine-effect-rejected))))
      ((атом? (як-є ())) (як-є machine-effect-rejected)))))

; #4358 replay — target-neutral bounded DIFFERENCE/TIMES mechanism requests.
;
; These constructors preserve the already-proved bounded rectangles:
;   DIFFERENCE: exact non-negative u64 inputs with left >= right;
;   TIMES: exact non-negative u32 inputs, whose product is guaranteed u64.
;
; No target, ISA, register, flag, encoding, surface spelling, or domain
; coordinate belongs in this generic effect-definition module.

(визначити machine-effect-u64-carrier?
  (функція (value)
    (за-умовою
      ((machine-effect-exact-integer? value)
       (machine-effect-within-inclusive-integer-range?
         value 0 18446744073709551615))
      ((атом? (як-є ()))
       (010 (001 (000)))))))

(визначити machine-effect-bounded-u64-sub-form?
  (функція (effect)
    (за-умовою
      ((010 effect) (010 (001 (000))))
      ((тотожне? (довжина effect) 3)
       (тотожне? (перше effect) (як-є bounded-u64-sub)))
      ((атом? (як-є ()))
       (010 (001 (000)))))))

(визначити machine-effect-bounded-u64-mul-form?
  (функція (effect)
    (за-умовою
      ((010 effect) (010 (001 (000))))
      ((тотожне? (довжина effect) 3)
       (тотожне? (перше effect) (як-є bounded-u64-mul)))
      ((атом? (як-є ()))
       (010 (001 (000)))))))

; Застосовувати лише точні предикати D5/D6 як тести D3 COND.
; Історичні W8 числові порівняння не є D1 PredicateBit.
(визначити machine-effect-bounded-u64-sub
  (функція (left right)
    (за-умовою
      ((machine-effect-u64-carrier? left)
       (за-умовою
         ((machine-effect-u64-carrier? right)
          (за-умовою
            ((менше? left right)
             (як-є machine-effect-rejected))
            ((атом? ())
             (список (як-є bounded-u64-sub) left right))))
         ((атом? (як-є ())) (як-є machine-effect-rejected))))
      ((атом? (як-є ())) (як-є machine-effect-rejected)))))

(визначити machine-effect-bounded-u64-mul
  (функція (left right)
    (за-умовою
      ((machine-effect-u32-carrier? left)
       (за-умовою
         ((machine-effect-u32-carrier? right)
          (список (як-є bounded-u64-mul) left right))
         ((атом? (як-є ())) (як-є machine-effect-rejected))))
      ((атом? (як-є ())) (як-є machine-effect-rejected)))))

