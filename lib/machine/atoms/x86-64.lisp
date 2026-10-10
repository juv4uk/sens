; #177 — thin x86-64 machine atoms over the structured forms admitted by #176.
; These constructors own composition only. They intentionally contain no
; opcodes, byte strings, register-code tables, or CPU feature tables.
;
; Raw operands remain accepted for compatibility with the first #177 slice,
; but are normalized through the typed operand layer before a machine form is
; constructed. Operand typing does not grant instruction admission.

(00001001 x86-ret
  (00001000 ()
    (00000001 (ret))))

(00001001 x86-mov-r64-imm64
  (00001000 (register immediate)
    (10011100 ((typed-register (x86-as-gpr64 register)))
      (00000111
        ((x86-machine-rejected? typed-register) typed-register)
        ((00000010 ())
         (10011100 ((typed-immediate (x86-as-u64-imm immediate)))
           (00000111
             ((x86-machine-rejected? typed-immediate) typed-immediate)
             ((00000010 ())
              (00100111 (00000001 mov-r64-imm64)
                    (x86-gpr64-value typed-register)
                    (x86-u64-imm-value typed-immediate))))))))))

(00001001 x86-add-r64-r64
  (00001000 (destination source)
    (10011100 ((typed-destination (x86-as-gpr64 destination)))
      (00000111
        ((x86-machine-rejected? typed-destination) typed-destination)
        ((00000010 ())
         (10011100 ((typed-source (x86-as-gpr64 source)))
           (00000111
             ((x86-machine-rejected? typed-source) typed-source)
             ((00000010 ())
              (00100111 (00000001 add-r64-r64)
                    (x86-gpr64-value typed-destination)
                    (x86-gpr64-value typed-source))))))))))

(00001001 x86-binary-gpr64-form
  (00001000 (mnemonic destination source)
    (10011100 ((typed-destination (x86-as-gpr64 destination)))
      (00000111
        ((x86-machine-rejected? typed-destination) typed-destination)
        ((00000010 ())
         (10011100 ((typed-source (x86-as-gpr64 source)))
           (00000111
             ((x86-machine-rejected? typed-source) typed-source)
             ((00000010 ())
              (00100111 mnemonic
                    (x86-gpr64-value typed-destination)
                    (x86-gpr64-value typed-source))))))))))

(00001001 x86-or-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 or-r64-r64) destination source)))

(00001001 x86-and-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 and-r64-r64) destination source)))

(00001001 x86-sub-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 sub-r64-r64) destination source)))

(00001001 x86-xor-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 xor-r64-r64) destination source)))

(00001001 x86-cmp-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmp-r64-r64) destination source)))

; #196 bounded conditional-growth slice. The Jcc encoding/admission fact is
; already owned by #202. This atom owns only typed composition of the one
; conditional-transfer family demanded by the bounded EQ+COND witness.
(00001001 x86-jnz-rel8
  (00001000 (displacement)
    (10011100 ((typed-displacement (x86-as-disp8 displacement)))
      (00000111
        ((x86-machine-rejected? typed-displacement) typed-displacement)
        ((00000010 ())
         (00100111
           (00000001 jnz-rel8)
           (x86-disp8-value typed-displacement)))))))

(00001001 x86-unary-gpr64-form
  (00001000 (mnemonic register)
    (10011100 ((typed-register (x86-as-gpr64 register)))
      (00000111
        ((x86-machine-rejected? typed-register) typed-register)
        ((00000010 ())
         (00100111 mnemonic (x86-gpr64-value typed-register)))))))

(00001001 x86-push-r64
  (00001000 (register)
    (x86-unary-gpr64-form (00000001 push-r64) register)))

(00001001 x86-pop-r64
  (00001000 (register)
    (x86-unary-gpr64-form (00000001 pop-r64) register)))

(00001001 x86-inc-r64
  (00001000 (register)
    (x86-unary-gpr64-form (00000001 inc-r64) register)))

(00001001 x86-dec-r64
  (00001000 (register)
    (x86-unary-gpr64-form (00000001 dec-r64) register)))

