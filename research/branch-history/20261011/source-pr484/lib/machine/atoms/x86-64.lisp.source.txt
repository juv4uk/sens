; #177 — thin x86-64 machine atoms over the structured forms admitted by #176.
; These constructors own composition only. They intentionally contain no
; opcodes, byte strings, register-code tables, or CPU feature tables.
;
; Raw operands remain accepted for compatibility with the first #177 slice,
; but are normalized through the typed operand layer before a machine form is
; constructed. Operand typing does not grant instruction admission.

(def x86-ret
  (lambda ()
    (quote (ret))))

(def x86-mov-r64-imm64
  (lambda (register immediate)
    (let ((typed-register (x86-as-gpr64 register)))
      (cond
        ((x86-machine-rejected? typed-register) typed-register)
        (t
         (let ((typed-immediate (x86-as-u64-imm immediate)))
           (cond
             ((x86-machine-rejected? typed-immediate) typed-immediate)
             (t
              (list (quote mov-r64-imm64)
                    (x86-gpr64-value typed-register)
                    (x86-u64-imm-value typed-immediate))))))))))

(def x86-add-r64-r64
  (lambda (destination source)
    (let ((typed-destination (x86-as-gpr64 destination)))
      (cond
        ((x86-machine-rejected? typed-destination) typed-destination)
        (t
         (let ((typed-source (x86-as-gpr64 source)))
           (cond
             ((x86-machine-rejected? typed-source) typed-source)
             (t
              (list (quote add-r64-r64)
                    (x86-gpr64-value typed-destination)
                    (x86-gpr64-value typed-source))))))))))

(def x86-binary-gpr64-form
  (lambda (mnemonic destination source)
    (let ((typed-destination (x86-as-gpr64 destination)))
      (cond
        ((x86-machine-rejected? typed-destination) typed-destination)
        (t
         (let ((typed-source (x86-as-gpr64 source)))
           (cond
             ((x86-machine-rejected? typed-source) typed-source)
             (t
              (list mnemonic
                    (x86-gpr64-value typed-destination)
                    (x86-gpr64-value typed-source))))))))))

(def x86-or-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote or-r64-r64) destination source)))

(def x86-and-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote and-r64-r64) destination source)))

(def x86-sub-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote sub-r64-r64) destination source)))

(def x86-xor-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote xor-r64-r64) destination source)))

(def x86-cmp-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmp-r64-r64) destination source)))

; #196 bounded conditional-growth slice. The Jcc encoding/admission fact is
; already owned by #202. This atom owns only typed composition of the one
; conditional-transfer family demanded by the bounded EQ+COND witness.
(def x86-jnz-rel8
  (lambda (displacement)
    (let ((typed-displacement (x86-as-disp8 displacement)))
      (cond
        ((x86-machine-rejected? typed-displacement) typed-displacement)
        (t
         (list
           (quote jnz-rel8)
           (x86-disp8-value typed-displacement)))))))

(def x86-unary-gpr64-form
  (lambda (mnemonic register)
    (let ((typed-register (x86-as-gpr64 register)))
      (cond
        ((x86-machine-rejected? typed-register) typed-register)
        (t
         (list mnemonic (x86-gpr64-value typed-register)))))))

(def x86-push-r64
  (lambda (register)
    (x86-unary-gpr64-form (quote push-r64) register)))

(def x86-pop-r64
  (lambda (register)
    (x86-unary-gpr64-form (quote pop-r64) register)))

(def x86-inc-r64
  (lambda (register)
    (x86-unary-gpr64-form (quote inc-r64) register)))

(def x86-dec-r64
  (lambda (register)
    (x86-unary-gpr64-form (quote dec-r64) register)))

