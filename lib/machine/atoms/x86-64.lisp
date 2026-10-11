; #177 — thin x86-64 machine atoms over the structured forms admitted by #176.
; These constructors own composition only. They intentionally contain no
; opcodes, byte strings, register-code tables, or CPU feature tables.
;
; Raw operands remain accepted for compatibility with the first #177 slice,
; but are normalized through the typed operand layer before a machine form is
; constructed. Operand typing does not grant instruction admission.

(0011 x86-ret
  (0010 ()
    (001 (ret))))

(0011 x86-mov-r64-imm64
  (0010 (register immediate)
    (001000 ((typed-register (x86-as-gpr64 register)))
      (110
        ((x86-machine-rejected? typed-register) typed-register)
        ((010 ())
         (001000 ((typed-immediate (x86-as-u64-imm immediate)))
           (110
             ((x86-machine-rejected? typed-immediate) typed-immediate)
             ((010 ())
              (1110 (001 mov-r64-imm64)
                    (x86-gpr64-value typed-register)
                    (x86-u64-imm-value typed-immediate))))))))))

(0011 x86-add-r64-r64
  (0010 (destination source)
    (001000 ((typed-destination (x86-as-gpr64 destination)))
      (110
        ((x86-machine-rejected? typed-destination) typed-destination)
        ((010 ())
         (001000 ((typed-source (x86-as-gpr64 source)))
           (110
             ((x86-machine-rejected? typed-source) typed-source)
             ((010 ())
              (1110 (001 add-r64-r64)
                    (x86-gpr64-value typed-destination)
                    (x86-gpr64-value typed-source))))))))))

(0011 x86-binary-gpr64-form
  (0010 (mnemonic destination source)
    (001000 ((typed-destination (x86-as-gpr64 destination)))
      (110
        ((x86-machine-rejected? typed-destination) typed-destination)
        ((010 ())
         (001000 ((typed-source (x86-as-gpr64 source)))
           (110
             ((x86-machine-rejected? typed-source) typed-source)
             ((010 ())
              (1110 mnemonic
                    (x86-gpr64-value typed-destination)
                    (x86-gpr64-value typed-source))))))))))

(0011 x86-or-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 or-r64-r64) destination source)))

(0011 x86-and-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 and-r64-r64) destination source)))

(0011 x86-sub-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 sub-r64-r64) destination source)))

(0011 x86-xor-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 xor-r64-r64) destination source)))

(0011 x86-cmp-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmp-r64-r64) destination source)))

; #196 bounded conditional-growth slice. The Jcc encoding/admission fact is
; already owned by #202. This atom owns only typed composition of the one
; conditional-transfer family demanded by the bounded EQ+COND witness.
(0011 x86-jnz-rel8
  (0010 (displacement)
    (001000 ((typed-displacement (x86-as-disp8 displacement)))
      (110
        ((x86-machine-rejected? typed-displacement) typed-displacement)
        ((010 ())
         (1110
           (001 jnz-rel8)
           (x86-disp8-value typed-displacement)))))))

(0011 x86-unary-gpr64-form
  (0010 (mnemonic register)
    (001000 ((typed-register (x86-as-gpr64 register)))
      (110
        ((x86-machine-rejected? typed-register) typed-register)
        ((010 ())
         (1110 mnemonic (x86-gpr64-value typed-register)))))))

(0011 x86-push-r64
  (0010 (register)
    (x86-unary-gpr64-form (001 push-r64) register)))

(0011 x86-pop-r64
  (0010 (register)
    (x86-unary-gpr64-form (001 pop-r64) register)))

(0011 x86-inc-r64
  (0010 (register)
    (x86-unary-gpr64-form (001 inc-r64) register)))

(0011 x86-dec-r64
  (0010 (register)
    (x86-unary-gpr64-form (001 dec-r64) register)))

