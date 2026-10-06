; #3989 — current exact-domain x86-64 machine projection.
;
; This is the current semantic->machine projection for already-witnessed
; Contract 11.8 residents. Keys are exact domain literals; their width is part
; of identity. This file does not infer meaning from a historical SID8 byte.
;
; It is intentionally small. Rows are admitted only when an existing machine
; witness already proves the realization.

(machine-domain-profile/1
  (target x86-64)
  (cpu intel-core-i5-6400)
  (rows
    (01010 fast-path "ADD / u32 inputs -> exact u64 result")     ; D5 PLUS
    (01011 fast-path "SUB / u64, left>=right")     ; D5 DIFFERENCE
    (10110 fast-path "IMUL / u32 inputs -> exact u64 result")    ; D5 TIMES
    (101 direct "CMP/SETE")                        ; D3 EQ
    (110 control "CMP+Jcc")                        ; D3 COND
    (111 runtime "STORE-pair-head+tail")           ; D3 CONS
    (100 direct "LOAD-pair-head")                  ; D3 CAR
    (011 direct "LOAD-pair-tail")))                ; D3 CDR
