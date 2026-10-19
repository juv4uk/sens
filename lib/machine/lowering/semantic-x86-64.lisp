; Semantic -> x86-64 lowering projection.
; Language meaning remains owned by Contract 11.8 + ratified exact-domain laws.
; ISA identity/encoding remains owned by lib/machine/isa + lib/machine/encoding.
; Rows here only say how an already-existing semantic identity may be realized.
;
; Executable lowerings produce structured machine forms. Byte materialization
; belongs to the closed Lisp-owned admission layer and is deliberately not
; re-exported from semantic lowering as a compatibility convenience.

; First executable semantic-lowering witness.
; Semantic identity 00001100 already exists before this file is loaded. This
; routine does not define addition; it chooses one bounded u64 realization.
; It returns structured machine forms only. Admission owns the path from those
; forms to executable bytes.
;
; RAX carries the result per SysV x86-64. RCX is caller-saved, so the proof
; routine does not violate the host ABI by clobbering a callee-saved register.
(визначити x86-lower-add-u64-forms
  (функція (лівий-операнд-машини правий-операнд-машини)
    (список
      (список (як-є mov-r64-imm64) (як-є rax) лівий-операнд-машини)
      (список (як-є mov-r64-imm64) (як-є rcx) правий-операнд-машини)
      (список (як-є add-r64-r64) (як-є rax) (як-є rcx))
      (список (як-є ret)))))

; #4001 bounded exact-D5 DIFFERENCE/TIMES witnesses. These routines only
; describe machine forms. Selection is guarded below by exact D5 evaluation,
; so SUB/IMUL are used only when inputs and the exact result all fit u64.
(визначити x86-lower-difference-u64-forms
  (функція (лівий-операнд-машини правий-операнд-машини)
    (список
      (список (як-є mov-r64-imm64) (як-є rax) лівий-операнд-машини)
      (список (як-є mov-r64-imm64) (як-є rcx) правий-операнд-машини)
      (список (як-є sub-r64-r64) (як-є rax) (як-є rcx))
      (список (як-є ret)))))

(визначити x86-lower-times-u64-forms
  (функція (лівий-операнд-машини правий-операнд-машини)
    (список
      (список (як-є mov-r64-imm64) (як-є rax) лівий-операнд-машини)
      (список (як-є mov-r64-imm64) (як-є rcx) правий-операнд-машини)
      (список (як-є imul-r64-r64) (як-є rax) (як-є rcx))
      (список (як-є ret)))))

; #4017 first exact-D5 QUOTIENT machine witness.
; This intentionally proves only x/x = 1 for positive signed-i64 operands.
; The narrow relation guarantees exact divisibility without borrowing a
; spelling, historical SID8 remainder helper, or truncating rational semantics.
(визначити x86-lower-quotient-i64-equal-forms
  (функція (лівий-операнд-машини правий-операнд-машини)
    (список
      (список (як-є mov-r64-imm64) (як-є rax) лівий-операнд-машини)
      (список (як-є mov-r64-imm64) (як-є rcx) правий-операнд-машини)
      (список (як-є cqo))
      (список (як-є idiv-r64) (як-є rcx))
      (список (як-є ret)))))

; #196 bounded conditional-growth witness for existing EQ + COND semantics.
; This routine does not define equality or conditional evaluation. It chooses
; one fixed-width u64 realization whose only purpose is to establish the
; machine-effect lower bound demanded by a two-arm runtime decision.
;
; JNZ +11 skips exactly one MOV r64,imm64 (10 bytes) plus one RET (1 byte),
; landing at the ELSE arm. This is deliberately not a general label resolver,
; branch assembler, or compiler policy. It returns structured forms only;
; closed admission remains the sole path to bytes.
(визначити x86-lower-eq-cond-u64-forms
  (функція (left right then-value else-value)
    (список
      (список (як-є mov-r64-imm64) (як-є rax) left)
      (список (як-є mov-r64-imm64) (як-є rcx) right)
      (список (як-є cmp-r64-r64) (як-є rax) (як-є rcx))
      (список (як-є jnz-rel8) 11)
      (список (як-є mov-r64-imm64) (як-є rax) then-value)
      (список (як-є ret))
      (список (як-є mov-r64-imm64) (як-є rax) else-value)
      (список (як-є ret)))))