(0011 x86-mov-mem64-r64
  (0010 (memory source)
    (001000 ((typed-memory (x86-as-mem64-disp8 memory)))
      (110
        ((x86-machine-rejected? typed-memory) typed-memory)
        ((010 ())
         (001000 ((typed-source (x86-as-gpr64 source)))
           (110
             ((x86-machine-rejected? typed-source) typed-source)
             ((010 ())
              (1110 (001 mov-mem-disp8-r64)
                    (x86-mem64-disp8-base typed-memory)
                    (x86-mem64-disp8-displacement typed-memory)
                    (x86-gpr64-value typed-source))))))))))

(0011 x86-mov-r64-mem64
  (0010 (destination memory)
    (001000 ((typed-destination (x86-as-gpr64 destination)))
      (110
        ((x86-machine-rejected? typed-destination) typed-destination)
        ((010 ())
         (001000 ((typed-memory (x86-as-mem64-disp8 memory)))
           (110
             ((x86-machine-rejected? typed-memory) typed-memory)
             ((010 ())
              (1110 (001 mov-r64-mem-disp8)
                    (x86-gpr64-value typed-destination)
                    (x86-mem64-disp8-base typed-memory)
                    (x86-mem64-disp8-displacement typed-memory))))))))))

; Compatibility constructors for the first #177 foundation. They now pass
; through typed memory/register validation and project back to the canonical
; #176-native forms.
(0011 x86-mov-mem-disp8-r64
  (0010 (base displacement source)
    (001000 ((memory (x86-mem64-disp8 base displacement)))
      (110
        ((x86-machine-rejected? memory) memory)
        ((010 ()) (x86-mov-mem64-r64 memory source))))))

(0011 x86-mov-r64-mem-disp8
  (0010 (destination base displacement)
    (001000 ((memory (x86-mem64-disp8 base displacement)))
      (110
        ((x86-machine-rejected? memory) memory)
        ((010 ()) (x86-mov-r64-mem64 destination memory))))))

; #178 — composable atoms for register/implicit forms that #176 already
; admits and encodes. These constructors reuse typed GPR/memory operands and
; contain no opcode/REX/ModR/M facts. Byte operations use explicit gpr8;
; MOVSXD uses an explicit gpr32 view; ordinary operations remain gpr64.

(0011 x86-mov-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 mov-r64-r64) destination source)))

(0011 x86-test-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 test-r64-r64) destination source)))

(0011 x86-imul-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 imul-r64-r64) destination source)))

(0011 x86-not-r64
  (0010 (register)
    (x86-unary-gpr64-form (001 not-r64) register)))

(0011 x86-neg-r64
  (0010 (register)
    (x86-unary-gpr64-form (001 neg-r64) register)))

(0011 x86-idiv-r64
  (0010 (register)
    (x86-unary-gpr64-form (001 idiv-r64) register)))

(0011 x86-call-r64
  (0010 (register)
    (x86-unary-gpr64-form (001 call-r64) register)))

(0011 x86-jmp-r64
  (0010 (register)
    (x86-unary-gpr64-form (001 jmp-r64) register)))

(0011 x86-cqo
  (0010 ()
    (001 (cqo))))

(0011 x86-unary-gpr8-form
  (0010 (mnemonic register)
    (001000 ((typed-register (x86-as-gpr8 register)))
      (110
        ((x86-machine-rejected? typed-register) typed-register)
        ((010 ())
         (1110 mnemonic (x86-gpr8-value typed-register)))))))

(0011 x86-gpr64-gpr8-form
  (0010 (mnemonic destination source)
    (001000 ((typed-destination (x86-as-gpr64 destination)))
      (110
        ((x86-machine-rejected? typed-destination) typed-destination)
        ((010 ())
         (001000 ((typed-source (x86-as-gpr8 source)))
           (110
             ((x86-machine-rejected? typed-source) typed-source)
             ((010 ())
              (1110 mnemonic
                    (x86-gpr64-value typed-destination)
                    (x86-gpr8-value typed-source))))))))))

