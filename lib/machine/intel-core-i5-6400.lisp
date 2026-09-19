; Intel Core i5-6400 / Skylake execution projection for existing my-lisp identities.
;
; This file is NOT a semantic registry and does not create language meaning.
; `lib/surface/semantic-registry.lisp` remains the only authority for semantic
; identities and human surfaces.  Each row here is keyed by an existing
; semantic ID and records a plausible physical realization on this processor.
;
; The projection deliberately distinguishes a one/few-instruction fast path
; from a wider Lisp/runtime implementation.  For example `+` keeps arbitrary-
; precision exact semantics even though small exact integers can use ADD.
;
; Row schema:
;   (semantic-id class "machine path")
;
; class is descriptive only:
;   direct    — one/few ordinary ISA operations are the natural realization
;   fast-path — ISA operation covers a bounded representation; Lisp fallback remains
;   sequence  — several ordinary ISA operations implement the semantic action
;   runtime   — allocation/iteration/runtime state is required
;   control   — maps naturally to CPU control flow

(machine-profile/1
  (cpu intel-core-i5-6400)
  (microarchitecture skylake)
  (isa x86-64)
  (rows
    ("00000010" sequence "tag-test: TEST/AND/CMP")
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
    ("10011011" control "short-circuit TEST/Jcc")
  ))