; #196 conditional+structural composition helper. Each branch constructs one
; bounded pair in the same native-call arena and returns its CAR. The caller
; selects distinct caller-saved extended GPRs so #207's widened MOV imm64
; admission is exercised by semantic composition rather than by an ISA-only
; witness. RAX remains the guest ABI result register.
(визначити x86-lower-bounded-car-cons-u64-arm-forms
  (функція (left right left-register right-register)
    (список
      (список (як-є mov-r64-imm64) left-register left)
      (список
        (як-є mov-mem-disp8-r64)
        (як-є rdi)
        x86-pair-car-offset
        left-register)
      (список (як-є mov-r64-imm64) right-register right)
      (список
        (як-є mov-mem-disp8-r64)
        (як-є rdi)
        x86-pair-cdr-offset
        right-register)
      (список
        (як-є mov-r64-mem-disp8)
        (як-є rax)
        (як-є rdi)
        x86-pair-car-offset)
      (список (як-є ret)))))

; Third bounded #196 slice: compose runtime COND/EQ choice with structural
; CAR(CONS ...) branch bodies. This remains deliberately finite: JNZ +33 skips
; exactly one six-form CAR(CONS) arm (10+4+10+4+4+1 bytes with base RDI), and
; each arm returns directly. No label resolver, register allocator, GC, or
; general recursive expression lowering is claimed here.
(визначити x86-lower-eq-cond-car-cons-u64-forms
  (функція (left right then-car then-cdr else-car else-cdr)
    (приєднати
      (список
        (список (як-є mov-r64-imm64) (як-є rax) left)
        (список (як-є mov-r64-imm64) (як-є rcx) right)
        (список (як-є cmp-r64-r64) (як-є rax) (як-є rcx))
        (список (як-є jnz-rel8) 33))
      (приєднати
        (x86-lower-bounded-car-cons-u64-arm-forms
          then-car then-cdr (як-є r8) (як-є r9))
        (x86-lower-bounded-car-cons-u64-arm-forms
          else-car else-cdr (як-є r10) (як-є r11))))))

; Bounded structural witness for semantic identities 00000100/00000101/00000110.
; The host contributes only a raw writable arena pointer in RDI. Lisp owns
; the fact that one admitted pair cell has head at x86-pair-car-offset and
; tail at x86-pair-cdr-offset. These routines produce structured STORE/LOAD
; forms; admission and the encoder produce physical bytes only afterwards.
;
; This is deliberately not a claim that arbitrary first-class pair values may
; already escape native code: pair-x86-64.lisp fixes lifetime=native-call and
; escape=forbidden for this proof slice.
(визначити x86-lower-bounded-pair-store-u64-forms
  (функція (left right)
    (список
      (список (як-є mov-r64-imm64) (як-є rax) left)
      (список
        (як-є mov-mem-disp8-r64)
        (як-є rdi)
        x86-pair-car-offset
        (як-є rax))
      (список (як-є mov-r64-imm64) (як-є rax) right)
      (список
        (як-є mov-mem-disp8-r64)
        (як-є rdi)
        x86-pair-cdr-offset
        (як-є rax)))))

; Historical internal name retained as an explicit forwarding closure.
; Do not place the bare function designator in value position: the strict
; source path must make callability explicit and preserve structured forms.
(визначити x86-lower-bounded-pair-store-u64-instructions
  (функція (left right)
    (x86-lower-bounded-pair-store-u64-forms left right)))

; Append only the finite structured machine-form lists using current D3
; primitives. Do not route this boundary through Core4's deferred legacy
; reverse-onto/COND implementation: tests and authority remain language-owned.
(визначити x86-machine-append-forms
  (функція (форми хвіст)
    (за-умовою
      ((атом? форми) хвіст)
      (так (сполучити (перше форми) (x86-machine-append-forms (решта форми) хвіст))))))

