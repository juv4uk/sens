; #177 — thin x86-64 machine atoms over the structured forms admitted by #176.
; These constructors own composition only. They intentionally contain no
; opcodes, byte strings, register-code tables, or CPU feature tables.
;
; Raw operands remain accepted for compatibility with the first #177 slice,
; but are normalized through the typed operand layer before a machine form is
; constructed. Operand typing does not grant instruction admission.

(визначити x86-ret
  (функція ()
    (як-є (ret))))

(визначити x86-mov-r64-imm64
  (функція (register immediate)
    ((функція (typed-register) (за-умовою
        ((x86-machine-rejected? typed-register) typed-register)
        ((атом? ())
         ((функція (typed-immediate) (за-умовою
             ((x86-machine-rejected? typed-immediate) typed-immediate)
             ((атом? ())
              (список (як-є mov-r64-imm64)
                    (x86-gpr64-value typed-register)
                    (x86-u64-imm-value typed-immediate))))) (x86-as-u64-imm immediate))))) (x86-as-gpr64 register))))

(визначити x86-add-r64-r64
  (функція (destination source)
    ((функція (typed-destination) (за-умовою
        ((x86-machine-rejected? typed-destination) typed-destination)
        ((атом? ())
         ((функція (typed-source) (за-умовою
             ((x86-machine-rejected? typed-source) typed-source)
             ((атом? ())
              (список (як-є add-r64-r64)
                    (x86-gpr64-value typed-destination)
                    (x86-gpr64-value typed-source))))) (x86-as-gpr64 source))))) (x86-as-gpr64 destination))))

(визначити x86-binary-gpr64-form
  (функція (mnemonic destination source)
    ((функція (typed-destination) (за-умовою
        ((x86-machine-rejected? typed-destination) typed-destination)
        ((атом? ())
         ((функція (typed-source) (за-умовою
             ((x86-machine-rejected? typed-source) typed-source)
             ((атом? ())
              (список mnemonic
                    (x86-gpr64-value typed-destination)
                    (x86-gpr64-value typed-source))))) (x86-as-gpr64 source))))) (x86-as-gpr64 destination))))

(визначити x86-or-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є or-r64-r64) destination source)))

(визначити x86-and-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є and-r64-r64) destination source)))

(визначити x86-sub-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є sub-r64-r64) destination source)))

(визначити x86-xor-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є xor-r64-r64) destination source)))

(визначити x86-cmp-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmp-r64-r64) destination source)))

; #196 bounded conditional-growth slice. The Jcc encoding/admission fact is
; already owned by #202. This atom owns only typed composition of the one
; conditional-transfer family demanded by the bounded EQ+COND witness.
(визначити x86-jnz-rel8
  (функція (displacement)
    ((функція (typed-displacement) (за-умовою
        ((x86-machine-rejected? typed-displacement) typed-displacement)
        ((атом? ())
         (список
           (як-є jnz-rel8)
           (x86-disp8-value typed-displacement))))) (x86-as-disp8 displacement))))

(визначити x86-unary-gpr64-form
  (функція (mnemonic register)
    ((функція (typed-register) (за-умовою
        ((x86-machine-rejected? typed-register) typed-register)
        ((атом? ())
         (список mnemonic (x86-gpr64-value typed-register))))) (x86-as-gpr64 register))))

(визначити x86-push-r64
  (функція (register)
    (x86-unary-gpr64-form (як-є push-r64) register)))

(визначити x86-pop-r64
  (функція (register)
    (x86-unary-gpr64-form (як-є pop-r64) register)))

(визначити x86-inc-r64
  (функція (register)
    (x86-unary-gpr64-form (як-є inc-r64) register)))

(визначити x86-dec-r64
  (функція (register)
    (x86-unary-gpr64-form (як-є dec-r64) register)))

