; Executable SENS law: negative results of CURRENT meta-eval predicates
; are exact one-bit D1:NO, not structural D3 empty.
; The only semantic tests are SENS D3 EQ/COND; helper names resolve to
; existing library functions, not host-language replacement implementations.
; Run with lib/meta-eval.lisp loaded first, then this form.
(110
  ((101 (my-macro? (001 sample)) #d1:1)
    (110
      ((101 (my-closure? (001 sample)) #d1:0)
        (110
          ((101 (my-recursive-closure? (001 sample)) #d1:0)
            (110
              ((101 (my-rest-param? (001 ())) #d1:0)
                #d1:1)
              (#d1:1 (#d1:0))))
          (#d1:1 (#d1:0))))
      (#d1:1 (#d1:0))))
  (#d1:1 (#d1:0)))