(0011 x86-gpr64-gpr32-form
  (0010 (mnemonic destination source)
    (001000 ((typed-destination (x86-as-gpr64 destination)))
      (110
        ((x86-machine-rejected? typed-destination) typed-destination)
        ((010 ())
         (001000 ((typed-source (x86-as-gpr32 source)))
           (110
             ((x86-machine-rejected? typed-source) typed-source)
             ((010 ())
              (1110 mnemonic
                    (x86-gpr64-value typed-destination)
                    (x86-gpr32-value typed-source))))))))))

(0011 x86-seto-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 seto-r8) register)))

(0011 x86-setno-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 setno-r8) register)))

(0011 x86-setb-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 setb-r8) register)))

(0011 x86-setc-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 setc-r8) register)))

(0011 x86-setnb-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 setnb-r8) register)))

(0011 x86-setnc-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 setnc-r8) register)))

(0011 x86-setae-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 setae-r8) register)))

(0011 x86-setz-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 setz-r8) register)))

(0011 x86-sete-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 sete-r8) register)))

(0011 x86-setnz-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 setnz-r8) register)))

(0011 x86-setne-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 setne-r8) register)))

(0011 x86-setbe-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 setbe-r8) register)))

(0011 x86-setna-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 setna-r8) register)))

(0011 x86-setnbe-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 setnbe-r8) register)))

(0011 x86-seta-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 seta-r8) register)))

(0011 x86-sets-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 sets-r8) register)))

(0011 x86-setns-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 setns-r8) register)))

(0011 x86-setp-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 setp-r8) register)))

(0011 x86-setpe-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 setpe-r8) register)))

(0011 x86-setnp-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 setnp-r8) register)))

(0011 x86-setpo-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 setpo-r8) register)))

(0011 x86-setl-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 setl-r8) register)))

(0011 x86-setnge-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 setnge-r8) register)))

(0011 x86-setnl-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 setnl-r8) register)))

(0011 x86-setge-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 setge-r8) register)))

(0011 x86-setle-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 setle-r8) register)))

(0011 x86-setng-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 setng-r8) register)))

(0011 x86-setnle-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 setnle-r8) register)))

(0011 x86-setg-r8
  (0010 (register)
    (x86-unary-gpr8-form (001 setg-r8) register)))

(0011 x86-movzx-r64-r8
  (0010 (destination source)
    (x86-gpr64-gpr8-form (001 movzx-r64-r8) destination source)))

(0011 x86-movsx-r64-r8
  (0010 (destination source)
    (x86-gpr64-gpr8-form (001 movsx-r64-r8) destination source)))

(0011 x86-movsxd-r64-r32
  (0010 (destination source)
    (x86-gpr64-gpr32-form (001 movsxd-r64-r32) destination source)))

(0011 x86-cmovo-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmovo-r64-r64) destination source)))

(0011 x86-cmovno-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmovno-r64-r64) destination source)))

(0011 x86-cmovb-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmovb-r64-r64) destination source)))

(0011 x86-cmovc-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmovc-r64-r64) destination source)))

(0011 x86-cmovnb-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmovnb-r64-r64) destination source)))

(0011 x86-cmovnc-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmovnc-r64-r64) destination source)))

(0011 x86-cmovae-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmovae-r64-r64) destination source)))

(0011 x86-cmovz-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmovz-r64-r64) destination source)))

(0011 x86-cmove-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmove-r64-r64) destination source)))

(0011 x86-cmovnz-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmovnz-r64-r64) destination source)))

(0011 x86-cmovne-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmovne-r64-r64) destination source)))

(0011 x86-cmovbe-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmovbe-r64-r64) destination source)))

(0011 x86-cmovna-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmovna-r64-r64) destination source)))

(0011 x86-cmovnbe-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmovnbe-r64-r64) destination source)))

(0011 x86-cmova-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmova-r64-r64) destination source)))

(0011 x86-cmovs-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmovs-r64-r64) destination source)))