; The bounded native pair witness has a fixed six-instruction shape. Build it
; directly rather than routing through generic append/reverse: those Core4 list
; traversals currently consume graded relation answers as COND control and must
; keep failing closed until their predicate adapter is migrated. This narrow
; witness should not depend on an unfinished generic traversal path.
(визначити x86-lower-cons-car-u64-forms
  (функція (left right)
    (список
      (список (як-є mov-r64-imm64) (як-є rax) left)
      (список
        (як-є mov-mem-disp8-r64)
        (як-є rdi)
        x86-pair-car-offset
        (як-є rax))
      (список (як-є mov-r64-imm64) (як-є rax) right)
      (список
        (як-є mov-mem-disp8-r64)
        (як-є rdi)
        x86-pair-cdr-offset
        (як-є rax))
      (список
        (як-є mov-r64-mem-disp8)
        (як-є rax)
        (як-є rdi)
        x86-pair-car-offset)
      (список (як-є ret)))))

(визначити x86-lower-cons-cdr-u64-forms
  (функція (left right)
    (список
      (список (як-є mov-r64-imm64) (як-є rax) left)
      (список
        (як-є mov-mem-disp8-r64)
        (як-є rdi)
        x86-pair-car-offset
        (як-є rax))
      (список (як-є mov-r64-imm64) (як-є rax) right)
      (список
        (як-є mov-mem-disp8-r64)
        (як-є rdi)
        x86-pair-cdr-offset
        (як-є rax))
      (список
        (як-є mov-r64-mem-disp8)
        (як-є rax)
        (як-є rdi)
        x86-pair-cdr-offset)
      (список (як-є ret)))))

; Bounded semantic entry for the Vertical Day CAR witness.
; Canonical CAR/CDR own pair validity and therefore fail with the language's
; existing Type outcome before any machine request exists. Only after that
; language-owned gate succeeds do the extracted u64 fields become structured
; machine forms, pass closed admission, and enter the semantics-blind host.
; No pair predicate or tag rule is duplicated in this machine layer.
(визначити x86-call-semantic-car-u64
  (функція (pair-value)
    (x86-call-admitted-u64
      (x86-lower-cons-car-u64-forms
        (перше pair-value)
        (решта pair-value))
      x86-pair-cell-bytes)))


; #3989/#4001 current exact-domain D5 arithmetic entry.
; Exact D5 semantic identity chooses the operation. The machine fast path then
; applies a deliberately conservative numeric guard that cannot change exact
; language meaning:
;   PLUS/TIMES: both exact-integer inputs in u32 => result is guaranteed u64;
;   DIFFERENCE: both exact-integer inputs in u64 and left >= right.
; Anything outside those proved rectangles fails closed to the exact Lisp/Q
; fallback. Historical SID8 values and human spellings never participate.
(визначити x86-current-d5-u32-inputs?
  (функція (left right)
    (за-умовою
      ((x86-admission-exact-integer? left)
       (за-умовою
         ((x86-admission-within-inclusive-integer-range?
            left 0 4294967295)
          (за-умовою
            ((x86-admission-exact-integer? right)
             (x86-admission-within-inclusive-integer-range?
               right 0 4294967295))
            ((атом? ()) (як-є ()))))
         ((атом? ()) (як-є ()))))
      ((атом? ()) (як-є ())))))

(визначити x86-current-d5-difference-u64-safe?
  (функція (left right)
    (за-умовою
      ((x86-admission-exact-integer? left)
       (за-умовою
         ((x86-admission-within-inclusive-integer-range?
            left 0 18446744073709551615)
          (за-умовою
            ((x86-admission-exact-integer? right)
             (за-умовою
               ((x86-admission-within-inclusive-integer-range?
                  right 0 18446744073709551615)
                ; Inclusive order is derived from admitted D5 LESSP + D4 NOT.
                ; Exact D1 controls stay distinct from numeric 0/1 and host truth.
                (за-умовою
                  ((хибне? (менше? left right)) так)
                  ((атом? ()) (як-є ()))))
               ((атом? ()) (як-є ()))))
            ((атом? ()) (як-є ()))))
         ((атом? ()) (як-є ()))))
      ((атом? ()) (як-є ())))))

; #4068 width-safe machine key helper. Width and packed bits are separate
; mechanism scalars derived from Rust DomainIdentity; source leading zeros are never
; consulted.
(визначити x86-current-domain-key?
  (функція (width bits expected-width expected-bits)
    (за-умовою
      ((тотожне? width expected-width)
       (тотожне? bits expected-bits))
      ((атом? ()) (як-є ())))))

