; Semantic -> x86-64 lowering projection.
; Language meaning remains owned by Contract 11.8 + ratified exact-domain laws.
; ISA identity/encoding remains owned by lib/machine/isa + lib/machine/encoding.
; Rows here only say how an already-existing semantic identity may be realized.
;
; Executable lowerings produce structured machine forms. Byte materialization
; belongs to the closed Lisp-owned admission layer and is deliberately not
; re-exported from semantic lowering as a compatibility convenience.

; Historical byte-SID projection retained only as compatibility/provenance.
(00001001 x86-legacy-sid-lowering-profile-v1
  (00000001
    ((00000010 sequence "tag-test: TEST/AND/CMP")
     (00000011 direct "CMP/SETE")
     (00000100 runtime "allocate+STORE-pair")
     (00000101 direct "LOAD-pair-head")
     (00000110 direct "LOAD-pair-tail")
     (00000111 control "TEST/CMP+Jcc")

     (00001100 fast-path "ADD / ADDSD")
     (00001101 fast-path "SUB/NEG / SUBSD")
     (00001110 fast-path "IMUL / MULSD")
     (00001111 fast-path "DIVSD; exact-rational routine")
     (00010000 sequence "TEST/NEG/CMOV")
     (00010001 sequence "CMP/CMOV-min")
     (00010010 sequence "CMP/CMOV-max")
     (00010011 fast-path "IDIV-remainder")
     (00010100 fast-path "IDIV-quotient")
     (00010101 fast-path "SQRTSD")
     (00010110 runtime "integer-sqrt routine")
     (00010111 runtime "loop+CMP/CMOV-min")
     (00011000 runtime "loop+CMP/CMOV-max")
     (00011010 direct "CMP/SETL")
     (00011011 direct "CMP/SETG")
     (00011100 direct "CMP/SETE")
     (00011101 direct "CMP/SETLE")
     (00011110 direct "CMP/SETGE")
     (00100001 direct "TEST/SETE")

     (00100011 sequence "tag-test: symbol")
     (00100100 sequence "tag-test: string")
     (00100110 sequence "tag-test: numeric-buffer")
     (00101000 runtime "list-walk+LOAD-pair-tail")
     (00101011 runtime "indexed-list-walk+LOAD")
     (00101111 sequence "LOAD-tail+LOAD-head")
     (00110000 sequence "2xLOAD-tail+LOAD-head")
     (00110001 sequence "3xLOAD-tail+LOAD-head")
     (00110010 sequence "4xLOAD-tail+LOAD-head")
     (00110011 sequence "LOAD-head+LOAD-head")
     (00110100 sequence "LOAD-tail+LOAD-head")
     (00110101 sequence "LOAD-tail+LOAD-tail")
     (00110110 sequence "3xLOAD-tail+LOAD-head")

     (01001111 runtime "allocate+STORE-vector")
     (01010000 runtime "allocate+fill-vector")
     (01010001 direct "LOAD-vector-length")
     (01010010 direct "LOAD-vector-element")
     (01010011 direct "STORE-vector-element")
     (01010100 runtime "allocate+STORE-i32-buffer")
     (01010101 runtime "allocate+STORE-f32-buffer")
     (01010110 direct "LOAD-buffer-tag")
     (01010111 direct "LOAD-buffer-length")
     (01011000 direct "LOAD-buffer-element")
     (01011001 runtime "loop; AVX2 specialization possible")

     (01100001 fast-path "IDIV/IMUL-reciprocal")
     (01100110 direct "CMP/SETGE")
     (01100111 direct "CMP/SETGE")
     (01101000 direct "SUB")
     (01101001 direct "ADD")
     (01101010 direct "ADD")

     (01110001 runtime "empty-vector object")
     (01110010 runtime "allocate+copy+STORE-vector")
     (01110011 direct "LOAD-vector-length")
     (01110100 direct "LOAD-vector-element")

     (10011000 direct "MOV/pass-through")
     (10011010 control "short-circuit TEST/Jcc")
     (10011011 control "short-circuit TEST/Jcc"))))

