; #3989/#4068 — current exact-domain x86-64 machine projection.
;
; Current semantic->machine rows for already-witnessed Contract 11.8 residents.
; Live keys are (domain-width, packed-bits), not source binary lexemes.
;
; D5:01010 and D4:1010 both have packed_bits=10, so width MUST be present.
; These rows never infer meaning from a historical SID8 byte or a spelling.

(machine-domain-profile/2
  (target x86-64)
  (cpu intel-core-i5-6400)
  (key-shape width+packed-bits)
  (rows
    (5 10 fast-path "ADD / u32 inputs -> exact u64 result")      ; D5 PLUS
    (5 11 fast-path "SUB / u64, left>=right")                   ; D5 DIFFERENCE
    (5 22 fast-path "IMUL / u32 inputs -> exact u64 result")     ; D5 TIMES
    (5 23 fast-path "CQO+IDIV / positive i64 equal operands")    ; D5 QUOTIENT
    (5 26 proof "CMP+SETL+MOVZX / internal bit; D1 boundary")    ; D5 LESSP
    (5 27 proof "CMP+SETG+MOVZX / internal bit; D1 boundary")    ; D5 GREATERP
    (3 5 direct "CMP/SETE")                                      ; D3 EQ
    (3 6 control "CMP+Jcc")                                      ; D3 COND
    (3 7 runtime "STORE-pair-head+tail")                         ; D3 CONS
    (3 4 direct "LOAD-pair-head")                                ; D3 CAR
    (3 3 direct "LOAD-pair-tail")))                              ; D3 CDR
