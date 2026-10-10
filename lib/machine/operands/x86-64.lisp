; #177 — typed x86-64 machine operands as Lisp-owned data.
;
; This layer owns operand *shape*, not instruction admission and not encoding.
; Register knowledge is intentionally reused from x86-reg-code in the existing
; Lisp encoder so this file cannot become a second GPR table. A well-typed
; operand may still participate in an instruction form that #176 admission
; rejects; type success is not capability/admission success.

(00001001 x86-machine-operand-rejection
  (00001000 (expected actual)
    (00100111 (00000001 rejected) (00000001 machine-operand) expected actual)))

(00001001 x86-machine-rejected?
  (00001000 (value)
    (110
      
      ((010 value)  (00000001 ()))
      ((011 (101 value) (00000001 rejected)) t)
      )))

(00001001 x86-gpr8-name?
  (00001000 (name)
    (110
      ((00100011 name)
       (00101100
         name
         (00000001
           (al cl dl bl spl bpl sil dil
               r8b r9b r10b r11b r12b r13b r14b r15b))))
      )))

(00001001 x86-gpr64-name?
  (00001000 (name)
    (110
      ((00100011 name)
       (10011010
         (00100001 (011 (x86-reg-code name) (00000001 ())))
         (00100001 (x86-gpr8-name? name))))
      )))

(00001001 x86-gpr8?
  (00001000 (operand)
    (110
      
      ((010 operand)  (00000001 ()))
      ((011 (101 operand) (00000001 gpr8))
       (110
         
         ((010 (111 operand))  (00000001 ()))
         ((00100010 (111 (111 operand)) (00000001 ()))
          (x86-gpr8-name? (00101111 operand)))
         ))
      )))

(00001001 x86-gpr8
  (00001000 (name)
    (110
      ((x86-gpr8-name? name) (00100111 (00000001 gpr8) name))
      ((010 ()) (x86-machine-operand-rejection (00000001 gpr8) name)))))

(00001001 x86-as-gpr8
  (00001000 (operand)
    (110
      ((x86-machine-rejected? operand) operand)
      ((x86-gpr8? operand) operand)
      ((010 ()) (x86-gpr8 operand)))))

(00001001 x86-gpr8-value
  (00001000 (operand)
    (00101111 operand)))

(00001001 x86-gpr64?
  (00001000 (operand)
    (110
      
      ((010 operand)  (00000001 ()))
      ((011 (101 operand) (00000001 gpr64))
       (110
         
         ((010 (111 operand))  (00000001 ()))
         ((00100010 (111 (111 operand)) (00000001 ()))
          (x86-gpr64-name? (00101111 operand)))
         ))
      )))

(00001001 x86-gpr64
  (00001000 (name)
    (110
      ((x86-gpr64-name? name) (00100111 (00000001 gpr64) name))
      ((010 ()) (x86-machine-operand-rejection (00000001 gpr64) name)))))

(00001001 x86-as-gpr64
  (00001000 (operand)
    (110
      ((x86-machine-rejected? operand) operand)
      ((x86-gpr64? operand) operand)
      ((010 ()) (x86-gpr64 operand)))))

(00001001 x86-gpr64-value
  (00001000 (operand)
    (00101111 operand)))

; A gpr32 operand is a 32-bit view of the same physical general-purpose
; register named by its canonical 64-bit base name. The encoder already owns
; the physical register-code mapping and the instruction form owns width, so
; this typed view deliberately does not introduce a second eax/ecx/... code
; table merely to say "lower 32 bits of rax/rcx/...".
(00001001 x86-gpr32-name?
  (00001000 (name)
    (x86-gpr64-name? name)))

(00001001 x86-gpr32?
  (00001000 (operand)
    (110
      
      ((010 operand)  (00000001 ()))
      ((011 (101 operand) (00000001 gpr32))
       (110
         
         ((010 (111 operand))  (00000001 ()))
         ((00100010 (111 (111 operand)) (00000001 ()))
          (x86-gpr32-name? (00101111 operand)))
         ))
      )))

