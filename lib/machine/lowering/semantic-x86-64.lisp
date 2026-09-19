; Semantic -> x86-64 lowering projection.
; Language meaning remains owned by lib/surface/semantic-registry.lisp.
; ISA identity/encoding remains owned by lib/machine/isa + lib/machine/encoding.
; Rows here only say how an already-existing semantic identity may be realized.
;
; Executable lowerings produce structured machine forms. Byte materialization
; belongs to the closed Lisp-owned admission layer and is deliberately not
; re-exported from semantic lowering as a compatibility convenience.

(def x86-semantic-lowering-profile
  (quote
    (("00000010" sequence "tag-test: TEST/AND/CMP")
     ("00000011" direct "CMP/SETE")
     ("00000100" runtime "allocate+STORE-pair")
     ("00000101" direct "LOAD-pair-head")
     ("00000110" direct "LOAD-pair-tail")
     ("00000111" control "TEST/CMP+Jcc")

     ("00001100" fast-path "ADD / ADDSD")
     ("00001101" fast-path "SUB/NEG / SUBSD")
     ("00001110" fast-path "IMUL / MULSD")
     ("00001111" fast-path "DIVSD; exact-rational routine")
     ("00010000" sequence "TEST/NEG/CMOV")
     ("00010001" sequence "CMP/CMOV-min")
     ("00010010" sequence "CMP/CMOV-max")
     ("00010011" fast-path "IDIV-remainder")
     ("00010100" fast-path "IDIV-quotient")
     ("00010101" fast-path "SQRTSD")
     ("00010110" runtime "integer-sqrt routine")
     ("00010111" runtime "loop+CMP/CMOV-min")
     ("00011000" runtime "loop+CMP/CMOV-max")
     ("00011010" direct "CMP/SETL")
     ("00011011" direct "CMP/SETG")
     ("00011100" direct "CMP/SETE")
     ("00011101" direct "CMP/SETLE")
     ("00011110" direct "CMP/SETGE")
     ("00100001" direct "TEST/SETE")

     ("00100011" sequence "tag-test: symbol")
     ("00100100" sequence "tag-test: string")
     ("00100110" sequence "tag-test: numeric-buffer")
     ("00101000" runtime "list-walk+LOAD-pair-tail")
     ("00101011" runtime "indexed-list-walk+LOAD")
     ("00101111" sequence "LOAD-tail+LOAD-head")
     ("00110000" sequence "2xLOAD-tail+LOAD-head")
     ("00110001" sequence "3xLOAD-tail+LOAD-head")
     ("00110010" sequence "4xLOAD-tail+LOAD-head")
     ("00110011" sequence "LOAD-head+LOAD-head")
     ("00110100" sequence "LOAD-tail+LOAD-head")
     ("00110101" sequence "LOAD-tail+LOAD-tail")
     ("00110110" sequence "3xLOAD-tail+LOAD-head")

     ("01001111" runtime "allocate+STORE-vector")
     ("01010000" runtime "allocate+fill-vector")
     ("01010001" direct "LOAD-vector-length")
     ("01010010" direct "LOAD-vector-element")
     ("01010011" direct "STORE-vector-element")
     ("01010100" runtime "allocate+STORE-i32-buffer")
     ("01010101" runtime "allocate+STORE-f32-buffer")
     ("01010110" direct "LOAD-buffer-tag")
     ("01010111" direct "LOAD-buffer-length")
     ("01011000" direct "LOAD-buffer-element")
     ("01011001" runtime "loop; AVX2 specialization possible")

     ("01100001" fast-path "IDIV/IMUL-reciprocal")
     ("01100110" direct "CMP/SETGE")
     ("01100111" direct "CMP/SETGE")
     ("01101000" direct "SUB")
     ("01101001" direct "ADD")
     ("01101010" direct "ADD")

     ("01110001" runtime "empty-vector object")
     ("01110010" runtime "allocate+copy+STORE-vector")
     ("01110011" direct "LOAD-vector-length")
     ("01110100" direct "LOAD-vector-element")

     ("10011000" direct "MOV/pass-through")
     ("10011010" control "short-circuit TEST/Jcc")
     ("10011011" control "short-circuit TEST/Jcc"))))

; First executable semantic-lowering witness.
; Semantic identity 00001100 already exists before this file is loaded. This
; routine does not define addition; it chooses one bounded u64 realization.
; It returns structured machine forms only. Admission owns the path from those
; forms to executable bytes.
;
; RAX carries the result per SysV x86-64. RCX is caller-saved, so the proof
; routine does not violate the host ABI by clobbering a callee-saved register.
(def x86-lower-add-u64-forms
  (lambda (left right)
    (list
      (list (quote mov-r64-imm64) (quote rax) left)
      (list (quote mov-r64-imm64) (quote rcx) right)
      (list (quote add-r64-r64) (quote rax) (quote rcx))
      (list (quote ret)))))