(def x86-mov-mem64-r64
  (lambda (memory source)
    (let ((typed-memory (x86-as-mem64-disp8 memory)))
      (cond
        ((x86-machine-rejected? typed-memory) typed-memory)
        (t
         (let ((typed-source (x86-as-gpr64 source)))
           (cond
             ((x86-machine-rejected? typed-source) typed-source)
             (t
              (list (quote mov-mem-disp8-r64)
                    (x86-mem64-disp8-base typed-memory)
                    (x86-mem64-disp8-displacement typed-memory)
                    (x86-gpr64-value typed-source))))))))))

(def x86-mov-r64-mem64
  (lambda (destination memory)
    (let ((typed-destination (x86-as-gpr64 destination)))
      (cond
        ((x86-machine-rejected? typed-destination) typed-destination)
        (t
         (let ((typed-memory (x86-as-mem64-disp8 memory)))
           (cond
             ((x86-machine-rejected? typed-memory) typed-memory)
             (t
              (list (quote mov-r64-mem-disp8)
                    (x86-gpr64-value typed-destination)
                    (x86-mem64-disp8-base typed-memory)
                    (x86-mem64-disp8-displacement typed-memory))))))))))

; Compatibility constructors for the first #177 foundation. They now pass
; through typed memory/register validation and project back to the canonical
; #176-native forms.
(def x86-mov-mem-disp8-r64
  (lambda (base displacement source)
    (let ((memory (x86-mem64-disp8 base displacement)))
      (cond
        ((x86-machine-rejected? memory) memory)
        (t (x86-mov-mem64-r64 memory source))))))

(def x86-mov-r64-mem-disp8
  (lambda (destination base displacement)
    (let ((memory (x86-mem64-disp8 base displacement)))
      (cond
        ((x86-machine-rejected? memory) memory)
        (t (x86-mov-r64-mem64 destination memory))))))

; #178 — composable atoms for register/implicit forms that #176 already
; admits and encodes. These constructors reuse typed GPR/memory operands and
; contain no opcode/REX/ModR/M facts. Byte operations use explicit gpr8;
; MOVSXD uses an explicit gpr32 view; ordinary operations remain gpr64.

(def x86-mov-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote mov-r64-r64) destination source)))

(def x86-test-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote test-r64-r64) destination source)))

(def x86-imul-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote imul-r64-r64) destination source)))

(def x86-not-r64
  (lambda (register)
    (x86-unary-gpr64-form (quote not-r64) register)))

(def x86-neg-r64
  (lambda (register)
    (x86-unary-gpr64-form (quote neg-r64) register)))

(def x86-idiv-r64
  (lambda (register)
    (x86-unary-gpr64-form (quote idiv-r64) register)))

(def x86-call-r64
  (lambda (register)
    (x86-unary-gpr64-form (quote call-r64) register)))

(def x86-jmp-r64
  (lambda (register)
    (x86-unary-gpr64-form (quote jmp-r64) register)))

(def x86-cqo
  (lambda ()
    (quote (cqo))))

(def x86-unary-gpr8-form
  (lambda (mnemonic register)
    (let ((typed-register (x86-as-gpr8 register)))
      (cond
        ((x86-machine-rejected? typed-register) typed-register)
        (t
         (list mnemonic (x86-gpr8-value typed-register)))))))

(def x86-gpr64-gpr8-form
  (lambda (mnemonic destination source)
    (let ((typed-destination (x86-as-gpr64 destination)))
      (cond
        ((x86-machine-rejected? typed-destination) typed-destination)
        (t
         (let ((typed-source (x86-as-gpr8 source)))
           (cond
             ((x86-machine-rejected? typed-source) typed-source)
             (t
              (list mnemonic
                    (x86-gpr64-value typed-destination)
                    (x86-gpr8-value typed-source))))))))))

(def x86-gpr64-gpr32-form
  (lambda (mnemonic destination source)
    (let ((typed-destination (x86-as-gpr64 destination)))
      (cond
        ((x86-machine-rejected? typed-destination) typed-destination)
        (t
         (let ((typed-source (x86-as-gpr32 source)))
           (cond
             ((x86-machine-rejected? typed-source) typed-source)
             (t
              (list mnemonic
                    (x86-gpr64-value typed-destination)
                    (x86-gpr32-value typed-source))))))))))