(00001001 x86-mov-mem64-r64
  (00001000 (memory source)
    (10011100 ((typed-memory (x86-as-mem64-disp8 memory)))
      (00000111
        ((x86-machine-rejected? typed-memory) typed-memory)
        ((00000010 ())
         (10011100 ((typed-source (x86-as-gpr64 source)))
           (00000111
             ((x86-machine-rejected? typed-source) typed-source)
             ((00000010 ())
              (00100111 (00000001 mov-mem-disp8-r64)
                    (x86-mem64-disp8-base typed-memory)
                    (x86-mem64-disp8-displacement typed-memory)
                    (x86-gpr64-value typed-source))))))))))

(00001001 x86-mov-r64-mem64
  (00001000 (destination memory)
    (10011100 ((typed-destination (x86-as-gpr64 destination)))
      (00000111
        ((x86-machine-rejected? typed-destination) typed-destination)
        ((00000010 ())
         (10011100 ((typed-memory (x86-as-mem64-disp8 memory)))
           (00000111
             ((x86-machine-rejected? typed-memory) typed-memory)
             ((00000010 ())
              (00100111 (00000001 mov-r64-mem-disp8)
                    (x86-gpr64-value typed-destination)
                    (x86-mem64-disp8-base typed-memory)
                    (x86-mem64-disp8-displacement typed-memory))))))))))

; Compatibility constructors for the first #177 foundation. They now pass
; through typed memory/register validation and project back to the canonical
; #176-native forms.
(00001001 x86-mov-mem-disp8-r64
  (00001000 (base displacement source)
    (10011100 ((memory (x86-mem64-disp8 base displacement)))
      (00000111
        ((x86-machine-rejected? memory) memory)
        ((00000010 ()) (x86-mov-mem64-r64 memory source))))))

(00001001 x86-mov-r64-mem-disp8
  (00001000 (destination base displacement)
    (10011100 ((memory (x86-mem64-disp8 base displacement)))
      (00000111
        ((x86-machine-rejected? memory) memory)
        ((00000010 ()) (x86-mov-r64-mem64 destination memory))))))

; #178 — composable atoms for register/implicit forms that #176 already
; admits and encodes. These constructors reuse typed GPR/memory operands and
; contain no opcode/REX/ModR/M facts. Byte operations use explicit gpr8;
; MOVSXD uses an explicit gpr32 view; ordinary operations remain gpr64.

(00001001 x86-mov-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 mov-r64-r64) destination source)))

(00001001 x86-test-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 test-r64-r64) destination source)))

(00001001 x86-imul-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 imul-r64-r64) destination source)))

(00001001 x86-not-r64
  (00001000 (register)
    (x86-unary-gpr64-form (00000001 not-r64) register)))

(00001001 x86-neg-r64
  (00001000 (register)
    (x86-unary-gpr64-form (00000001 neg-r64) register)))

(00001001 x86-idiv-r64
  (00001000 (register)
    (x86-unary-gpr64-form (00000001 idiv-r64) register)))

(00001001 x86-call-r64
  (00001000 (register)
    (x86-unary-gpr64-form (00000001 call-r64) register)))

(00001001 x86-jmp-r64
  (00001000 (register)
    (x86-unary-gpr64-form (00000001 jmp-r64) register)))

(00001001 x86-cqo
  (00001000 ()
    (00000001 (cqo))))

(00001001 x86-unary-gpr8-form
  (00001000 (mnemonic register)
    (10011100 ((typed-register (x86-as-gpr8 register)))
      (00000111
        ((x86-machine-rejected? typed-register) typed-register)
        ((00000010 ())
         (00100111 mnemonic (x86-gpr8-value typed-register)))))))

(00001001 x86-gpr64-gpr8-form
  (00001000 (mnemonic destination source)
    (10011100 ((typed-destination (x86-as-gpr64 destination)))
      (00000111
        ((x86-machine-rejected? typed-destination) typed-destination)
        ((00000010 ())
         (10011100 ((typed-source (x86-as-gpr8 source)))
           (00000111
             ((x86-machine-rejected? typed-source) typed-source)
             ((00000010 ())
              (00100111 mnemonic
                    (x86-gpr64-value typed-destination)
                    (x86-gpr8-value typed-source))))))))))