(визначити x86-lower-current-binary-u64-forms
  (функція (width bits left right)
    (за-умовою
      ((x86-current-domain-key? width bits 5 10)
       (за-умовою
         ((x86-current-d5-u32-inputs? left right)
          (x86-lower-add-u64-forms left right))
         ((атом? ()) (як-є exact-d5-fallback-required))))
      ((x86-current-domain-key? width bits 5 11)
       (за-умовою
         ((x86-current-d5-difference-u64-safe? left right)
          (x86-lower-difference-u64-forms left right))
         ((атом? ()) (як-є exact-d5-fallback-required))))
      ((x86-current-domain-key? width bits 5 22)
       (за-умовою
         ((x86-current-d5-u32-inputs? left right)
          (x86-lower-times-u64-forms left right))
         ((атом? ()) (як-є exact-d5-fallback-required))))
      ((атом? ())
       (як-є unsupported-current-domain-binary-u64)))))

(визначити x86-encode-current-binary-u64
  (функція (width bits left right)
    ((функція (forms)
       (за-умовою
        ((тотожне? forms (як-є unsupported-current-domain-binary-u64))
         (як-є unsupported-current-domain-binary-u64))
        ((тотожне? forms (як-є exact-d5-fallback-required))
         (як-є exact-d5-fallback-required))
        ((атом? ())
         (x86-encode-admitted-program forms))))
      (x86-lower-current-binary-u64-forms
                    width bits left right))))

; #4063 exact D6 ADD1/SUB1 bounded fast paths.
; Language meaning is already admitted as LOWER_DOMAIN_COMPOSITION over exact
; D5 PLUS/DIFFERENCE with exact integer 1. This machine slice reuses the same
; admitted ADD/SUB forms and adds no arithmetic meaning of its own.
(визначити x86-current-d6-add1-u64-safe?
  (функція (value)
    (за-умовою
      ((x86-admission-exact-integer? value)
       (x86-admission-within-inclusive-integer-range?
         value 0 18446744073709551614))
      ((атом? ()) (як-є ())))))

(визначити x86-current-d6-sub1-u64-safe?
  (функція (value)
    (за-умовою
      ((x86-admission-exact-integer? value)
       (x86-admission-within-inclusive-integer-range?
         value 1 18446744073709551615))
      ((атом? ()) (як-є ())))))

(визначити x86-lower-current-d6-unary-u64-forms
  (функція (width bits value)
    (за-умовою
      ((x86-current-domain-key? width bits 6 14)
       (за-умовою
         ((x86-current-d6-add1-u64-safe? value)
          (x86-lower-add-u64-forms value 1))
         ((атом? ()) (як-є exact-d6-fallback-required))))
      ((x86-current-domain-key? width bits 6 15)
       (за-умовою
         ((x86-current-d6-sub1-u64-safe? value)
          (x86-lower-difference-u64-forms value 1))
         ((атом? ()) (як-є exact-d6-fallback-required))))
      ((атом? ())
       (як-є unsupported-current-domain-d6-unary-u64)))))

(визначити x86-encode-current-d6-unary-u64
  (функція (width bits value)
    ((функція (forms) (за-умовою
        ((тотожне? forms (як-є unsupported-current-domain-d6-unary-u64))
         (як-є unsupported-current-domain-d6-unary-u64))
        ((тотожне? forms (як-є exact-d6-fallback-required))
         (як-є exact-d6-fallback-required))
        ((атом? ())
         (x86-encode-admitted-program forms)))) (x86-lower-current-d6-unary-u64-forms
                    width bits value))))

; #4017 exact D5:10111 QUOTIENT bounded dispatcher.
; Only equal positive exact integers inside signed i64 enter IDIV. This is a
; proof slice, not a claim of general integer division. All non-equal,
; rational, zero, negative or out-of-range cases remain exact Lisp/Q fallback.
(визначити x86-current-d5-quotient-i64-equal-safe?
  (функція (left right)
    (за-умовою
      ((x86-admission-exact-integer? left)
       (за-умовою
         ((x86-admission-within-inclusive-integer-range?
            left 1 9223372036854775807)
          (за-умовою
            ((x86-admission-exact-integer? right)
             (за-умовою
               ((x86-admission-within-inclusive-integer-range?
                  right 1 9223372036854775807)
                (тотожне? left right))
               ((атом? ()) (як-є ()))))
            ((атом? ()) (як-є ()))))
         ((атом? ()) (як-є ()))))
      ((атом? ()) (як-є ())))))