(визначити x86-mov-mem64-r64
  (функція (memory source)
    ((функція (typed-memory) (за-умовою
        ((x86-machine-rejected? typed-memory) typed-memory)
        ((атом? ())
         ((функція (typed-source) (за-умовою
             ((x86-machine-rejected? typed-source) typed-source)
             ((атом? ())
              (список (як-є mov-mem-disp8-r64)
                    (x86-mem64-disp8-base typed-memory)
                    (x86-mem64-disp8-displacement typed-memory)
                    (x86-gpr64-value typed-source))))) (x86-as-gpr64 source))))) (x86-as-mem64-disp8 memory))))

(визначити x86-mov-r64-mem64
  (функція (destination memory)
    ((функція (typed-destination) (за-умовою
        ((x86-machine-rejected? typed-destination) typed-destination)
        ((атом? ())
         ((функція (typed-memory) (за-умовою
             ((x86-machine-rejected? typed-memory) typed-memory)
             ((атом? ())
              (список (як-є mov-r64-mem-disp8)
                    (x86-gpr64-value typed-destination)
                    (x86-mem64-disp8-base typed-memory)
                    (x86-mem64-disp8-displacement typed-memory))))) (x86-as-mem64-disp8 memory))))) (x86-as-gpr64 destination))))

; Compatibility constructors for the first #177 foundation. They now pass
; through typed memory/register validation and project back to the canonical
; #176-native forms.
(визначити x86-mov-mem-disp8-r64
  (функція (base displacement source)
    ((функція (memory) (за-умовою
        ((x86-machine-rejected? memory) memory)
        ((атом? ()) (x86-mov-mem64-r64 memory source)))) (x86-mem64-disp8 base displacement))))

(визначити x86-mov-r64-mem-disp8
  (функція (destination base displacement)
    ((функція (memory) (за-умовою
        ((x86-machine-rejected? memory) memory)
        ((атом? ()) (x86-mov-r64-mem64 destination memory)))) (x86-mem64-disp8 base displacement))))

; #178 — composable atoms for register/implicit forms that #176 already
; admits and encodes. These constructors reuse typed GPR/memory operands and
; contain no opcode/REX/ModR/M facts. Byte operations use explicit gpr8;
; MOVSXD uses an explicit gpr32 view; ordinary operations remain gpr64.

(визначити x86-mov-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є mov-r64-r64) destination source)))

(визначити x86-test-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є test-r64-r64) destination source)))

(визначити x86-imul-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є imul-r64-r64) destination source)))

(визначити x86-not-r64
  (функція (register)
    (x86-unary-gpr64-form (як-є not-r64) register)))

(визначити x86-neg-r64
  (функція (register)
    (x86-unary-gpr64-form (як-є neg-r64) register)))

(визначити x86-idiv-r64
  (функція (register)
    (x86-unary-gpr64-form (як-є idiv-r64) register)))

(визначити x86-call-r64
  (функція (register)
    (x86-unary-gpr64-form (як-є call-r64) register)))

(визначити x86-jmp-r64
  (функція (register)
    (x86-unary-gpr64-form (як-є jmp-r64) register)))

(визначити x86-cqo
  (функція ()
    (як-є (cqo))))

(визначити x86-unary-gpr8-form
  (функція (mnemonic register)
    ((функція (typed-register) (за-умовою
        ((x86-machine-rejected? typed-register) typed-register)
        ((атом? ())
         (список mnemonic (x86-gpr8-value typed-register))))) (x86-as-gpr8 register))))

(визначити x86-gpr64-gpr8-form
  (функція (mnemonic destination source)
    ((функція (typed-destination) (за-умовою
        ((x86-machine-rejected? typed-destination) typed-destination)
        ((атом? ())
         ((функція (typed-source) (за-умовою
             ((x86-machine-rejected? typed-source) typed-source)
             ((атом? ())
              (список mnemonic
                    (x86-gpr64-value typed-destination)
                    (x86-gpr8-value typed-source))))) (x86-as-gpr8 source))))) (x86-as-gpr64 destination))))

