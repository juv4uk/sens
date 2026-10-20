; #3989/#4068 — чинна машинна проєкція x86-64 для точних доменів.
;
; Рядки зіставлення семантики та машинних форм для мешканців
; Контракту 11.8, уже підтверджених незалежними свідками.
; Ключ — (ширина домену, упаковані біти), а не вихідне текстове слово.
;
; У Д5:01010 і Д4:1010 упаковані біти однакові (10), тому
; ширина є обов'язковою частиною тотожності. Семантика не
; виводиться з історичного байта SID8 або людської назви.

(machine-domain-profile/2
  (target x86-64)
  (cpu intel-core-i5-6400)
  (key-shape width+packed-bits)
  (rows
    (5 8 proof "CMP+SETE+MOVZX / exact integer internal bit; D1 boundary") ; Д5:01000 — нуль?
    (5 10 fast-path "ADD / u32 inputs -> exact u64 result")      ; Д5:01010 — додати
    (5 11 fast-path "SUB / u64, left>=right")                   ; Д5:01011 — відняти
    (5 22 fast-path "IMUL / u32 inputs -> exact u64 result")     ; Д5:10110 — помножити
    (5 23 fast-path "CQO+IDIV / positive i64 equal operands")    ; Д5:10111 — частка
    (5 26 proof "CMP+SETL+MOVZX / internal bit; D1 boundary")    ; Д5:11010 — менше?
    (5 27 proof "CMP+SETG+MOVZX / internal bit; D1 boundary")    ; Д5:11011 — більше?
    (6 14 fast-path "ADD / exact u64 input <= u64-2, RHS=1")  ; Д6:001110 — додати-1
    (6 15 fast-path "SUB / exact u64 input >=1, RHS=1")        ; Д6:001111 — відняти-1
    (3 5 direct "CMP/SETE")                                      ; Д3:101 — тотожне?
    (3 6 control "CMP+Jcc")                                      ; Д3:110 — за-умовою
    (3 7 runtime "STORE-pair-head+tail")                         ; Д3:111 — сполучити
    (3 4 direct "LOAD-pair-head")                                ; Д3:100 — перше
    (3 3 direct "LOAD-pair-tail")))                              ; Д3:011 — решта