(0011 x86-cmovns-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmovns-r64-r64) destination source)))

(0011 x86-cmovp-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmovp-r64-r64) destination source)))

(0011 x86-cmovpe-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmovpe-r64-r64) destination source)))

(0011 x86-cmovnp-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmovnp-r64-r64) destination source)))

(0011 x86-cmovpo-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmovpo-r64-r64) destination source)))

(0011 x86-cmovl-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmovl-r64-r64) destination source)))

(0011 x86-cmovnge-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmovnge-r64-r64) destination source)))

(0011 x86-cmovnl-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmovnl-r64-r64) destination source)))

(0011 x86-cmovge-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmovge-r64-r64) destination source)))

(0011 x86-cmovle-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmovle-r64-r64) destination source)))

(0011 x86-cmovng-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmovng-r64-r64) destination source)))

(0011 x86-cmovnle-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmovnle-r64-r64) destination source)))

(0011 x86-cmovg-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 cmovg-r64-r64) destination source)))

(0011 x86-nop
  (0010 ()
    (001 (nop))))

(0011 x86-bt-r64-r64
  (0010 (base index)
    (x86-binary-gpr64-form (001 bt-r64-r64) base index)))

(0011 x86-popcnt-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 popcnt-r64-r64) destination source)))

(0011 x86-tzcnt-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 tzcnt-r64-r64) destination source)))

(0011 x86-bsf-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 bsf-r64-r64) destination source)))

(0011 x86-bsr-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form (001 bsr-r64-r64) destination source)))

(0011 x86-bswap-r64
  (0010 (register)
    (x86-unary-gpr64-form (001 bswap-r64) register)))

(0011 x86-xchg-r64-r64
  (0010 (left right)
    (x86-binary-gpr64-form (001 xchg-r64-r64) left right)))

(0011 x86-cld (0010 () (001 (cld))))
(0011 x86-std (0010 () (001 (std))))
(0011 x86-stosq (0010 () (001 (stosq))))
(0011 x86-rep-stosq (0010 () (001 (rep-stosq))))
(0011 x86-stosb (0010 () (001 (stosb))))
(0011 x86-rep-stosb (0010 () (001 (rep-stosb))))
(0011 x86-movsq (0010 () (001 (movsq))))
(0011 x86-rep-movsq (0010 () (001 (rep-movsq))))
(0011 x86-movsb (0010 () (001 (movsb))))
(0011 x86-rep-movsb (0010 () (001 (rep-movsb))))

(0011 x86-lea-r64-mem64
  (0010 (destination memory)
    (001000 ((typed-destination (x86-as-gpr64 destination)))
      (110
        ((x86-machine-rejected? typed-destination) typed-destination)
        ((010 ())
         (001000 ((typed-memory (x86-as-mem64-disp8 memory)))
           (110
             ((x86-machine-rejected? typed-memory) typed-memory)
             ((010 ())
              (1110 (001 lea-r64-mem-disp8)
                    (x86-gpr64-value typed-destination)
                    (x86-mem64-disp8-base typed-memory)
                    (x86-mem64-disp8-displacement typed-memory))))))))))

(0011 x86-lea-r64-mem-disp8
  (0010 (destination base displacement)
    (001000 ((memory (x86-mem64-disp8 base displacement)))
      (110
        ((x86-machine-rejected? memory) memory)
        ((010 ()) (x86-lea-r64-mem64 destination memory))))))

; Current admitted XMM and late #176 forms. These atoms own only typed
; composition; prefix/opcode/ModR/M facts remain in encoding/x86-64.lisp.

(0011 x86-binary-xmm-form
  (0010 (mnemonic destination source)
    (001000 ((typed-destination (x86-as-xmm destination)))
      (110
        ((x86-machine-rejected? typed-destination) typed-destination)
        ((010 ())
         (001000 ((typed-source (x86-as-xmm source)))
           (110
             ((x86-machine-rejected? typed-source) typed-source)
             ((010 ())
              (1110 mnemonic
                    (x86-xmm-value typed-destination)
                    (x86-xmm-value typed-source))))))))))

