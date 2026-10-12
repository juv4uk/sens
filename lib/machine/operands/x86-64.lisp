; #177 — typed x86-64 machine operands as Lisp-owned data.
;
; This layer owns operand *shape*, not instruction admission and not encoding.
; Register knowledge is intentionally reused from x86-reg-code in the existing
; Lisp encoder so this file cannot become a second GPR table. A well-typed
; operand may still participate in an instruction form that #176 admission
; rejects; type success is not capability/admission success.

(0011 x86-machine-operand-rejection
  (0010 (expected actual)
    (1110 (001 rejected) (001 machine-operand) expected actual)))

(0011 x86-machine-rejected?
  (0010 (value)
    (110
      ((010 value) (101 (001 ()) (001 rejected)))
      ((010 ()) (101 (100 value) (001 rejected))))))

(0011 x86-gpr8-name?
  (0010 (name)
    (110
      ((110101100 name)
       (11101
         name
         (001
           (al cl dl bl spl bpl sil dil
               r8b r9b r10b r11b r12b r13b r14b r15b))))
      )))

(0011 x86-gpr64-name?
  (0010 (name)
    (110
      ((110101100 name)
       (11110101
         (0100 (101 (x86-reg-code name) (001 ())))
         (0100 (x86-gpr8-name? name))))
      )))

(0011 x86-gpr8?
  (0010 (operand)
    (110
      
      ((010 operand)  (001 ()))
      ((101 (100 operand) (001 gpr8))
       (110
         
         ((010 (011 operand))  (001 ()))
         ((101 (011 (011 operand)) (001 ()))
          (x86-gpr8-name? (1001 operand)))
         ))
      )))

(0011 x86-gpr8
  (0010 (name)
    (110
      ((x86-gpr8-name? name) (1110 (001 gpr8) name))
      ((010 ()) (x86-machine-operand-rejection (001 gpr8) name)))))

(0011 x86-as-gpr8
  (0010 (operand)
    (110
      ((x86-machine-rejected? operand) operand)
      ((x86-gpr8? operand) operand)
      ((010 ()) (x86-gpr8 operand)))))

(0011 x86-gpr8-value
  (0010 (operand)
    (1001 operand)))

(0011 x86-gpr64?
  (0010 (operand)
    (110
      
      ((010 operand)  (001 ()))
      ((101 (100 operand) (001 gpr64))
       (110
         
         ((010 (011 operand))  (001 ()))
         ((101 (011 (011 operand)) (001 ()))
          (x86-gpr64-name? (1001 operand)))
         ))
      )))

(0011 x86-gpr64
  (0010 (name)
    (110
      ((x86-gpr64-name? name) (1110 (001 gpr64) name))
      ((010 ()) (x86-machine-operand-rejection (001 gpr64) name)))))

(0011 x86-as-gpr64
  (0010 (operand)
    (110
      ((x86-machine-rejected? operand) operand)
      ((x86-gpr64? operand) operand)
      ((010 ()) (x86-gpr64 operand)))))

(0011 x86-gpr64-value
  (0010 (operand)
    (1001 operand)))

; A gpr32 operand is a 32-bit view of the same physical general-purpose
; register named by its canonical 64-bit base name. The encoder already owns
; the physical register-code mapping and the instruction form owns width, so
; this typed view deliberately does not introduce a second eax/ecx/... code
; table merely to say "lower 32 bits of rax/rcx/...".
(0011 x86-gpr32-name?
  (0010 (name)
    (x86-gpr64-name? name)))

(0011 x86-gpr32?
  (0010 (operand)
    (110
      
      ((010 operand)  (001 ()))
      ((101 (100 operand) (001 gpr32))
       (110
         
         ((010 (011 operand))  (001 ()))
         ((101 (011 (011 operand)) (001 ()))
          (x86-gpr32-name? (1001 operand)))
         ))
      )))

(0011 x86-gpr32
  (0010 (name)
    (110
      ((x86-gpr32-name? name) (1110 (001 gpr32) name))
      ((010 ()) (x86-machine-operand-rejection (001 gpr32) name)))))

(0011 x86-as-gpr32
  (0010 (operand)
    (110
      ((x86-machine-rejected? operand) operand)
      ((x86-gpr32? operand) operand)
      ((010 ()) (x86-gpr32 operand)))))

(0011 x86-gpr32-value
  (0010 (operand)
    (1001 operand)))

; XMM is a separate register class even though encoding uses the same 4-bit
; ModR/M namespace width. Validity is projected from x86-xmm-reg-code so this
; typed layer does not become a second XMM number table.
(0011 x86-xmm-name?
  (0010 (name)
    (110
      ((110101100 name)
       (110
         ((101 (x86-xmm-reg-code name) (001 ()))
          (010 (001 (00000000))))
         ((101 (x86-xmm-reg-code name) (x86-xmm-reg-code name))
          (010 ()))
         ((010 ()) (010 (001 (00000000))))))
      ((010 ()) (010 (001 (00000000)))))))
(0011 x86-xmm?
  (0010 (operand)
    (110
      
      ((010 operand)  (001 ()))
      ((101 (100 operand) (001 xmm))
       (110
         
         ((010 (011 operand))  (001 ()))
         ((101 (011 (011 operand)) (001 ()))
          (x86-xmm-name? (1001 operand)))
         ))
      )))

(0011 x86-xmm
  (0010 (name)
    (110
      ((x86-xmm-name? name) (1110 (001 xmm) name))
      ((010 ()) (x86-machine-operand-rejection (001 xmm) name)))))