(визначити x86-gpr64-gpr32-form
  (функція (mnemonic destination source)
    ((функція (typed-destination) (за-умовою
        ((x86-machine-rejected? typed-destination) typed-destination)
        ((атом? ())
         ((функція (typed-source) (за-умовою
             ((x86-machine-rejected? typed-source) typed-source)
             ((атом? ())
              (список mnemonic
                    (x86-gpr64-value typed-destination)
                    (x86-gpr32-value typed-source))))) (x86-as-gpr32 source))))) (x86-as-gpr64 destination))))

(визначити x86-seto-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є seto-r8) register)))

(визначити x86-setno-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є setno-r8) register)))

(визначити x86-setb-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є setb-r8) register)))

(визначити x86-setc-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є setc-r8) register)))

(визначити x86-setnb-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є setnb-r8) register)))

(визначити x86-setnc-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є setnc-r8) register)))

(визначити x86-setae-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є setae-r8) register)))

(визначити x86-setz-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є setz-r8) register)))

(визначити x86-sete-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є sete-r8) register)))

(визначити x86-setnz-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є setnz-r8) register)))

(визначити x86-setne-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є setne-r8) register)))

(визначити x86-setbe-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є setbe-r8) register)))

(визначити x86-setna-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є setna-r8) register)))

(визначити x86-setnbe-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є setnbe-r8) register)))

(визначити x86-seta-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є seta-r8) register)))

(визначити x86-sets-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є sets-r8) register)))

(визначити x86-setns-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є setns-r8) register)))

(визначити x86-setp-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є setp-r8) register)))

(визначити x86-setpe-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є setpe-r8) register)))

(визначити x86-setnp-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є setnp-r8) register)))

(визначити x86-setpo-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є setpo-r8) register)))

(визначити x86-setl-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є setl-r8) register)))

(визначити x86-setnge-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є setnge-r8) register)))

(визначити x86-setnl-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є setnl-r8) register)))

(визначити x86-setge-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є setge-r8) register)))

(визначити x86-setle-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є setle-r8) register)))

(визначити x86-setng-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є setng-r8) register)))

(визначити x86-setnle-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є setnle-r8) register)))

(визначити x86-setg-r8
  (функція (register)
    (x86-unary-gpr8-form (як-є setg-r8) register)))

(визначити x86-movzx-r64-r8
  (функція (destination source)
    (x86-gpr64-gpr8-form (як-є movzx-r64-r8) destination source)))

(визначити x86-movsx-r64-r8
  (функція (destination source)
    (x86-gpr64-gpr8-form (як-є movsx-r64-r8) destination source)))

(визначити x86-movsxd-r64-r32
  (функція (destination source)
    (x86-gpr64-gpr32-form (як-є movsxd-r64-r32) destination source)))

(визначити x86-cmovo-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmovo-r64-r64) destination source)))

(визначити x86-cmovno-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmovno-r64-r64) destination source)))

(визначити x86-cmovb-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmovb-r64-r64) destination source)))

(визначити x86-cmovc-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmovc-r64-r64) destination source)))

(визначити x86-cmovnb-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmovnb-r64-r64) destination source)))

(визначити x86-cmovnc-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmovnc-r64-r64) destination source)))

(визначити x86-cmovae-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmovae-r64-r64) destination source)))

(визначити x86-cmovz-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmovz-r64-r64) destination source)))

(визначити x86-cmove-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmove-r64-r64) destination source)))

(визначити x86-cmovnz-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmovnz-r64-r64) destination source)))

(визначити x86-cmovne-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmovne-r64-r64) destination source)))

(визначити x86-cmovbe-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmovbe-r64-r64) destination source)))

(визначити x86-cmovna-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmovna-r64-r64) destination source)))

(визначити x86-cmovnbe-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmovnbe-r64-r64) destination source)))

(визначити x86-cmova-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmova-r64-r64) destination source)))

(визначити x86-cmovs-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmovs-r64-r64) destination source)))

(визначити x86-cmovns-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmovns-r64-r64) destination source)))

