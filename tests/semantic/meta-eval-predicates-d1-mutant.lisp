; Executable SENS law: negative results of CURRENT meta-eval predicates
; are exact one-bit D1:NO, not structural D3 empty.
; The only semantic tests are SENS D3 EQ/COND; helper names resolve to
; existing library functions, not host-language replacement implementations.
; Run with lib/meta-eval.lisp loaded first, then this form.
(110
  ((101 (my-macro? (001 sample)) #d1:1)
    (110
      ((тотожне? (це-замикання? (як-є sample)) ні)
        (110
          ((тотожне? (це-рекурсивне-замикання? (як-є sample)) ні)
            (110
              ((тотожне? (лямбда-має-параметр-залишку? (як-є ())) ні)
                #d1:1)
              (#d1:1 (#d1:0))))
          (#d1:1 (#d1:0))))
      (#d1:1 (#d1:0))))
  (#d1:1 (#d1:0)))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити це-замикання? my-closure?)
(визначити це-рекурсивне-замикання? my-recursive-closure?)
(визначити лямбда-має-параметр-залишку? my-rest-param?)
