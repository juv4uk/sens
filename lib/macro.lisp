; lib/macro.lisp — bootstrap макровизначення на точних доменах.
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

(make-macro
  (0010 args
    (110
      ((010 args)
       (make-macro))
      ((010 (011 args))
       (make-macro))
      ((010 (001 ()))
       (111 (001 0011)
         (111 (100 args)
           (111
             (111 (001 make-macro)
               (111
                 (111 (001 0010)
                   (111
                     (100 (011 args))
                     (011 (011 args))))
                 (001 ())))
             (001 ()))))))))
