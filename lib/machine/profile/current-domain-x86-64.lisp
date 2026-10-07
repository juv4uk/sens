; #4068 — current width-safe exact-domain x86-64 machine projection.
;
; This is the current semantic->machine projection for already-witnessed
; Contract 11.8 residents. Each row carries DomainIdentity::width() and
; DomainIdentity::packed_bits() as separate scalar fields, so ordinary Lisp
; reader width loss (#3946) cannot collapse D5:01010 into D4:1010.
;
; Row schema:
;   (domain-width packed-bits class "machine path")

(machine-domain-profile/2
  (target x86-64)
  (cpu intel-core-i5-6400)
  (rows
    (5 10 fast-path "ADD / u32 inputs -> exact u64 result")       ; D5:01010 PLUS
    (5 11 fast-path "SUB / u64, left>=right")                    ; D5:01011 DIFFERENCE
    (5 22 fast-path "IMUL / u32 inputs -> exact u64 result")      ; D5:10110 TIMES
    (5 23 fast-path "CQO+IDIV / positive i64 equal operands")    ; D5:10111 QUOTIENT
    (5 26 proof "CMP+SETL+MOVZX / internal bit; D1 boundary")    ; D5:11010 LESSP
    (5 27 proof "CMP+SETG+MOVZX / internal bit; D1 boundary")    ; D5:11011 GREATERP
    (3 5 direct "CMP/SETE")                                      ; D3:101 EQ
    (3 6 control "CMP+Jcc")                                      ; D3:110 COND
    (3 7 runtime "STORE-pair-head+tail")                         ; D3:111 CONS
    (3 4 direct "LOAD-pair-head")                                ; D3:100 CAR
    (3 3 direct "LOAD-pair-tail")))                              ; D3:011 CDR