(визначити x86-cmovp-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmovp-r64-r64) destination source)))

(визначити x86-cmovpe-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmovpe-r64-r64) destination source)))

(визначити x86-cmovnp-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmovnp-r64-r64) destination source)))

(визначити x86-cmovpo-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmovpo-r64-r64) destination source)))

(визначити x86-cmovl-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmovl-r64-r64) destination source)))

(визначити x86-cmovnge-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmovnge-r64-r64) destination source)))

(визначити x86-cmovnl-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmovnl-r64-r64) destination source)))

(визначити x86-cmovge-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmovge-r64-r64) destination source)))

(визначити x86-cmovle-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmovle-r64-r64) destination source)))

(визначити x86-cmovng-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmovng-r64-r64) destination source)))

(визначити x86-cmovnle-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmovnle-r64-r64) destination source)))

(визначити x86-cmovg-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є cmovg-r64-r64) destination source)))

(визначити x86-nop
  (функція ()
    (як-є (nop))))

(визначити x86-bt-r64-r64
  (функція (base index)
    (x86-binary-gpr64-form (як-є bt-r64-r64) base index)))

(визначити x86-popcnt-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є popcnt-r64-r64) destination source)))

(визначити x86-tzcnt-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є tzcnt-r64-r64) destination source)))

(визначити x86-bsf-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є bsf-r64-r64) destination source)))

(визначити x86-bsr-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form (як-є bsr-r64-r64) destination source)))

(визначити x86-bswap-r64
  (функція (register)
    (x86-unary-gpr64-form (як-є bswap-r64) register)))

(визначити x86-xchg-r64-r64
  (функція (left right)
    (x86-binary-gpr64-form (як-є xchg-r64-r64) left right)))

(визначити x86-cld (функція () (як-є (cld))))
(визначити x86-std (функція () (як-є (std))))
(визначити x86-stosq (функція () (як-є (stosq))))
(визначити x86-rep-stosq (функція () (як-є (rep-stosq))))
(визначити x86-stosb (функція () (як-є (stosb))))
(визначити x86-rep-stosb (функція () (як-є (rep-stosb))))
(визначити x86-movsq (функція () (як-є (movsq))))
(визначити x86-rep-movsq (функція () (як-є (rep-movsq))))
(визначити x86-movsb (функція () (як-є (movsb))))
(визначити x86-rep-movsb (функція () (як-є (rep-movsb))))

(визначити x86-lea-r64-mem64
  (функція (destination memory)
    ((функція (typed-destination) (за-умовою
        ((x86-machine-rejected? typed-destination) typed-destination)
        ((атом? ())
         ((функція (typed-memory) (за-умовою
             ((x86-machine-rejected? typed-memory) typed-memory)
             ((атом? ())
              (список (як-є lea-r64-mem-disp8)
                    (x86-gpr64-value typed-destination)
                    (x86-mem64-disp8-base typed-memory)
                    (x86-mem64-disp8-displacement typed-memory))))) (x86-as-mem64-disp8 memory))))) (x86-as-gpr64 destination))))

(визначити x86-lea-r64-mem-disp8
  (функція (destination base displacement)
    ((функція (memory) (за-умовою
        ((x86-machine-rejected? memory) memory)
        ((атом? ()) (x86-lea-r64-mem64 destination memory)))) (x86-mem64-disp8 base displacement))))

; Current admitted XMM and late #176 forms. These atoms own only typed
; composition; prefix/opcode/ModR/M facts remain in encoding/x86-64.lisp.

(визначити x86-binary-xmm-form
  (функція (mnemonic destination source)
    ((функція (typed-destination) (за-умовою
        ((x86-machine-rejected? typed-destination) typed-destination)
        ((атом? ())
         ((функція (typed-source) (за-умовою
             ((x86-machine-rejected? typed-source) typed-source)
             ((атом? ())
              (список mnemonic
                    (x86-xmm-value typed-destination)
                    (x86-xmm-value typed-source))))) (x86-as-xmm source))))) (x86-as-xmm destination))))