(00001001 x86-gpr32
  (00001000 (name)
    (110
      ((x86-gpr32-name? name) (00100111 (00000001 gpr32) name))
      ((010 ()) (x86-machine-operand-rejection (00000001 gpr32) name)))))

(00001001 x86-as-gpr32
  (00001000 (operand)
    (110
      ((x86-machine-rejected? operand) operand)
      ((x86-gpr32? operand) operand)
      ((010 ()) (x86-gpr32 operand)))))

(00001001 x86-gpr32-value
  (00001000 (operand)
    (00101111 operand)))

; XMM is a separate register class even though encoding uses the same 4-bit
; ModR/M namespace width. Validity is projected from x86-xmm-reg-code so this
; typed layer does not become a second XMM number table.
(00001001 x86-xmm-name?
  (00001000 (name)
    (110
      ((00100011 name)
       (110
         ((00100010 (x86-xmm-reg-code name) (00000001 ()))
          (010 (00000001 (00000000))))
         ((00100010 (x86-xmm-reg-code name) (x86-xmm-reg-code name))
          (010 ()))
         ((010 ()) (010 (00000001 (00000000))))))
      ((010 ()) (010 (00000001 (00000000)))))))
(00001001 x86-xmm?
  (00001000 (operand)
    (110
      
      ((010 operand)  (00000001 ()))
      ((011 (101 operand) (00000001 xmm))
       (110
         
         ((010 (111 operand))  (00000001 ()))
         ((00100010 (111 (111 operand)) (00000001 ()))
          (x86-xmm-name? (00101111 operand)))
         ))
      )))

(00001001 x86-xmm
  (00001000 (name)
    (110
      ((x86-xmm-name? name) (00100111 (00000001 xmm) name))
      ((010 ()) (x86-machine-operand-rejection (00000001 xmm) name)))))

(00001001 x86-as-xmm
  (00001000 (operand)
    (110
      ((x86-machine-rejected? operand) operand)
      ((x86-xmm? operand) operand)
      ((010 ()) (x86-xmm operand)))))

(00001001 x86-xmm-value
  (00001000 (operand)
    (00101111 operand)))

; Exact integer recognition stays in Lisp and does not require a new host
; `number?`/`integer?` primitive. Canonical exact Number identity is the
; #q2:<num>/<den> wire, independent of human presentation.  In reduced form
; an exact number is an integer exactly when its denominator is 1.
(00001001 x86-wire-denominator-one?
  (00001000 (text)
    (110
      ((00111100 text) (00000001 ()))
      ((011 (00111111 text) "/")
       (let ((rest (01000000 text)))
         (110
           ((00111100 rest) (00000001 ()))
           ((011 (00111111 rest) "1")
            (110
              ((00111100 (01000000 rest)) t)
              ((011 0 0) (00000001 ()))))
           ((011 0 0) (00000001 ())))))
      ((011 0 0) (x86-wire-denominator-one? (01000000 text))))))

(00001001 x86-exact-integer?
  (00001000 (value)
    (let ((wire (01001100 value)))
      (110
        ((00111101 "#q2:" wire) (x86-wire-denominator-one? wire))
        ((011 0 0) (00000001 ()))))))