(00001001 x86-gpr64-gpr32-form
  (00001000 (mnemonic destination source)
    (10011100 ((typed-destination (x86-as-gpr64 destination)))
      (00000111
        ((x86-machine-rejected? typed-destination) typed-destination)
        ((00000010 ())
         (10011100 ((typed-source (x86-as-gpr32 source)))
           (00000111
             ((x86-machine-rejected? typed-source) typed-source)
             ((00000010 ())
              (00100111 mnemonic
                    (x86-gpr64-value typed-destination)
                    (x86-gpr32-value typed-source))))))))))

(00001001 x86-seto-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 seto-r8) register)))

(00001001 x86-setno-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 setno-r8) register)))

(00001001 x86-setb-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 setb-r8) register)))

(00001001 x86-setc-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 setc-r8) register)))

(00001001 x86-setnb-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 setnb-r8) register)))

(00001001 x86-setnc-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 setnc-r8) register)))

(00001001 x86-setae-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 setae-r8) register)))

(00001001 x86-setz-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 setz-r8) register)))

(00001001 x86-sete-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 sete-r8) register)))

(00001001 x86-setnz-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 setnz-r8) register)))

(00001001 x86-setne-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 setne-r8) register)))

(00001001 x86-setbe-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 setbe-r8) register)))

(00001001 x86-setna-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 setna-r8) register)))

(00001001 x86-setnbe-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 setnbe-r8) register)))

(00001001 x86-seta-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 seta-r8) register)))

(00001001 x86-sets-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 sets-r8) register)))

(00001001 x86-setns-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 setns-r8) register)))

(00001001 x86-setp-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 setp-r8) register)))

(00001001 x86-setpe-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 setpe-r8) register)))

(00001001 x86-setnp-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 setnp-r8) register)))

(00001001 x86-setpo-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 setpo-r8) register)))

(00001001 x86-setl-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 setl-r8) register)))

(00001001 x86-setnge-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 setnge-r8) register)))

(00001001 x86-setnl-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 setnl-r8) register)))

(00001001 x86-setge-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 setge-r8) register)))

(00001001 x86-setle-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 setle-r8) register)))

(00001001 x86-setng-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 setng-r8) register)))

(00001001 x86-setnle-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 setnle-r8) register)))

(00001001 x86-setg-r8
  (00001000 (register)
    (x86-unary-gpr8-form (00000001 setg-r8) register)))

(00001001 x86-movzx-r64-r8
  (00001000 (destination source)
    (x86-gpr64-gpr8-form (00000001 movzx-r64-r8) destination source)))

(00001001 x86-movsx-r64-r8
  (00001000 (destination source)
    (x86-gpr64-gpr8-form (00000001 movsx-r64-r8) destination source)))

(00001001 x86-movsxd-r64-r32
  (00001000 (destination source)
    (x86-gpr64-gpr32-form (00000001 movsxd-r64-r32) destination source)))

(00001001 x86-cmovo-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmovo-r64-r64) destination source)))

(00001001 x86-cmovno-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmovno-r64-r64) destination source)))

(00001001 x86-cmovb-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmovb-r64-r64) destination source)))

(00001001 x86-cmovc-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmovc-r64-r64) destination source)))

(00001001 x86-cmovnb-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmovnb-r64-r64) destination source)))

(00001001 x86-cmovnc-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmovnc-r64-r64) destination source)))

(00001001 x86-cmovae-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmovae-r64-r64) destination source)))

(00001001 x86-cmovz-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmovz-r64-r64) destination source)))

(00001001 x86-cmove-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmove-r64-r64) destination source)))

(00001001 x86-cmovnz-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmovnz-r64-r64) destination source)))

(00001001 x86-cmovne-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmovne-r64-r64) destination source)))

(00001001 x86-cmovbe-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmovbe-r64-r64) destination source)))

(00001001 x86-cmovna-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmovna-r64-r64) destination source)))

(00001001 x86-cmovnbe-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmovnbe-r64-r64) destination source)))

(00001001 x86-cmova-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmova-r64-r64) destination source)))

(00001001 x86-cmovs-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmovs-r64-r64) destination source)))

(00001001 x86-cmovns-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmovns-r64-r64) destination source)))