(визначити x86-xmm-gpr64-form
  (функція (mnemonic destination source)
    ((функція (typed-destination) (за-умовою
        ((x86-machine-rejected? typed-destination) typed-destination)
        ((атом? ())
         ((функція (typed-source) (за-умовою
             ((x86-machine-rejected? typed-source) typed-source)
             ((атом? ())
              (список mnemonic
                    (x86-xmm-value typed-destination)
                    (x86-gpr64-value typed-source))))) (x86-as-gpr64 source))))) (x86-as-xmm destination))))

(визначити x86-gpr64-xmm-form
  (функція (mnemonic destination source)
    ((функція (typed-destination) (за-умовою
        ((x86-machine-rejected? typed-destination) typed-destination)
        ((атом? ())
         ((функція (typed-source) (за-умовою
             ((x86-machine-rejected? typed-source) typed-source)
             ((атом? ())
              (список mnemonic
                    (x86-gpr64-value typed-destination)
                    (x86-xmm-value typed-source))))) (x86-as-xmm source))))) (x86-as-gpr64 destination))))

(визначити x86-rdtsc (функція () (як-є (rdtsc))))

(визначити x86-cmpxchg-r64-r64
  (функція (destination source)
    (x86-binary-gpr64-form
      (як-є cmpxchg-r64-r64)
      destination
      source)))

(визначити x86-movsd-xmm-xmm
  (функція (destination source)
    (x86-binary-xmm-form (як-є movsd-xmm-xmm) destination source)))
(визначити x86-addsd-xmm-xmm
  (функція (destination source)
    (x86-binary-xmm-form (як-є addsd-xmm-xmm) destination source)))
(визначити x86-subsd-xmm-xmm
  (функція (destination source)
    (x86-binary-xmm-form (як-є subsd-xmm-xmm) destination source)))
(визначити x86-mulsd-xmm-xmm
  (функція (destination source)
    (x86-binary-xmm-form (як-є mulsd-xmm-xmm) destination source)))
(визначити x86-divsd-xmm-xmm
  (функція (destination source)
    (x86-binary-xmm-form (як-є divsd-xmm-xmm) destination source)))
(визначити x86-sqrtsd-xmm-xmm
  (функція (destination source)
    (x86-binary-xmm-form (як-є sqrtsd-xmm-xmm) destination source)))
(визначити x86-maxsd-xmm-xmm
  (функція (destination source)
    (x86-binary-xmm-form (як-є maxsd-xmm-xmm) destination source)))
(визначити x86-minsd-xmm-xmm
  (функція (destination source)
    (x86-binary-xmm-form (як-є minsd-xmm-xmm) destination source)))
(визначити x86-ucomisd-xmm-xmm
  (функція (left right)
    (x86-binary-xmm-form (як-є ucomisd-xmm-xmm) left right)))
(визначити x86-xorpd-xmm-xmm
  (функція (destination source)
    (x86-binary-xmm-form (як-є xorpd-xmm-xmm) destination source)))

(визначити x86-cvtsi2sd-xmm-r64
  (функція (destination source)
    (x86-xmm-gpr64-form
      (як-є cvtsi2sd-xmm-r64)
      destination
      source)))
(визначити x86-cvttsd2si-r64-xmm
  (функція (destination source)
    (x86-gpr64-xmm-form
      (як-є cvttsd2si-r64-xmm)
      destination
      source)))
(визначити x86-movq-xmm-r64
  (функція (destination source)
    (x86-xmm-gpr64-form
      (як-є movq-xmm-r64)
      destination
      source)))
(визначити x86-movq-r64-xmm
  (функція (destination source)
    (x86-gpr64-xmm-form
      (як-є movq-r64-xmm)
      destination
      source)))

(визначити x86-encode-machine-block
  (функція (block)
    (x86-encode-admitted-program-or-reject (форми-машинного-блоку block))))