(def x86-seto-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote seto-r8) register)))

(def x86-setno-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote setno-r8) register)))

(def x86-setb-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote setb-r8) register)))

(def x86-setc-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote setc-r8) register)))

(def x86-setnb-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote setnb-r8) register)))

(def x86-setnc-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote setnc-r8) register)))

(def x86-setae-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote setae-r8) register)))

(def x86-setz-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote setz-r8) register)))

(def x86-sete-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote sete-r8) register)))

(def x86-setnz-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote setnz-r8) register)))

(def x86-setne-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote setne-r8) register)))

(def x86-setbe-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote setbe-r8) register)))

(def x86-setna-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote setna-r8) register)))

(def x86-setnbe-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote setnbe-r8) register)))

(def x86-seta-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote seta-r8) register)))

(def x86-sets-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote sets-r8) register)))

(def x86-setns-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote setns-r8) register)))

(def x86-setp-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote setp-r8) register)))

(def x86-setpe-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote setpe-r8) register)))

(def x86-setnp-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote setnp-r8) register)))

(def x86-setpo-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote setpo-r8) register)))

(def x86-setl-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote setl-r8) register)))

(def x86-setnge-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote setnge-r8) register)))

(def x86-setnl-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote setnl-r8) register)))

(def x86-setge-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote setge-r8) register)))

(def x86-setle-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote setle-r8) register)))

(def x86-setng-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote setng-r8) register)))

(def x86-setnle-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote setnle-r8) register)))

(def x86-setg-r8
  (lambda (register)
    (x86-unary-gpr8-form (quote setg-r8) register)))

(def x86-movzx-r64-r8
  (lambda (destination source)
    (x86-gpr64-gpr8-form (quote movzx-r64-r8) destination source)))

(def x86-movsx-r64-r8
  (lambda (destination source)
    (x86-gpr64-gpr8-form (quote movsx-r64-r8) destination source)))

(def x86-movsxd-r64-r32
  (lambda (destination source)
    (x86-gpr64-gpr32-form (quote movsxd-r64-r32) destination source)))

(def x86-cmovo-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmovo-r64-r64) destination source)))

(def x86-cmovno-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmovno-r64-r64) destination source)))

(def x86-cmovb-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmovb-r64-r64) destination source)))

(def x86-cmovc-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmovc-r64-r64) destination source)))

(def x86-cmovnb-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmovnb-r64-r64) destination source)))

(def x86-cmovnc-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmovnc-r64-r64) destination source)))

(def x86-cmovae-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmovae-r64-r64) destination source)))

(def x86-cmovz-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmovz-r64-r64) destination source)))

(def x86-cmove-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmove-r64-r64) destination source)))

(def x86-cmovnz-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmovnz-r64-r64) destination source)))

(def x86-cmovne-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmovne-r64-r64) destination source)))

(def x86-cmovbe-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmovbe-r64-r64) destination source)))

(def x86-cmovna-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmovna-r64-r64) destination source)))

(def x86-cmovnbe-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmovnbe-r64-r64) destination source)))

(def x86-cmova-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmova-r64-r64) destination source)))

(def x86-cmovs-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmovs-r64-r64) destination source)))

(def x86-cmovns-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmovns-r64-r64) destination source)))

(def x86-cmovp-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmovp-r64-r64) destination source)))

(def x86-cmovpe-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmovpe-r64-r64) destination source)))

(def x86-cmovnp-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmovnp-r64-r64) destination source)))

(def x86-cmovpo-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmovpo-r64-r64) destination source)))

(def x86-cmovl-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmovl-r64-r64) destination source)))

(def x86-cmovnge-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmovnge-r64-r64) destination source)))

(def x86-cmovnl-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmovnl-r64-r64) destination source)))

