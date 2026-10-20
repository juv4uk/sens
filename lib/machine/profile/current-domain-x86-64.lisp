; #3989/#4068 — чинна машинна проєкція x86-64 для точних доменів.
;
; Рядки зіставлення семантики та машинних форм для мешканців
; Контракту 11.8, уже підтверджених незалежними свідками.
; Ключ — (ширина домену, упаковані біти), а не вихідне текстове слово.
;
; У D5:01010 і D4:1010 упаковані біти однакові (10), тому
; ширина є обов'язковою частиною тотожності. Семантика не
; виводиться з історичного байта SID8 або людської назви.

(machine-domain-profile/2
  (target x86-64)
  (cpu intel-core-i5-6400)
  (key-shape width+packed-bits)
  (rows
    (5 8 proof "CMP+SETE+MOVZX / exact integer internal bit; D1 boundary") ; D5 ZEROP
    (5 10 fast-path "ADD / u32 inputs -> exact u64 result")      ; D5 PLUS
    (5 11 fast-path "SUB / u64, left>=right")                   ; D5 DIFFERENCE
    (5 22 fast-path "IMUL / u32 inputs -> exact u64 result")     ; D5 TIMES
    (5 23 fast-path "CQO+IDIV / positive i64 equal operands")    ; D5 QUOTIENT
    (5 26 proof "CMP+SETL+MOVZX / internal bit; D1 boundary")    ; D5 LESSP
    (5 27 proof "CMP+SETG+MOVZX / internal bit; D1 boundary")    ; D5 GREATERP
    (6 14 fast-path "ADD / exact u64 input <= u64-2, RHS=1")  ; D6 ADD1
    (6 15 fast-path "SUB / exact u64 input >=1, RHS=1")        ; D6 SUB1
    (3 5 direct "CMP/SETE")                                      ; D3 EQ
    (3 6 control "CMP+Jcc")                                      ; D3 COND
    (3 7 runtime "STORE-pair-head+tail")                         ; D3 CONS
    (3 4 direct "LOAD-pair-head")                                ; D3 CAR
    (3 3 direct "LOAD-pair-tail")))                              ; D3 CDR