(0011 x86-as-xmm
  (0010 (operand)
    (110
      ((x86-machine-rejected? operand) operand)
      ((x86-xmm? operand) operand)
      ((010 ()) (x86-xmm operand)))))

(0011 x86-xmm-value
  (0010 (operand)
    (1001 operand)))

; Exact integer recognition stays in Lisp and does not require a new host
; `number?`/`integer?` primitive. Canonical exact Number identity is the
; #q2:<num>/<den> wire, independent of human presentation.  In reduced form
; an exact number is an integer exactly when its denominator is 1.
(0011 x86-wire-denominator-one?
  (0010 (text)
    (110
      ((110011100 text) (001 ()))
      ((101 (110101011 text) "/")
       (let ((rest (110011101 text)))
         (110
           ((110011100 rest) (001 ()))
           ((101 (110101011 rest) "1")
            (110
              ((110011100 (110011101 rest)) t)
              ((101 0 0) (001 ()))))
           ((101 0 0) (001 ())))))
      ((101 0 0) (x86-wire-denominator-one? (110011101 text))))))

(0011 x86-exact-integer?
  (0010 (value)
    (let ((wire (11110100 value)))
      (110
        ((110101010 "#q2:" wire) (x86-wire-denominator-one? wire))
        ((101 0 0) (001 ()))))))

(0011 x86-operand-in-inclusive-range?
  (0010 (value lower upper)
    ; Exact-Q comparisons answer 1 (так) / 0 (ні), and 0 is truthy -- so a
    ; bare `and` over comparison results accepted every operand, overflowing
    ; u64-imm/disp8 slots. E1 (#216): explicit expected-result domains,
    ; reduced to a t/() structural predicate so it is safe as a cond query.
    (110
      ((110110 value lower) 
        (110
          ((110100 value upper)  t)
          ))
      )))

(0011 x86-u64-imm?
  (0010 (operand)
    (110
      
      ((010 operand)  (001 ()))
      ((101 (100 operand) (001 u64-imm))
       (110
         
         ((010 (011 operand))  (001 ()))
         ((101 (011 (011 operand)) (001 ()))
          (let ((value (1001 operand)))
            (110
              ((x86-exact-integer? value)
               (x86-operand-in-inclusive-range? value 0 18446744073709551615))
              )))
         ))
      )))

(0011 x86-u64-imm
  (0010 (value)
    (110
      ((x86-exact-integer? value)
       (110
         ((x86-operand-in-inclusive-range? value 0 18446744073709551615)
          (1110 (001 u64-imm) value))
         ((010 ()) (x86-machine-operand-rejection (001 u64-imm) value))))
      ((010 ()) (x86-machine-operand-rejection (001 u64-imm) value)))))

(0011 x86-as-u64-imm
  (0010 (operand)
    (110
      ((x86-machine-rejected? operand) operand)
      ((x86-u64-imm? operand) operand)
      ((010 ()) (x86-u64-imm operand)))))

(0011 x86-u64-imm-value
  (0010 (operand)
    (1001 operand)))

(0011 x86-disp8?
  (0010 (operand)
    (110
      
      ((010 operand)  (001 ()))
      ((101 (100 operand) (001 disp8))
       (110
         
         ((010 (011 operand))  (001 ()))
         ((101 (011 (011 operand)) (001 ()))
          (let ((value (1001 operand)))
            (110
              ((x86-exact-integer? value)
               (x86-operand-in-inclusive-range? value -128 127))
              )))
         ))
      )))

(0011 x86-disp8
  (0010 (value)
    (110
      ((x86-exact-integer? value)
       (110
         ((x86-operand-in-inclusive-range? value -128 127)
          (1110 (001 disp8) value))
         ((010 ()) (x86-machine-operand-rejection (001 disp8) value))))
      ((010 ()) (x86-machine-operand-rejection (001 disp8) value)))))

(0011 x86-as-disp8
  (0010 (operand)
    (110
      ((x86-machine-rejected? operand) operand)
      ((x86-disp8? operand) operand)
      ((010 ()) (x86-disp8 operand)))))

(0011 x86-disp8-value
  (0010 (operand)
    (1001 operand)))

(0011 x86-mem64-disp8?
  (0010 (operand)
    (110
      
      ((010 operand)  (001 ()))
      ((101 (100 operand) (001 mem64-disp8))
       (110
         
         ((010 ()) (001 ()))
         
         ((010 (011 (011 operand)))  (001 ()))
         ((101 (011 (011 (011 operand))) (001 ()))
          (11110101 (x86-gpr64? (1001 operand))
               (x86-disp8? (10011 operand))))
         ))
      )))

(0011 x86-mem64-disp8
  (0010 (base displacement)
    (let ((typed-base (x86-as-gpr64 base)))
      (110
        ((x86-machine-rejected? typed-base) typed-base)
        ((010 ())
         (let ((typed-displacement (x86-as-disp8 displacement)))
           (110
             ((x86-machine-rejected? typed-displacement) typed-displacement)
             ((010 ())
              (1110 (001 mem64-disp8)
                    typed-base
                    typed-displacement)))))))))

(0011 x86-as-mem64-disp8
  (0010 (operand)
    (110
      ((x86-machine-rejected? operand) operand)
      ((x86-mem64-disp8? operand) operand)
      ((010 ()) (x86-machine-operand-rejection (001 mem64-disp8) operand)))))

(0011 x86-mem64-disp8-base
  (0010 (operand)
    (x86-gpr64-value (1001 operand))))

(0011 x86-mem64-disp8-displacement
  (0010 (operand)
    (x86-disp8-value (10011 operand))))