; #196 bounded conditional-growth witness for existing EQ + COND semantics.
; This routine does not define equality or conditional evaluation. It chooses
; one fixed-width u64 realization whose only purpose is to establish the
; machine-effect lower bound demanded by a two-arm runtime decision.
;
; JNZ +11 skips exactly one MOV r64,imm64 (10 bytes) plus one RET (1 byte),
; landing at the ELSE arm. This is deliberately not a general label resolver,
; branch assembler, or compiler policy. It returns structured forms only;
; closed admission remains the sole path to bytes.
(def x86-lower-eq-cond-u64-forms
  (lambda (left right then-value else-value)
    (list
      (list (quote mov-r64-imm64) (quote rax) left)
      (list (quote mov-r64-imm64) (quote rcx) right)
      (list (quote cmp-r64-r64) (quote rax) (quote rcx))
      (list (quote jnz-rel8) 11)
      (list (quote mov-r64-imm64) (quote rax) then-value)
      (list (quote ret))
      (list (quote mov-r64-imm64) (quote rax) else-value)
      (list (quote ret)))))

; #196 conditional+structural composition helper. Each branch constructs one
; bounded pair in the same native-call arena and returns its CAR. The caller
; selects distinct caller-saved extended GPRs so #207's widened MOV imm64
; admission is exercised by semantic composition rather than by an ISA-only
; witness. RAX remains the guest ABI result register.
(def x86-lower-bounded-car-cons-u64-arm-forms
  (lambda (left right left-register right-register)
    (list
      (list (quote mov-r64-imm64) left-register left)
      (list
        (quote mov-mem-disp8-r64)
        (quote rdi)
        x86-pair-car-offset
        left-register)
      (list (quote mov-r64-imm64) right-register right)
      (list
        (quote mov-mem-disp8-r64)
        (quote rdi)
        x86-pair-cdr-offset
        right-register)
      (list
        (quote mov-r64-mem-disp8)
        (quote rax)
        (quote rdi)
        x86-pair-car-offset)
      (list (quote ret)))))

; Third bounded #196 slice: compose runtime COND/EQ choice with structural
; CAR(CONS ...) branch bodies. This remains deliberately finite: JNZ +33 skips
; exactly one six-form CAR(CONS) arm (10+4+10+4+4+1 bytes with base RDI), and
; each arm returns directly. No label resolver, register allocator, GC, or
; general recursive expression lowering is claimed here.
(def x86-lower-eq-cond-car-cons-u64-forms
  (lambda (left right then-car then-cdr else-car else-cdr)
    (append
      (list
        (list (quote mov-r64-imm64) (quote rax) left)
        (list (quote mov-r64-imm64) (quote rcx) right)
        (list (quote cmp-r64-r64) (quote rax) (quote rcx))
        (list (quote jnz-rel8) 33))
      (append
        (x86-lower-bounded-car-cons-u64-arm-forms
          then-car then-cdr (quote r8) (quote r9))
        (x86-lower-bounded-car-cons-u64-arm-forms
          else-car else-cdr (quote r10) (quote r11))))))

; Bounded structural witness for semantic identities 00000100/00000101/00000110.
; The host contributes only a raw writable arena pointer in RDI. Lisp owns
; the fact that one admitted pair cell has head at x86-pair-car-offset and
; tail at x86-pair-cdr-offset. These routines produce structured STORE/LOAD
; forms; admission and the encoder produce physical bytes only afterwards.
;
; This is deliberately not a claim that arbitrary first-class pair values may
; already escape native code: pair-x86-64.lisp fixes lifetime=native-call and
; escape=forbidden for this proof slice.
(def x86-lower-bounded-pair-store-u64-forms
  (lambda (left right)
    (list
      (list (quote mov-r64-imm64) (quote rax) left)
      (list
        (quote mov-mem-disp8-r64)
        (quote rdi)
        x86-pair-car-offset
        (quote rax))
      (list (quote mov-r64-imm64) (quote rax) right)
      (list
        (quote mov-mem-disp8-r64)
        (quote rdi)
        x86-pair-cdr-offset
        (quote rax)))))

; Historical internal name retained only as a form-level alias so existing
; Lisp callers do not regain a byte-level bypass.
(def x86-lower-bounded-pair-store-u64-instructions
  x86-lower-bounded-pair-store-u64-forms)

(def x86-lower-cons-car-u64-forms
  (lambda (left right)
    (append
      (x86-lower-bounded-pair-store-u64-forms left right)
      (list
        (list
          (quote mov-r64-mem-disp8)
          (quote rax)
          (quote rdi)
          x86-pair-car-offset)
        (list (quote ret))))))

(def x86-lower-cons-cdr-u64-forms
  (lambda (left right)
    (append
      (x86-lower-bounded-pair-store-u64-forms left right)
      (list
        (list
          (quote mov-r64-mem-disp8)
          (quote rax)
          (quote rdi)
          x86-pair-cdr-offset)
        (list (quote ret))))))

; Bounded semantic entry for the Vertical Day CAR witness.
; Canonical CAR/CDR own pair validity and therefore fail with the language's
; existing Type outcome before any machine request exists. Only after that
; language-owned gate succeeds do the extracted u64 fields become structured
; machine forms, pass closed admission, and enter the semantics-blind host.
; No pair predicate or tag rule is duplicated in this machine layer.
(def x86-call-semantic-car-u64
  (lambda (pair-value)
    (x86-call-admitted-u64
      (x86-lower-cons-car-u64-forms
        (car pair-value)
        (cdr pair-value))
      x86-pair-cell-bytes)))