(def x86-cmovge-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmovge-r64-r64) destination source)))

(def x86-cmovle-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmovle-r64-r64) destination source)))

(def x86-cmovng-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmovng-r64-r64) destination source)))

(def x86-cmovnle-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmovnle-r64-r64) destination source)))

(def x86-cmovg-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote cmovg-r64-r64) destination source)))

(def x86-nop
  (lambda ()
    (quote (nop))))

(def x86-bt-r64-r64
  (lambda (base index)
    (x86-binary-gpr64-form (quote bt-r64-r64) base index)))

(def x86-popcnt-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote popcnt-r64-r64) destination source)))

(def x86-tzcnt-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote tzcnt-r64-r64) destination source)))

(def x86-bsf-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote bsf-r64-r64) destination source)))

(def x86-bsr-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form (quote bsr-r64-r64) destination source)))

(def x86-bswap-r64
  (lambda (register)
    (x86-unary-gpr64-form (quote bswap-r64) register)))

(def x86-xchg-r64-r64
  (lambda (left right)
    (x86-binary-gpr64-form (quote xchg-r64-r64) left right)))

(def x86-cld (lambda () (quote (cld))))
(def x86-std (lambda () (quote (std))))
(def x86-stosq (lambda () (quote (stosq))))
(def x86-rep-stosq (lambda () (quote (rep-stosq))))
(def x86-stosb (lambda () (quote (stosb))))
(def x86-rep-stosb (lambda () (quote (rep-stosb))))
(def x86-movsq (lambda () (quote (movsq))))
(def x86-rep-movsq (lambda () (quote (rep-movsq))))
(def x86-movsb (lambda () (quote (movsb))))
(def x86-rep-movsb (lambda () (quote (rep-movsb))))

(def x86-lea-r64-mem64
  (lambda (destination memory)
    (let ((typed-destination (x86-as-gpr64 destination)))
      (cond
        ((x86-machine-rejected? typed-destination) typed-destination)
        (t
         (let ((typed-memory (x86-as-mem64-disp8 memory)))
           (cond
             ((x86-machine-rejected? typed-memory) typed-memory)
             (t
              (list (quote lea-r64-mem-disp8)
                    (x86-gpr64-value typed-destination)
                    (x86-mem64-disp8-base typed-memory)
                    (x86-mem64-disp8-displacement typed-memory))))))))))

(def x86-lea-r64-mem-disp8
  (lambda (destination base displacement)
    (let ((memory (x86-mem64-disp8 base displacement)))
      (cond
        ((x86-machine-rejected? memory) memory)
        (t (x86-lea-r64-mem64 destination memory))))))

; Current admitted XMM and late #176 forms. These atoms own only typed
; composition; prefix/opcode/ModR/M facts remain in encoding/x86-64.lisp.

(def x86-binary-xmm-form
  (lambda (mnemonic destination source)
    (let ((typed-destination (x86-as-xmm destination)))
      (cond
        ((x86-machine-rejected? typed-destination) typed-destination)
        (t
         (let ((typed-source (x86-as-xmm source)))
           (cond
             ((x86-machine-rejected? typed-source) typed-source)
             (t
              (list mnemonic
                    (x86-xmm-value typed-destination)
                    (x86-xmm-value typed-source))))))))))

(def x86-xmm-gpr64-form
  (lambda (mnemonic destination source)
    (let ((typed-destination (x86-as-xmm destination)))
      (cond
        ((x86-machine-rejected? typed-destination) typed-destination)
        (t
         (let ((typed-source (x86-as-gpr64 source)))
           (cond
             ((x86-machine-rejected? typed-source) typed-source)
             (t
              (list mnemonic
                    (x86-xmm-value typed-destination)
                    (x86-gpr64-value typed-source))))))))))