(визначити x86-lower-current-quotient-i64-forms
  (функція (width bits left right)
    (за-умовою
      ((x86-current-domain-key? width bits 5 23)
       (за-умовою
         ((x86-current-d5-quotient-i64-equal-safe? left right)
          (x86-lower-quotient-i64-equal-forms left right))
         ((атом? ()) (як-є exact-d5-fallback-required))))
      ((атом? ()) (як-є unsupported-current-domain-quotient-i64)))))

(визначити x86-encode-current-quotient-i64
  (функція (width bits left right)
    ((функція (forms) (за-умовою
        ((тотожне? forms (як-є unsupported-current-domain-quotient-i64))
         (як-є unsupported-current-domain-quotient-i64))
        ((тотожне? forms (як-є exact-d5-fallback-required))
         (як-є exact-d5-fallback-required))
        ((атом? ())
         (x86-encode-admitted-program forms)))) (x86-lower-current-quotient-i64-forms
                    width bits left right))))

; #4018 exact D5 order-predicate machine proof.
; These forms intentionally produce only an INTERNAL machine bit in RAX.
; No native-call wrapper exposes that 0/1 as a language predicate. The
; language-visible result boundary remains the existing D5 -> D1
; canonicalization in Rust.
(визначити x86-current-d5-order-i63-safe?
  (функція (left right)
    (за-умовою
      ((x86-admission-exact-integer? left)
       (за-умовою
         ((x86-admission-within-inclusive-integer-range?
            left 0 9223372036854775807)
          (за-умовою
            ((x86-admission-exact-integer? right)
             (x86-admission-within-inclusive-integer-range?
               right 0 9223372036854775807))
            ((атом? ()) (як-є ()))))
         ((атом? ()) (як-є ()))))
      ((атом? ()) (як-є ())))))

(визначити x86-lower-order-i64-forms
  (функція (width bits left right)
    (за-умовою
      ((x86-current-d5-order-i63-safe? left right)
       (за-умовою
         ((x86-current-domain-key? width bits 5 26)
          (список
            (список (як-є mov-r64-imm64) (як-є rax) left)
            (список (як-є mov-r64-imm64) (як-є rcx) right)
            (список (як-є cmp-r64-r64) (як-є rax) (як-є rcx))
            (список (як-є setl-r8) (як-є al))
            (список (як-є movzx-r64-r8) (як-є rax) (як-є al))
            (список (як-є ret))))
         ((x86-current-domain-key? width bits 5 27)
          (список
            (список (як-є mov-r64-imm64) (як-є rax) left)
            (список (як-є mov-r64-imm64) (як-є rcx) right)
            (список (як-є cmp-r64-r64) (як-є rax) (як-є rcx))
            (список (як-є setg-r8) (як-є al))
            (список (як-є movzx-r64-r8) (як-є rax) (як-є al))
            (список (як-є ret))))
         ((атом? ())
          (як-є unsupported-current-domain-order-i64))))
      ((атом? ())
       (як-є exact-d5-fallback-required)))))

(визначити x86-encode-current-order-bit
  (функція (width bits left right)
    ((функція (forms) (за-умовою
        ((тотожне? forms (як-є unsupported-current-domain-order-i64))
         (як-є unsupported-current-domain-order-i64))
        ((тотожне? forms (як-є exact-d5-fallback-required))
         (як-є exact-d5-fallback-required))
        ((атом? ())
         (x86-encode-admitted-program forms)))) (x86-lower-order-i64-forms width bits left right))))

; #4064/#4068 exact D5:01000 ZEROP bounded machine proof.
; Full ZEROP semantics include the historical epsilon policy for rational
; carriers. Native CMP-to-zero is therefore admitted only for exact
; nonnegative u64 integers. The emitted 0/1 remains INTERNAL machine data;
; language-visible result remains exact D1.
(визначити x86-current-d5-zerop-u64-safe?
  (функція (value)
    (за-умовою
      ((x86-admission-exact-integer? value)
       (x86-admission-within-inclusive-integer-range?
         value 0 18446744073709551615))
      ((атом? ()) (як-є ())))))