(0011 x86-xmm-gpr64-form
  (0010 (mnemonic destination source)
    (001000 ((typed-destination (x86-as-xmm destination)))
      (110
        ((x86-machine-rejected? typed-destination) typed-destination)
        ((010 ())
         (001000 ((typed-source (x86-as-gpr64 source)))
           (110
             ((x86-machine-rejected? typed-source) typed-source)
             ((010 ())
              (1110 mnemonic
                    (x86-xmm-value typed-destination)
                    (x86-gpr64-value typed-source))))))))))

(0011 x86-gpr64-xmm-form
  (0010 (mnemonic destination source)
    (001000 ((typed-destination (x86-as-gpr64 destination)))
      (110
        ((x86-machine-rejected? typed-destination) typed-destination)
        ((010 ())
         (001000 ((typed-source (x86-as-xmm source)))
           (110
             ((x86-machine-rejected? typed-source) typed-source)
             ((010 ())
              (1110 mnemonic
                    (x86-gpr64-value typed-destination)
                    (x86-xmm-value typed-source))))))))))

(0011 x86-rdtsc (0010 () (001 (rdtsc))))

(0011 x86-cmpxchg-r64-r64
  (0010 (destination source)
    (x86-binary-gpr64-form
      (001 cmpxchg-r64-r64)
      destination
      source)))

(0011 x86-movsd-xmm-xmm
  (0010 (destination source)
    (x86-binary-xmm-form (001 movsd-xmm-xmm) destination source)))
(0011 x86-addsd-xmm-xmm
  (0010 (destination source)
    (x86-binary-xmm-form (001 addsd-xmm-xmm) destination source)))
(0011 x86-subsd-xmm-xmm
  (0010 (destination source)
    (x86-binary-xmm-form (001 subsd-xmm-xmm) destination source)))
(0011 x86-mulsd-xmm-xmm
  (0010 (destination source)
    (x86-binary-xmm-form (001 mulsd-xmm-xmm) destination source)))
(0011 x86-divsd-xmm-xmm
  (0010 (destination source)
    (x86-binary-xmm-form (001 divsd-xmm-xmm) destination source)))
(0011 x86-sqrtsd-xmm-xmm
  (0010 (destination source)
    (x86-binary-xmm-form (001 sqrtsd-xmm-xmm) destination source)))
(0011 x86-maxsd-xmm-xmm
  (0010 (destination source)
    (x86-binary-xmm-form (001 maxsd-xmm-xmm) destination source)))
(0011 x86-minsd-xmm-xmm
  (0010 (destination source)
    (x86-binary-xmm-form (001 minsd-xmm-xmm) destination source)))
(0011 x86-ucomisd-xmm-xmm
  (0010 (left right)
    (x86-binary-xmm-form (001 ucomisd-xmm-xmm) left right)))
(0011 x86-xorpd-xmm-xmm
  (0010 (destination source)
    (x86-binary-xmm-form (001 xorpd-xmm-xmm) destination source)))

(0011 x86-cvtsi2sd-xmm-r64
  (0010 (destination source)
    (x86-xmm-gpr64-form
      (001 cvtsi2sd-xmm-r64)
      destination
      source)))
(0011 x86-cvttsd2si-r64-xmm
  (0010 (destination source)
    (x86-gpr64-xmm-form
      (001 cvttsd2si-r64-xmm)
      destination
      source)))
(0011 x86-movq-xmm-r64
  (0010 (destination source)
    (x86-xmm-gpr64-form
      (001 movq-xmm-r64)
      destination
      source)))
(0011 x86-movq-r64-xmm
  (0010 (destination source)
    (x86-gpr64-xmm-form
      (001 movq-r64-xmm)
      destination
      source)))

(0011 x86-encode-machine-block
  (0010 (block)
    (x86-encode-admitted-program-or-reject (machine-block-forms block))))