(def x86-gpr64-xmm-form
  (lambda (mnemonic destination source)
    (let ((typed-destination (x86-as-gpr64 destination)))
      (cond
        ((x86-machine-rejected? typed-destination) typed-destination)
        (t
         (let ((typed-source (x86-as-xmm source)))
           (cond
             ((x86-machine-rejected? typed-source) typed-source)
             (t
              (list mnemonic
                    (x86-gpr64-value typed-destination)
                    (x86-xmm-value typed-source))))))))))

(def x86-rdtsc (lambda () (quote (rdtsc))))

(def x86-cmpxchg-r64-r64
  (lambda (destination source)
    (x86-binary-gpr64-form
      (quote cmpxchg-r64-r64)
      destination
      source)))

(def x86-movsd-xmm-xmm
  (lambda (destination source)
    (x86-binary-xmm-form (quote movsd-xmm-xmm) destination source)))
(def x86-addsd-xmm-xmm
  (lambda (destination source)
    (x86-binary-xmm-form (quote addsd-xmm-xmm) destination source)))
(def x86-subsd-xmm-xmm
  (lambda (destination source)
    (x86-binary-xmm-form (quote subsd-xmm-xmm) destination source)))
(def x86-mulsd-xmm-xmm
  (lambda (destination source)
    (x86-binary-xmm-form (quote mulsd-xmm-xmm) destination source)))
(def x86-divsd-xmm-xmm
  (lambda (destination source)
    (x86-binary-xmm-form (quote divsd-xmm-xmm) destination source)))
(def x86-sqrtsd-xmm-xmm
  (lambda (destination source)
    (x86-binary-xmm-form (quote sqrtsd-xmm-xmm) destination source)))
(def x86-maxsd-xmm-xmm
  (lambda (destination source)
    (x86-binary-xmm-form (quote maxsd-xmm-xmm) destination source)))
(def x86-minsd-xmm-xmm
  (lambda (destination source)
    (x86-binary-xmm-form (quote minsd-xmm-xmm) destination source)))
(def x86-ucomisd-xmm-xmm
  (lambda (left right)
    (x86-binary-xmm-form (quote ucomisd-xmm-xmm) left right)))
(def x86-xorpd-xmm-xmm
  (lambda (destination source)
    (x86-binary-xmm-form (quote xorpd-xmm-xmm) destination source)))

(def x86-cvtsi2sd-xmm-r64
  (lambda (destination source)
    (x86-xmm-gpr64-form
      (quote cvtsi2sd-xmm-r64)
      destination
      source)))
(def x86-cvttsd2si-r64-xmm
  (lambda (destination source)
    (x86-gpr64-xmm-form
      (quote cvttsd2si-r64-xmm)
      destination
      source)))
(def x86-movq-xmm-r64
  (lambda (destination source)
    (x86-xmm-gpr64-form
      (quote movq-xmm-r64)
      destination
      source)))
(def x86-movq-r64-xmm
  (lambda (destination source)
    (x86-gpr64-xmm-form
      (quote movq-r64-xmm)
      destination
      source)))

; #178 preparation — immediate and relative-control atoms over forms already
; admitted/encoded by #176. Operand bounds come exclusively from the typed
; operand layer; these helpers contain no opcode or branch-condition tables.

(def x86-gpr64-imm32-form
  (lambda (mnemonic register immediate)
    (let ((typed-register (x86-as-gpr64 register)))
      (cond
        ((x86-machine-rejected? typed-register) typed-register)
        (t
         (let ((typed-immediate (x86-as-imm32 immediate)))
           (cond
             ((x86-machine-rejected? typed-immediate) typed-immediate)
             (t
              (list mnemonic
                    (x86-gpr64-value typed-register)
                    (x86-imm32-value typed-immediate))))))))))

(def x86-add-r64-imm32
  (lambda (register immediate)
    (x86-gpr64-imm32-form (quote add-r64-imm32) register immediate)))

(def x86-or-r64-imm32
  (lambda (register immediate)
    (x86-gpr64-imm32-form (quote or-r64-imm32) register immediate)))