(00001001 x86-operand-in-inclusive-range?
  (00001000 (value lower upper)
    ; Exact-Q comparisons answer 1 (так) / 0 (ні), and 0 is truthy -- so a
    ; bare `and` over comparison results accepted every operand, overflowing
    ; u64-imm/disp8 slots. E1 (#216): explicit expected-result domains,
    ; reduced to a t/() structural predicate so it is safe as a cond query.
    (110
      ((00011110 value lower) 
        (110
          ((00011101 value upper)  t)
          ))
      )))

(00001001 x86-u64-imm?
  (00001000 (operand)
    (110
      
      ((010 operand)  (00000001 ()))
      ((011 (101 operand) (00000001 u64-imm))
       (110
         
         ((010 (111 operand))  (00000001 ()))
         ((00100010 (111 (111 operand)) (00000001 ()))
          (let ((value (00101111 operand)))
            (110
              ((x86-exact-integer? value)
               (x86-operand-in-inclusive-range? value 0 18446744073709551615))
              )))
         ))
      )))

(00001001 x86-u64-imm
  (00001000 (value)
    (110
      ((x86-exact-integer? value)
       (110
         ((x86-operand-in-inclusive-range? value 0 18446744073709551615)
          (00100111 (00000001 u64-imm) value))
         ((010 ()) (x86-machine-operand-rejection (00000001 u64-imm) value))))
      ((010 ()) (x86-machine-operand-rejection (00000001 u64-imm) value)))))

(00001001 x86-as-u64-imm
  (00001000 (operand)
    (110
      ((x86-machine-rejected? operand) operand)
      ((x86-u64-imm? operand) operand)
      ((010 ()) (x86-u64-imm operand)))))

(00001001 x86-u64-imm-value
  (00001000 (operand)
    (00101111 operand)))

(00001001 x86-disp8?
  (00001000 (operand)
    (110
      
      ((010 operand)  (00000001 ()))
      ((011 (101 operand) (00000001 disp8))
       (110
         
         ((010 (111 operand))  (00000001 ()))
         ((00100010 (111 (111 operand)) (00000001 ()))
          (let ((value (00101111 operand)))
            (110
              ((x86-exact-integer? value)
               (x86-operand-in-inclusive-range? value -128 127))
              )))
         ))
      )))

(00001001 x86-disp8
  (00001000 (value)
    (110
      ((x86-exact-integer? value)
       (110
         ((x86-operand-in-inclusive-range? value -128 127)
          (00100111 (00000001 disp8) value))
         ((010 ()) (x86-machine-operand-rejection (00000001 disp8) value))))
      ((010 ()) (x86-machine-operand-rejection (00000001 disp8) value)))))

(00001001 x86-as-disp8
  (00001000 (operand)
    (110
      ((x86-machine-rejected? operand) operand)
      ((x86-disp8? operand) operand)
      ((010 ()) (x86-disp8 operand)))))

(00001001 x86-disp8-value
  (00001000 (operand)
    (00101111 operand)))

(00001001 x86-mem64-disp8?
  (00001000 (operand)
    (110
      
      ((010 operand)  (00000001 ()))
      ((011 (101 operand) (00000001 mem64-disp8))
       (110
         
         ((010 ()) (00000001 ()))
         
         ((010 (111 (111 operand)))  (00000001 ()))
         ((00100010 (111 (111 (111 operand))) (00000001 ()))
          (10011010 (x86-gpr64? (00101111 operand))
               (x86-disp8? (00110000 operand))))
         ))
      )))

(00001001 x86-mem64-disp8
  (00001000 (base displacement)
    (let ((typed-base (x86-as-gpr64 base)))
      (110
        ((x86-machine-rejected? typed-base) typed-base)
        ((010 ())
         (let ((typed-displacement (x86-as-disp8 displacement)))
           (110
             ((x86-machine-rejected? typed-displacement) typed-displacement)
             ((010 ())
              (00100111 (00000001 mem64-disp8)
                    typed-base
                    typed-displacement)))))))))

(00001001 x86-as-mem64-disp8
  (00001000 (operand)
    (110
      ((x86-machine-rejected? operand) operand)
      ((x86-mem64-disp8? operand) operand)
      ((010 ()) (x86-machine-operand-rejection (00000001 mem64-disp8) operand)))))

(00001001 x86-mem64-disp8-base
  (00001000 (operand)
    (x86-gpr64-value (00101111 operand))))

(00001001 x86-mem64-disp8-displacement
  (00001000 (operand)
    (x86-disp8-value (00110000 operand))))