(визначити x86-lower-zerop-u64-forms
  (функція (value)
    (список
      (список (як-є mov-r64-imm64) (як-є rax) value)
      (список (як-є mov-r64-imm64) (як-є rcx) 0)
      (список (як-є cmp-r64-r64) (як-є rax) (як-є rcx))
      (список (як-є sete-r8) (як-є al))
      (список (як-є movzx-r64-r8) (як-є rax) (як-є al))
      (список (як-є ret)))))

(визначити x86-lower-current-zerop-u64-forms
  (функція (width bits value)
    (за-умовою
      ((x86-current-domain-key? width bits 5 8)
       (за-умовою
         ((x86-current-d5-zerop-u64-safe? value)
          (x86-lower-zerop-u64-forms value))
         ((атом? ()) (як-є exact-d5-fallback-required))))
      ((атом? ())
       (як-є unsupported-current-domain-zerop-u64)))))

(визначити x86-encode-current-zerop-bit
  (функція (width bits value)
    ((функція (forms) (за-умовою
        ((тотожне? forms (як-є unsupported-current-domain-zerop-u64))
         (як-є unsupported-current-domain-zerop-u64))
        ((тотожне? forms (як-є exact-d5-fallback-required))
         (як-є exact-d5-fallback-required))
        ((атом? ())
         (x86-encode-admitted-program forms)))) (x86-lower-current-zerop-u64-forms width bits value))))

; #3996 exact-domain structural D3 dispatcher.
; These are bounded native-call witnesses only. They do not claim a general
; allocator, escaping pair ABI, GC, or arbitrary first-class native pair value.
(визначити x86-lower-current-structural-u64-forms
  (функція (width bits left right)
    (за-умовою
      ((x86-current-domain-key? width bits 3 7)
       (x86-lower-bounded-pair-store-u64-forms left right))
      ((x86-current-domain-key? width bits 3 4)
       (x86-lower-cons-car-u64-forms left right))
      ((x86-current-domain-key? width bits 3 3)
       (x86-lower-cons-cdr-u64-forms left right))
      ((атом? ())
       (як-є unsupported-current-domain-structural-u64)))))

(визначити x86-encode-current-structural-u64
  (функція (width bits left right)
    ((функція (forms) (за-умовою
        ((тотожне? forms (як-є unsupported-current-domain-structural-u64))
         (як-є unsupported-current-domain-structural-u64))
        ((атом? ())
         (x86-encode-admitted-program-or-reject forms)))) (x86-lower-current-structural-u64-forms
                    width bits left right))))

; #4000 exact-domain bounded composition for current D3 EQ + COND.
; This route intentionally does not expose an independent numeric-boolean EQ
; machine API. The equality decision stays internal to the already-witnessed
; two-arm composition; the language boundary remains exact D1/EMPTY according
; to current D3 law.
(визначити x86-lower-current-eq-cond-u64-forms
  (функція
    (eq-width eq-bits cond-width cond-bits left right then-value else-value)
    (за-умовою
      ((x86-current-domain-key? eq-width eq-bits 3 5)
       (за-умовою
         ((x86-current-domain-key? cond-width cond-bits 3 6)
          (x86-lower-eq-cond-u64-forms
            left right then-value else-value))
         ((атом? ())
          (як-є unsupported-current-domain-eq-cond-u64))))
      ((атом? ())
       (як-є unsupported-current-domain-eq-cond-u64)))))

(визначити x86-encode-current-eq-cond-u64
  (функція
    (eq-width eq-bits cond-width cond-bits left right then-value else-value)
    ((функція (forms) (за-умовою
        ((тотожне? forms (як-є unsupported-current-domain-eq-cond-u64))
         (як-є unsupported-current-domain-eq-cond-u64))
        ((атом? ())
         (x86-encode-admitted-program-or-reject forms)))) (x86-lower-current-eq-cond-u64-forms
              eq-width eq-bits cond-width cond-bits
              left right then-value else-value))))