(def x86-and-r64-imm32
  (lambda (register immediate)
    (x86-gpr64-imm32-form (quote and-r64-imm32) register immediate)))

(def x86-sub-r64-imm32
  (lambda (register immediate)
    (x86-gpr64-imm32-form (quote sub-r64-imm32) register immediate)))

(def x86-xor-r64-imm32
  (lambda (register immediate)
    (x86-gpr64-imm32-form (quote xor-r64-imm32) register immediate)))

(def x86-cmp-r64-imm32
  (lambda (register immediate)
    (x86-gpr64-imm32-form (quote cmp-r64-imm32) register immediate)))

(def x86-gpr64-uimm8-form
  (lambda (mnemonic register immediate)
    (let ((typed-register (x86-as-gpr64 register)))
      (cond
        ((x86-machine-rejected? typed-register) typed-register)
        (t
         (let ((typed-immediate (x86-as-uimm8 immediate)))
           (cond
             ((x86-machine-rejected? typed-immediate) typed-immediate)
             (t
              (list mnemonic
                    (x86-gpr64-value typed-register)
                    (x86-uimm8-value typed-immediate))))))))))

(def x86-shl-r64-imm8
  (lambda (register immediate)
    (x86-gpr64-uimm8-form (quote shl-r64-imm8) register immediate)))

(def x86-shr-r64-imm8
  (lambda (register immediate)
    (x86-gpr64-uimm8-form (quote shr-r64-imm8) register immediate)))

(def x86-sar-r64-imm8
  (lambda (register immediate)
    (x86-gpr64-uimm8-form (quote sar-r64-imm8) register immediate)))

(def x86-rel8-form
  (lambda (mnemonic displacement)
    (let ((typed-displacement (x86-as-disp8 displacement)))
      (cond
        ((x86-machine-rejected? typed-displacement) typed-displacement)
        (t
         (list mnemonic (x86-disp8-value typed-displacement)))))))

(def x86-jo-rel8
  (lambda (displacement)
    (x86-rel8-form (quote jo-rel8) displacement)))

(def x86-jno-rel8
  (lambda (displacement)
    (x86-rel8-form (quote jno-rel8) displacement)))

(def x86-jb-rel8
  (lambda (displacement)
    (x86-rel8-form (quote jb-rel8) displacement)))

(def x86-jnb-rel8
  (lambda (displacement)
    (x86-rel8-form (quote jnb-rel8) displacement)))

(def x86-jz-rel8
  (lambda (displacement)
    (x86-rel8-form (quote jz-rel8) displacement)))

(def x86-jbe-rel8
  (lambda (displacement)
    (x86-rel8-form (quote jbe-rel8) displacement)))

(def x86-jnbe-rel8
  (lambda (displacement)
    (x86-rel8-form (quote jnbe-rel8) displacement)))

(def x86-js-rel8
  (lambda (displacement)
    (x86-rel8-form (quote js-rel8) displacement)))

(def x86-jns-rel8
  (lambda (displacement)
    (x86-rel8-form (quote jns-rel8) displacement)))

(def x86-jp-rel8
  (lambda (displacement)
    (x86-rel8-form (quote jp-rel8) displacement)))

(def x86-jnp-rel8
  (lambda (displacement)
    (x86-rel8-form (quote jnp-rel8) displacement)))

(def x86-jl-rel8
  (lambda (displacement)
    (x86-rel8-form (quote jl-rel8) displacement)))

(def x86-jnl-rel8
  (lambda (displacement)
    (x86-rel8-form (quote jnl-rel8) displacement)))

(def x86-jle-rel8
  (lambda (displacement)
    (x86-rel8-form (quote jle-rel8) displacement)))

(def x86-jnle-rel8
  (lambda (displacement)
    (x86-rel8-form (quote jnle-rel8) displacement)))

(def x86-jmp-rel8
  (lambda (displacement)
    (x86-rel8-form (quote jmp-rel8) displacement)))

