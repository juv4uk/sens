; lib/macro.lisp — bootstrap макровизначення на точних доменах.
;
; Migrated: COND fallback is exact D1:1 (010 (001 ())). Width is identity;
; every bit of the domain address is valued. No host truthiness.
;
; Семантична identity тут уже не 8-бітна площина:
;   D3:001 QUOTE, D3:010 ATOM, D3:011 CDR, D3:100 CAR,
;   D3:110 COND, D3:111 CONS, D4:0010 LAMBDA, D4:0011 DEFINE.
;
; `make-macro` — вузький host-substrate Closure -> Macro. Він не створює
; окремої SENS identity. Сам DEFMACRO лишається мовно-виведеним.
;
; Дві цитовані форми 0010/0011 нижче є саме code-data identities. Path-pinned
; reader lib/macro.lisp матеріалізує їх як D4 DomainIdentity, не як числа.
;
; Reuses (2000+ surface): D3 ATOM/EQ/CAR/CDR/COND/CONS, D4 LAMBDA/DEFINE,
; make-macro host substrate only for Closure->Macro tag.

(make-macro
  (функція args
    (за-умовою
      ((атом? args)
       (make-macro))
      ((атом? (решта args))
       (make-macro))
      ((атом? (як-є ()))
       (сполучити (як-є 0011)
         (сполучити (перше args)
           (сполучити
             (сполучити (як-є make-macro)
               (сполучити
                 (сполучити (як-є 0010)
                   (сполучити
                     (перше (решта args))
                     (решта (решта args))))
                 (як-є ())))
             (як-є ()))))))))