; First executable semantic-lowering witness.
; Semantic identity 00001100 already exists before this file is loaded. This
; routine does not define addition; it chooses one bounded u64 realization.
; It returns structured machine forms only. Admission owns the path from those
; forms to executable bytes.
;
; RAX carries the result per SysV x86-64. RCX is caller-saved, so the proof
; routine does not violate the host ABI by clobbering a callee-saved register.
(00001001 x86-lower-add-u64-forms
  (00001000 (left right)
    (00100111
      (00100111 (00000001 mov-r64-imm64) (00000001 rax) left)
      (00100111 (00000001 mov-r64-imm64) (00000001 rcx) right)
      (00100111 (00000001 add-r64-r64) (00000001 rax) (00000001 rcx))
      (00100111 (00000001 ret)))))

; #4001 bounded exact-D5 DIFFERENCE/TIMES witnesses. These routines only
; describe machine forms. Selection is guarded below by exact D5 evaluation,
; so SUB/IMUL are used only when inputs and the exact result all fit u64.
(00001001 x86-lower-difference-u64-forms
  (00001000 (left right)
    (00100111
      (00100111 (00000001 mov-r64-imm64) (00000001 rax) left)
      (00100111 (00000001 mov-r64-imm64) (00000001 rcx) right)
      (00100111 (00000001 sub-r64-r64) (00000001 rax) (00000001 rcx))
      (00100111 (00000001 ret)))))

(00001001 x86-lower-times-u64-forms
  (00001000 (left right)
    (00100111
      (00100111 (00000001 mov-r64-imm64) (00000001 rax) left)
      (00100111 (00000001 mov-r64-imm64) (00000001 rcx) right)
      (00100111 (00000001 imul-r64-r64) (00000001 rax) (00000001 rcx))
      (00100111 (00000001 ret)))))

; #4017 first exact-D5 QUOTIENT machine witness.
; This intentionally proves only x/x = 1 for positive signed-i64 operands.
; The narrow relation guarantees exact divisibility without borrowing a
; spelling, historical SID8 remainder helper, or truncating rational semantics.
(00001001 x86-lower-quotient-i64-equal-forms
  (00001000 (left right)
    (00100111
      (00100111 (00000001 mov-r64-imm64) (00000001 rax) left)
      (00100111 (00000001 mov-r64-imm64) (00000001 rcx) right)
      (00100111 (00000001 cqo))
      (00100111 (00000001 idiv-r64) (00000001 rcx))
      (00100111 (00000001 ret)))))