(00001001 x86-cmovp-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmovp-r64-r64) destination source)))

(00001001 x86-cmovpe-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmovpe-r64-r64) destination source)))

(00001001 x86-cmovnp-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmovnp-r64-r64) destination source)))

(00001001 x86-cmovpo-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmovpo-r64-r64) destination source)))

(00001001 x86-cmovl-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmovl-r64-r64) destination source)))

(00001001 x86-cmovnge-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmovnge-r64-r64) destination source)))

(00001001 x86-cmovnl-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmovnl-r64-r64) destination source)))

(00001001 x86-cmovge-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmovge-r64-r64) destination source)))

(00001001 x86-cmovle-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmovle-r64-r64) destination source)))

(00001001 x86-cmovng-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmovng-r64-r64) destination source)))

(00001001 x86-cmovnle-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmovnle-r64-r64) destination source)))

(00001001 x86-cmovg-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 cmovg-r64-r64) destination source)))

(00001001 x86-nop
  (00001000 ()
    (00000001 (nop))))

(00001001 x86-bt-r64-r64
  (00001000 (base index)
    (x86-binary-gpr64-form (00000001 bt-r64-r64) base index)))

(00001001 x86-popcnt-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 popcnt-r64-r64) destination source)))

(00001001 x86-tzcnt-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 tzcnt-r64-r64) destination source)))

(00001001 x86-bsf-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 bsf-r64-r64) destination source)))

(00001001 x86-bsr-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form (00000001 bsr-r64-r64) destination source)))

(00001001 x86-bswap-r64
  (00001000 (register)
    (x86-unary-gpr64-form (00000001 bswap-r64) register)))

(00001001 x86-xchg-r64-r64
  (00001000 (left right)
    (x86-binary-gpr64-form (00000001 xchg-r64-r64) left right)))

(00001001 x86-cld (00001000 () (00000001 (cld))))
(00001001 x86-std (00001000 () (00000001 (std))))
(00001001 x86-stosq (00001000 () (00000001 (stosq))))
(00001001 x86-rep-stosq (00001000 () (00000001 (rep-stosq))))
(00001001 x86-stosb (00001000 () (00000001 (stosb))))
(00001001 x86-rep-stosb (00001000 () (00000001 (rep-stosb))))
(00001001 x86-movsq (00001000 () (00000001 (movsq))))
(00001001 x86-rep-movsq (00001000 () (00000001 (rep-movsq))))
(00001001 x86-movsb (00001000 () (00000001 (movsb))))
(00001001 x86-rep-movsb (00001000 () (00000001 (rep-movsb))))

(00001001 x86-lea-r64-mem64
  (00001000 (destination memory)
    (10011100 ((typed-destination (x86-as-gpr64 destination)))
      (00000111
        ((x86-machine-rejected? typed-destination) typed-destination)
        ((00000010 ())
         (10011100 ((typed-memory (x86-as-mem64-disp8 memory)))
           (00000111
             ((x86-machine-rejected? typed-memory) typed-memory)
             ((00000010 ())
              (00100111 (00000001 lea-r64-mem-disp8)
                    (x86-gpr64-value typed-destination)
                    (x86-mem64-disp8-base typed-memory)
                    (x86-mem64-disp8-displacement typed-memory))))))))))

(00001001 x86-lea-r64-mem-disp8
  (00001000 (destination base displacement)
    (10011100 ((memory (x86-mem64-disp8 base displacement)))
      (00000111
        ((x86-machine-rejected? memory) memory)
        ((00000010 ()) (x86-lea-r64-mem64 destination memory))))))

; Current admitted XMM and late #176 forms. These atoms own only typed
; composition; prefix/opcode/ModR/M facts remain in encoding/x86-64.lisp.

(00001001 x86-binary-xmm-form
  (00001000 (mnemonic destination source)
    (10011100 ((typed-destination (x86-as-xmm destination)))
      (00000111
        ((x86-machine-rejected? typed-destination) typed-destination)
        ((00000010 ())
         (10011100 ((typed-source (x86-as-xmm source)))
           (00000111
             ((x86-machine-rejected? typed-source) typed-source)
             ((00000010 ())
              (00100111 mnemonic
                    (x86-xmm-value typed-destination)
                    (x86-xmm-value typed-source))))))))))

