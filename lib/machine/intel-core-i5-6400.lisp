; Історична сумісна проєкція SID8 для Intel Core i5-6400 / Skylake.
;
; Цей файл НЕ є чинним джерелом семантичних повноважень.
; Він зберігає стару побайтову проєкцію SID лише для сумісності
; та відстеження походження. Сучасні рядки точних доменів розміщено
; в lib/machine/profile/current-domain-x86-64.lisp; їхні ключі —
; точні значення DomainIdentity, а не історичні байти SID8.
;
; Проєкція розрізняє швидкий шлях з однієї або кількох інструкцій
; та повнішу реалізацію Lisp/виконавця. Наприклад, дія `+` зберігає
; необмежену точну арифметику, хоча малі цілі числа допускають ADD.
;
; Схема одного рядка:
;   (semantic-id class "machine path")
;
; Класи є лише описом механізмів, а не новими значеннями мови:
;   direct    — одна або декілька звичайних інструкцій ISA;
;   fast-path — прискорення лише в доведених межах; інші входи — Lisp;
;   sequence  — послідовність кількох інструкцій ISA;
;   runtime   — потрібні виділення пам'яті, обхід або стан виконавця;
;   control   — керувальний потік процесора.
(machine-profile/1
  (cpu intel-core-i5-6400)
  (microarchitecture skylake)
  (isa x86-64)
  (rows
    (00000010 sequence "tag-test: TEST/AND/CMP")
    (00000011 direct "CMP/SETE")
    (00000100 runtime "allocate+STORE-pair")
    (00000101 direct "LOAD-pair-head")
    (00000110 direct "LOAD-pair-tail")
    (00000111 control "TEST/CMP+Jcc")

    (додати fast-path "ADD / ADDSD")
    (відняти fast-path "SUB/NEG / SUBSD")
    (помножити fast-path "IMUL / MULSD")
    (поділити fast-path "DIVSD; exact-rational routine")
    (модуль sequence "TEST/NEG/CMOV")
    (найменше sequence "CMP/CMOV-min")
    (найбільше sequence "CMP/CMOV-max")
    (модульна-остача fast-path "IDIV-remainder")
    (00010100 fast-path "IDIV-quotient")
    (корінь fast-path "SQRTSD")
    (цілий-корінь runtime "integer-sqrt routine")
    (найменше-у-списку runtime "loop+CMP/CMOV-min")
    (найбільше-у-списку runtime "loop+CMP/CMOV-max")
    (менше? direct "CMP/SETL")
    (більше? direct "CMP/SETG")
    (00011100 direct "CMP/SETE")
    (00011101 direct "CMP/SETLE")
    (00011110 direct "CMP/SETGE")
    (хибне? direct "TEST/SETE")

    (символ? sequence "tag-test: symbol")
    (00100100 sequence "tag-test: string")
    (00100110 sequence "tag-test: numeric-buffer")
    (довжина runtime "list-walk+LOAD-pair-tail")
    (елемент-списку-за-індексом runtime "indexed-list-walk+LOAD")
    (00101111 sequence "LOAD-tail+LOAD-head")
    (00110000 sequence "2xLOAD-tail+LOAD-head")
    (четверте sequence "3xLOAD-tail+LOAD-head")
    (п'ятий sequence "4xLOAD-tail+LOAD-head")
    (перше-першого sequence "LOAD-head+LOAD-head")
    (друге sequence "LOAD-tail+LOAD-head")
    (решта-решти sequence "LOAD-tail+LOAD-tail")
    (четверте sequence "3xLOAD-tail+LOAD-head")

    (вектор runtime "allocate+STORE-vector")
    (створити-вектор runtime "allocate+fill-vector")
    (довжина-вектора direct "LOAD-vector-length")
    (елемент-вектора direct "LOAD-vector-element")
    (встановити-елемент-вектора! direct "STORE-vector-element")
    (цілий-32-буфер runtime "allocate+STORE-i32-buffer")
    (дійсний-32-буфер runtime "allocate+STORE-f32-buffer")
    (числовий-буфер-тип direct "LOAD-buffer-tag")
    (числовий-буфер-довжина direct "LOAD-buffer-length")
    (числовий-буфер-посилання direct "LOAD-buffer-element")
    (числовий-буфер-мапа runtime "loop; AVX2 specialization possible")

    (мілісекунди-з-наносекунди fast-path "IDIV/IMUL-reciprocal")
    (крайній-час-досягнуто? direct "CMP/SETGE")
    (крайній-час-досягнуто-у? direct "CMP/SETGE")
    (минуло-нс direct "SUB")
    (крайній-час-з direct "ADD")
    (крайній-час-після-нс direct "ADD")

    (вектор-порожній runtime "empty-vector object")
    (вектор-додати runtime "allocate+copy+STORE-vector")
    (вектор-кількість direct "LOAD-vector-length")
    (вектор-н-тий direct "LOAD-vector-element")

    (тотожність direct "MOV/pass-through")
    (та control "short-circuit TEST/Jcc")
    (або control "short-circuit TEST/Jcc")
  ))