; #196 bounded conditional-growth witness for existing EQ + COND semantics.
; This routine does not define equality or conditional evaluation. It chooses
; one fixed-width u64 realization whose only purpose is to establish the
; machine-effect lower bound demanded by a two-arm runtime decision.
;
; JNZ +11 skips exactly one MOV r64,imm64 (10 bytes) plus one RET (1 byte),
; landing at the ELSE arm. This is deliberately not a general label resolver,
; branch assembler, or compiler policy. It returns structured forms only;
; closed admission remains the sole path to bytes.
(00001001 x86-lower-eq-cond-u64-forms
  (00001000 (left right then-value else-value)
    (00100111
      (00100111 (00000001 mov-r64-imm64) (00000001 rax) left)
      (00100111 (00000001 mov-r64-imm64) (00000001 rcx) right)
      (00100111 (00000001 cmp-r64-r64) (00000001 rax) (00000001 rcx))
      (00100111 (00000001 jnz-rel8) #d11)
      (00100111 (00000001 mov-r64-imm64) (00000001 rax) then-value)
      (00100111 (00000001 ret))
      (00100111 (00000001 mov-r64-imm64) (00000001 rax) else-value)
      (00100111 (00000001 ret)))))

; #196 conditional+structural composition helper. Each branch constructs one
; bounded pair in the same native-call arena and returns its CAR. The caller
; selects distinct caller-saved extended GPRs so #207's widened MOV imm64
; admission is exercised by semantic composition rather than by an ISA-only
; witness. RAX remains the guest ABI result register.
(00001001 x86-lower-bounded-car-cons-u64-arm-forms
  (00001000 (left right left-register right-register)
    (00100111
      (00100111 (00000001 mov-r64-imm64) left-register left)
      (00100111
        (00000001 mov-mem-disp8-r64)
        (00000001 rdi)
        x86-pair-car-offset
        left-register)
      (00100111 (00000001 mov-r64-imm64) right-register right)
      (00100111
        (00000001 mov-mem-disp8-r64)
        (00000001 rdi)
        x86-pair-cdr-offset
        right-register)
      (00100111
        (00000001 mov-r64-mem-disp8)
        (00000001 rax)
        (00000001 rdi)
        x86-pair-car-offset)
      (00100111 (00000001 ret)))))

; Third bounded #196 slice: compose runtime COND/EQ choice with structural
; CAR(CONS ...) branch bodies. This remains deliberately finite: JNZ +33 skips
; exactly one six-form CAR(CONS) arm (10+4+10+4+4+1 bytes with base RDI), and
; each arm returns directly. No label resolver, register allocator, GC, or
; general recursive expression lowering is claimed here.
(00001001 x86-lower-eq-cond-car-cons-u64-forms
  (00001000 (left right then-car then-cdr else-car else-cdr)
    (00101001
      (00100111
        (00100111 (00000001 mov-r64-imm64) (00000001 rax) left)
        (00100111 (00000001 mov-r64-imm64) (00000001 rcx) right)
        (00100111 (00000001 cmp-r64-r64) (00000001 rax) (00000001 rcx))
        (00100111 (00000001 jnz-rel8) 33))
      (00101001
        (x86-lower-bounded-car-cons-u64-arm-forms
          then-car then-cdr (00000001 r8) (00000001 r9))
        (x86-lower-bounded-car-cons-u64-arm-forms
          else-car else-cdr (00000001 r10) (00000001 r11))))))

; Bounded structural witness for semantic identities 00000100/00000101/00000110.
; The host contributes only a raw writable arena pointer in RDI. Lisp owns
; the fact that one admitted pair cell has head at x86-pair-car-offset and
; tail at x86-pair-cdr-offset. These routines produce structured STORE/LOAD
; forms; admission and the encoder produce physical bytes only afterwards.
;
; This is deliberately not a claim that arbitrary first-class pair values may
; already escape native code: pair-x86-64.lisp fixes lifetime=native-call and
; escape=forbidden for this proof slice.
(00001001 x86-lower-bounded-pair-store-u64-forms
  (00001000 (left right)
    (00100111
      (00100111 (00000001 mov-r64-imm64) (00000001 rax) left)
      (00100111
        (00000001 mov-mem-disp8-r64)
        (00000001 rdi)
        x86-pair-car-offset
        (00000001 rax))
      (00100111 (00000001 mov-r64-imm64) (00000001 rax) right)
      (00100111
        (00000001 mov-mem-disp8-r64)
        (00000001 rdi)
        x86-pair-cdr-offset
        (00000001 rax)))))

; Historical internal name retained as an explicit forwarding closure.
; Do not place the bare function designator in value position: the strict
; source path must make callability explicit and preserve structured forms.
(00001001 x86-lower-bounded-pair-store-u64-instructions
  (00001000 (left right)
    (x86-lower-bounded-pair-store-u64-forms left right)))

(00001001 x86-lower-cons-car-u64-forms
  (00001000 (left right)
    (00101001
      (x86-lower-bounded-pair-store-u64-forms left right)
      (00100111
        (00100111
          (00000001 mov-r64-mem-disp8)
          (00000001 rax)
          (00000001 rdi)
          x86-pair-car-offset)
        (00100111 (00000001 ret))))))

(00001001 x86-lower-cons-cdr-u64-forms
  (00001000 (left right)
    (00101001
      (x86-lower-bounded-pair-store-u64-forms left right)
      (00100111
        (00100111
          (00000001 mov-r64-mem-disp8)
          (00000001 rax)
          (00000001 rdi)
          x86-pair-cdr-offset)
        (00100111 (00000001 ret))))))

; Bounded semantic entry for the Vertical Day CAR witness.
; Canonical CAR/CDR own pair validity and therefore fail with the language's
; existing Type outcome before any machine request exists. Only after that
; language-owned gate succeeds do the extracted u64 fields become structured
; machine forms, pass closed admission, and enter the semantics-blind host.
; No pair predicate or tag rule is duplicated in this machine layer.
(00001001 x86-call-semantic-car-u64
  (00001000 (pair-value)
    (x86-call-admitted-u64
      (x86-lower-cons-car-u64-forms
        (00000101 pair-value)
        (00000110 pair-value))
      x86-pair-cell-bytes)))


; #3989/#4001 current exact-domain D5 arithmetic entry.
; Exact D5 semantic identity chooses the operation. The machine fast path then
; applies a deliberately conservative numeric guard that cannot change exact
; language meaning:
;   PLUS/TIMES: both exact-integer inputs in u32 => result is guaranteed u64;
;   DIFFERENCE: both exact-integer inputs in u64 and left >= right.
; Anything outside those proved rectangles fails closed to the exact Lisp/Q
; fallback. Historical SID8 values and human spellings never participate.
(00001001 x86-current-d5-u32-inputs?
  (00001000 (left right)
    (00000111
      ((x86-admission-exact-integer? left)
       (00000111
         ((x86-admission-within-inclusive-integer-range?
            left 0 4294967295)
          (00000111
            ((x86-admission-exact-integer? right)
             (x86-admission-within-inclusive-integer-range?
               right 0 4294967295))
            (t (00000001 ()))))
         (t (00000001 ()))))
      (t (00000001 ())))))

(00001001 x86-current-d5-difference-u64-safe?
  (00001000 (left right)
    (00000111
      ((x86-admission-exact-integer? left)
       (00000111
         ((x86-admission-within-inclusive-integer-range?
            left 0 18446744073709551615)
          (00000111
            ((x86-admission-exact-integer? right)
             (00000111
               ((x86-admission-within-inclusive-integer-range?
                  right 0 18446744073709551615)
                ; Exact-Q >= returns D1 1/0. Compare explicitly because 0 is
                ; itself a value and must never become generic truthiness.
                (00000111
                  ((00011110 left right)  t)
                  (t (00000001 ()))))
               (t (00000001 ()))))
            (t (00000001 ()))))
         (t (00000001 ()))))
      (t (00000001 ())))))

; #4068 width-safe machine key helper. Width and packed bits are separate
; mechanism scalars derived from Rust DomainIdentity; source leading zeros are never
; consulted.
(00001001 x86-current-domain-key?
  (00001000 (width bits expected-width expected-bits)
    (00000111
      ((00100010 width expected-width)
       (00100010 bits expected-bits))
      (t (00000001 ())))))

(00001001 x86-lower-current-binary-u64-forms
  (00001000 (width bits left right)
    (00000111
      ((x86-current-domain-key? width bits 5 10)
       (00000111
         ((x86-current-d5-u32-inputs? left right)
          (x86-lower-add-u64-forms left right))
         (t (00000001 exact-d5-fallback-required))))
      ((x86-current-domain-key? width bits 5 11)
       (00000111
         ((x86-current-d5-difference-u64-safe? left right)
          (x86-lower-difference-u64-forms left right))
         (t (00000001 exact-d5-fallback-required))))
      ((x86-current-domain-key? width bits 5 22)
       (00000111
         ((x86-current-d5-u32-inputs? left right)
          (x86-lower-times-u64-forms left right))
         (t (00000001 exact-d5-fallback-required))))
      (t
       (00000001 unsupported-current-domain-binary-u64)))))

(00001001 x86-encode-current-binary-u64
  (00001000 (width bits left right)
    (10011100 ((forms
                  (x86-lower-current-binary-u64-forms
                    width bits left right)))
      (00000111
        ((00100010 forms (00000001 unsupported-current-domain-binary-u64))
         (00000001 unsupported-current-domain-binary-u64))
        ((00100010 forms (00000001 exact-d5-fallback-required))
         (00000001 exact-d5-fallback-required))
        (t
         (x86-encode-admitted-program forms))))))

; #4063 exact D6 ADD1/SUB1 bounded fast paths.
; Language meaning is already admitted as LOWER_DOMAIN_COMPOSITION over exact
; D5 PLUS/DIFFERENCE with exact integer 1. This machine slice reuses the same
; admitted ADD/SUB forms and adds no arithmetic meaning of its own.
(00001001 x86-current-d6-add1-u64-safe?
  (00001000 (value)
    (00000111
      ((x86-admission-exact-integer? value)
       (x86-admission-within-inclusive-integer-range?
         value 0 18446744073709551614))
      (t (00000001 ())))))

(00001001 x86-current-d6-sub1-u64-safe?
  (00001000 (value)
    (00000111
      ((x86-admission-exact-integer? value)
       (x86-admission-within-inclusive-integer-range?
         value 1 18446744073709551615))
      (t (00000001 ())))))

(00001001 x86-lower-current-d6-unary-u64-forms
  (00001000 (width bits value)
    (00000111
      ((x86-current-domain-key? width bits 6 14)
       (00000111
         ((x86-current-d6-add1-u64-safe? value)
          (x86-lower-add-u64-forms value 1))
         (t (00000001 exact-d6-fallback-required))))
      ((x86-current-domain-key? width bits 6 15)
       (00000111
         ((x86-current-d6-sub1-u64-safe? value)
          (x86-lower-difference-u64-forms value 1))
         (t (00000001 exact-d6-fallback-required))))
      (t
       (00000001 unsupported-current-domain-d6-unary-u64)))))

(00001001 x86-encode-current-d6-unary-u64
  (00001000 (width bits value)
    (10011100 ((forms
                  (x86-lower-current-d6-unary-u64-forms
                    width bits value)))
      (00000111
        ((00100010 forms (00000001 unsupported-current-domain-d6-unary-u64))
         (00000001 unsupported-current-domain-d6-unary-u64))
        ((00100010 forms (00000001 exact-d6-fallback-required))
         (00000001 exact-d6-fallback-required))
        (t
         (x86-encode-admitted-program forms))))))

; #4017 exact D5:10111 QUOTIENT bounded dispatcher.
; Only equal positive exact integers inside signed i64 enter IDIV. This is a
; proof slice, not a claim of general integer division. All non-equal,
; rational, zero, negative or out-of-range cases remain exact Lisp/Q fallback.
(00001001 x86-current-d5-quotient-i64-equal-safe?
  (00001000 (left right)
    (00000111
      ((x86-admission-exact-integer? left)
       (00000111
         ((x86-admission-within-inclusive-integer-range?
            left 1 9223372036854775807)
          (00000111
            ((x86-admission-exact-integer? right)
             (00000111
               ((x86-admission-within-inclusive-integer-range?
                  right 1 9223372036854775807)
                (00100010 left right))
               (t (00000001 ()))))
            (t (00000001 ()))))
         (t (00000001 ()))))
      (t (00000001 ())))))

(00001001 x86-lower-current-quotient-i64-forms
  (00001000 (width bits left right)
    (00000111
      ((x86-current-domain-key? width bits 5 23)
       (00000111
         ((x86-current-d5-quotient-i64-equal-safe? left right)
          (x86-lower-quotient-i64-equal-forms left right))
         (t (00000001 exact-d5-fallback-required))))
      (t (00000001 unsupported-current-domain-quotient-i64)))))

(00001001 x86-encode-current-quotient-i64
  (00001000 (width bits left right)
    (10011100 ((forms
                  (x86-lower-current-quotient-i64-forms
                    width bits left right)))
      (00000111
        ((00100010 forms (00000001 unsupported-current-domain-quotient-i64))
         (00000001 unsupported-current-domain-quotient-i64))
        ((00100010 forms (00000001 exact-d5-fallback-required))
         (00000001 exact-d5-fallback-required))
        (t
         (x86-encode-admitted-program forms))))))

; #4018 exact D5 order-predicate machine proof.
; These forms intentionally produce only an INTERNAL machine bit in RAX.
; No native-call wrapper exposes that 0/1 as a language predicate. The
; language-visible result boundary remains the existing D5 -> D1
; canonicalization in Rust.
(00001001 x86-current-d5-order-i63-safe?
  (00001000 (left right)
    (00000111
      ((x86-admission-exact-integer? left)
       (00000111
         ((x86-admission-within-inclusive-integer-range?
            left 0 9223372036854775807)
          (00000111
            ((x86-admission-exact-integer? right)
             (x86-admission-within-inclusive-integer-range?
               right 0 9223372036854775807))
            (t (00000001 ()))))
         (t (00000001 ()))))
      (t (00000001 ())))))

(00001001 x86-lower-order-i64-forms
  (00001000 (width bits left right)
    (00000111
      ((x86-current-d5-order-i63-safe? left right)
       (00000111
         ((x86-current-domain-key? width bits 5 26)
          (00100111
            (00100111 (00000001 mov-r64-imm64) (00000001 rax) left)
            (00100111 (00000001 mov-r64-imm64) (00000001 rcx) right)
            (00100111 (00000001 cmp-r64-r64) (00000001 rax) (00000001 rcx))
            (00100111 (00000001 setl-r8) (00000001 al))
            (00100111 (00000001 movzx-r64-r8) (00000001 rax) (00000001 al))
            (00100111 (00000001 ret))))
         ((x86-current-domain-key? width bits 5 27)
          (00100111
            (00100111 (00000001 mov-r64-imm64) (00000001 rax) left)
            (00100111 (00000001 mov-r64-imm64) (00000001 rcx) right)
            (00100111 (00000001 cmp-r64-r64) (00000001 rax) (00000001 rcx))
            (00100111 (00000001 setg-r8) (00000001 al))
            (00100111 (00000001 movzx-r64-r8) (00000001 rax) (00000001 al))
            (00100111 (00000001 ret))))
         (t
          (00000001 unsupported-current-domain-order-i64))))
      (t
       (00000001 exact-d5-fallback-required)))))

(00001001 x86-encode-current-order-bit
  (00001000 (width bits left right)
    (10011100 ((forms (x86-lower-order-i64-forms width bits left right)))
      (00000111
        ((00100010 forms (00000001 unsupported-current-domain-order-i64))
         (00000001 unsupported-current-domain-order-i64))
        ((00100010 forms (00000001 exact-d5-fallback-required))
         (00000001 exact-d5-fallback-required))
        (t
         (x86-encode-admitted-program forms))))))

; #4064/#4068 exact D5:01000 ZEROP bounded machine proof.
; Full ZEROP semantics include the historical epsilon policy for rational
; carriers. Native CMP-to-zero is therefore admitted only for exact
; nonnegative u64 integers. The emitted 0/1 remains INTERNAL machine data;
; language-visible result remains exact D1.
(00001001 x86-current-d5-zerop-u64-safe?
  (00001000 (value)
    (00000111
      ((x86-admission-exact-integer? value)
       (x86-admission-within-inclusive-integer-range?
         value 0 18446744073709551615))
      (t (00000001 ())))))

(00001001 x86-lower-zerop-u64-forms
  (00001000 (value)
    (00100111
      (00100111 (00000001 mov-r64-imm64) (00000001 rax) value)
      (00100111 (00000001 mov-r64-imm64) (00000001 rcx) 0)
      (00100111 (00000001 cmp-r64-r64) (00000001 rax) (00000001 rcx))
      (00100111 (00000001 sete-r8) (00000001 al))
      (00100111 (00000001 movzx-r64-r8) (00000001 rax) (00000001 al))
      (00100111 (00000001 ret)))))

(00001001 x86-lower-current-zerop-u64-forms
  (00001000 (width bits value)
    (00000111
      ((x86-current-domain-key? width bits 5 8)
       (00000111
         ((x86-current-d5-zerop-u64-safe? value)
          (x86-lower-zerop-u64-forms value))
         (t (00000001 exact-d5-fallback-required))))
      (t
       (00000001 unsupported-current-domain-zerop-u64)))))

(00001001 x86-encode-current-zerop-bit
  (00001000 (width bits value)
    (10011100
      ((forms (x86-lower-current-zerop-u64-forms width bits value)))
      (00000111
        ((00100010 forms (00000001 unsupported-current-domain-zerop-u64))
         (00000001 unsupported-current-domain-zerop-u64))
        ((00100010 forms (00000001 exact-d5-fallback-required))
         (00000001 exact-d5-fallback-required))
        (t
         (x86-encode-admitted-program forms))))))

; #3996 exact-domain structural D3 dispatcher.
; These are bounded native-call witnesses only. They do not claim a general
; allocator, escaping pair ABI, GC, or arbitrary first-class native pair value.
(00001001 x86-lower-current-structural-u64-forms
  (00001000 (width bits left right)
    (00000111
      ((x86-current-domain-key? width bits 3 7)
       (x86-lower-bounded-pair-store-u64-forms left right))
      ((x86-current-domain-key? width bits 3 4)
       (x86-lower-cons-car-u64-forms left right))
      ((x86-current-domain-key? width bits 3 3)
       (x86-lower-cons-cdr-u64-forms left right))
      (t
       (00000001 unsupported-current-domain-structural-u64)))))

(00001001 x86-encode-current-structural-u64
  (00001000 (width bits left right)
    (10011100 ((forms
                  (x86-lower-current-structural-u64-forms
                    width bits left right)))
      (00000111
        ((00100010 forms (00000001 unsupported-current-domain-structural-u64))
         (00000001 unsupported-current-domain-structural-u64))
        (t
         (x86-encode-admitted-program-or-reject forms))))))

; #4000 exact-domain bounded composition for current D3 EQ + COND.
; This route intentionally does not expose an independent numeric-boolean EQ
; machine API. The equality decision stays internal to the already-witnessed
; two-arm composition; the language boundary remains exact D1/EMPTY according
; to current D3 law.
(00001001 x86-lower-current-eq-cond-u64-forms
  (00001000
    (eq-width eq-bits cond-width cond-bits left right then-value else-value)
    (00000111
      ((x86-current-domain-key? eq-width eq-bits 3 5)
       (00000111
         ((x86-current-domain-key? cond-width cond-bits 3 6)
          (x86-lower-eq-cond-u64-forms
            left right then-value else-value))
         (t
          (00000001 unsupported-current-domain-eq-cond-u64))))
      (t
       (00000001 unsupported-current-domain-eq-cond-u64)))))

(00001001 x86-encode-current-eq-cond-u64
  (00001000
    (eq-width eq-bits cond-width cond-bits left right then-value else-value)
    (10011100 ((forms
            (x86-lower-current-eq-cond-u64-forms
              eq-width eq-bits cond-width cond-bits
              left right then-value else-value)))
      (00000111
        ((00100010 forms (00000001 unsupported-current-domain-eq-cond-u64))
         (00000001 unsupported-current-domain-eq-cond-u64))
        (t
         (x86-encode-admitted-program-or-reject forms))))))