(00001001 x86-xmm-gpr64-form
  (00001000 (mnemonic destination source)
    (10011100 ((typed-destination (x86-as-xmm destination)))
      (00000111
        ((x86-machine-rejected? typed-destination) typed-destination)
        ((00000010 ())
         (10011100 ((typed-source (x86-as-gpr64 source)))
           (00000111
             ((x86-machine-rejected? typed-source) typed-source)
             ((00000010 ())
              (00100111 mnemonic
                    (x86-xmm-value typed-destination)
                    (x86-gpr64-value typed-source))))))))))

(00001001 x86-gpr64-xmm-form
  (00001000 (mnemonic destination source)
    (10011100 ((typed-destination (x86-as-gpr64 destination)))
      (00000111
        ((x86-machine-rejected? typed-destination) typed-destination)
        ((00000010 ())
         (10011100 ((typed-source (x86-as-xmm source)))
           (00000111
             ((x86-machine-rejected? typed-source) typed-source)
             ((00000010 ())
              (00100111 mnemonic
                    (x86-gpr64-value typed-destination)
                    (x86-xmm-value typed-source))))))))))

(00001001 x86-rdtsc (00001000 () (00000001 (rdtsc))))

(00001001 x86-cmpxchg-r64-r64
  (00001000 (destination source)
    (x86-binary-gpr64-form
      (00000001 cmpxchg-r64-r64)
      destination
      source)))

(00001001 x86-movsd-xmm-xmm
  (00001000 (destination source)
    (x86-binary-xmm-form (00000001 movsd-xmm-xmm) destination source)))
(00001001 x86-addsd-xmm-xmm
  (00001000 (destination source)
    (x86-binary-xmm-form (00000001 addsd-xmm-xmm) destination source)))
(00001001 x86-subsd-xmm-xmm
  (00001000 (destination source)
    (x86-binary-xmm-form (00000001 subsd-xmm-xmm) destination source)))
(00001001 x86-mulsd-xmm-xmm
  (00001000 (destination source)
    (x86-binary-xmm-form (00000001 mulsd-xmm-xmm) destination source)))
(00001001 x86-divsd-xmm-xmm
  (00001000 (destination source)
    (x86-binary-xmm-form (00000001 divsd-xmm-xmm) destination source)))
(00001001 x86-sqrtsd-xmm-xmm
  (00001000 (destination source)
    (x86-binary-xmm-form (00000001 sqrtsd-xmm-xmm) destination source)))
(00001001 x86-maxsd-xmm-xmm
  (00001000 (destination source)
    (x86-binary-xmm-form (00000001 maxsd-xmm-xmm) destination source)))
(00001001 x86-minsd-xmm-xmm
  (00001000 (destination source)
    (x86-binary-xmm-form (00000001 minsd-xmm-xmm) destination source)))
(00001001 x86-ucomisd-xmm-xmm
  (00001000 (left right)
    (x86-binary-xmm-form (00000001 ucomisd-xmm-xmm) left right)))
(00001001 x86-xorpd-xmm-xmm
  (00001000 (destination source)
    (x86-binary-xmm-form (00000001 xorpd-xmm-xmm) destination source)))

(00001001 x86-cvtsi2sd-xmm-r64
  (00001000 (destination source)
    (x86-xmm-gpr64-form
      (00000001 cvtsi2sd-xmm-r64)
      destination
      source)))
(00001001 x86-cvttsd2si-r64-xmm
  (00001000 (destination source)
    (x86-gpr64-xmm-form
      (00000001 cvttsd2si-r64-xmm)
      destination
      source)))
(00001001 x86-movq-xmm-r64
  (00001000 (destination source)
    (x86-xmm-gpr64-form
      (00000001 movq-xmm-r64)
      destination
      source)))
(00001001 x86-movq-r64-xmm
  (00001000 (destination source)
    (x86-gpr64-xmm-form
      (00000001 movq-r64-xmm)
      destination
      source)))

(00001001 x86-encode-machine-block
  (00001000 (block)
    (x86-encode-admitted-program-or-reject (machine-block-forms block))))