(def x86-rel32-form
  (lambda (mnemonic displacement)
    (let ((typed-displacement (x86-as-rel32 displacement)))
      (cond
        ((x86-machine-rejected? typed-displacement) typed-displacement)
        (t
         (list mnemonic (x86-rel32-value typed-displacement)))))))

(def x86-jo-rel32
  (lambda (displacement)
    (x86-rel32-form (quote jo-rel32) displacement)))

(def x86-jno-rel32
  (lambda (displacement)
    (x86-rel32-form (quote jno-rel32) displacement)))

(def x86-jb-rel32
  (lambda (displacement)
    (x86-rel32-form (quote jb-rel32) displacement)))

(def x86-jnb-rel32
  (lambda (displacement)
    (x86-rel32-form (quote jnb-rel32) displacement)))

(def x86-jz-rel32
  (lambda (displacement)
    (x86-rel32-form (quote jz-rel32) displacement)))

(def x86-jnz-rel32
  (lambda (displacement)
    (x86-rel32-form (quote jnz-rel32) displacement)))

(def x86-jbe-rel32
  (lambda (displacement)
    (x86-rel32-form (quote jbe-rel32) displacement)))

(def x86-jnbe-rel32
  (lambda (displacement)
    (x86-rel32-form (quote jnbe-rel32) displacement)))

(def x86-js-rel32
  (lambda (displacement)
    (x86-rel32-form (quote js-rel32) displacement)))

(def x86-jns-rel32
  (lambda (displacement)
    (x86-rel32-form (quote jns-rel32) displacement)))

(def x86-jp-rel32
  (lambda (displacement)
    (x86-rel32-form (quote jp-rel32) displacement)))

(def x86-jnp-rel32
  (lambda (displacement)
    (x86-rel32-form (quote jnp-rel32) displacement)))

(def x86-jl-rel32
  (lambda (displacement)
    (x86-rel32-form (quote jl-rel32) displacement)))

(def x86-jnl-rel32
  (lambda (displacement)
    (x86-rel32-form (quote jnl-rel32) displacement)))

(def x86-jle-rel32
  (lambda (displacement)
    (x86-rel32-form (quote jle-rel32) displacement)))

(def x86-jnle-rel32
  (lambda (displacement)
    (x86-rel32-form (quote jnle-rel32) displacement)))

(def x86-jmp-rel32
  (lambda (displacement)
    (x86-rel32-form (quote jmp-rel32) displacement)))

(def x86-call-rel32
  (lambda (displacement)
    (x86-rel32-form (quote call-rel32) displacement)))

; Forms admitted by later #176 slices reuse the same typed imm32/uimm8
; constructors. These atoms only choose the already-canonical form tag.
(def x86-test-r64-imm32
  (lambda (register immediate)
    (x86-gpr64-imm32-form (quote test-r64-imm32) register immediate)))

(def x86-bt-r64-imm8
  (lambda (register immediate)
    (x86-gpr64-uimm8-form (quote bt-r64-imm8) register immediate)))

(def x86-bts-r64-imm8
  (lambda (register immediate)
    (x86-gpr64-uimm8-form (quote bts-r64-imm8) register immediate)))

(def x86-btr-r64-imm8
  (lambda (register immediate)
    (x86-gpr64-uimm8-form (quote btr-r64-imm8) register immediate)))

(def x86-btc-r64-imm8
  (lambda (register immediate)
    (x86-gpr64-uimm8-form (quote btc-r64-imm8) register immediate)))

(def x86-rol-r64-imm8
  (lambda (register immediate)
    (x86-gpr64-uimm8-form (quote rol-r64-imm8) register immediate)))

(def x86-ror-r64-imm8
  (lambda (register immediate)
    (x86-gpr64-uimm8-form (quote ror-r64-imm8) register immediate)))

(def x86-encode-machine-block
  (lambda (block)
    (x86-encode-admitted-program-or-reject (machine-block-forms block))))
