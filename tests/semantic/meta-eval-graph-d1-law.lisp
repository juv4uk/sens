; SENS-owned D1 verdict over current meta-eval dependency helpers.
; D3 EQ/COND own every expectation. No host-language truth table.
; Native replay must load lib/meta-eval.lisp before this form.
(110
  ((101 (my-cond-has-migration-clause? (001 ())) #d1:0)
    (110
      ((101 (my-cond-has-migration-clause? (111 (111 (001 datum) (001 ())) (001 ()))) #d1:0)
        (110
          ((тотожне? (ім'я-зв'язане-формальними-параметрами? (як-є requested) (як-є ())) ні)
            (110
              ((тотожне? (ім'я-зв'язане-формальними-параметрами? (як-є requested) (як-є other)) ні)
                (110
                  ((тотожне? (ім'я-зв'язане-формальними-параметрами? (як-є requested) (як-є requested)) так)
                    (110
                      ((101 (my-forms-reference-name? (001 ()) (001 requested)) #d1:0)
                        (110
                          ((101 (my-graph-dependencies-reach? (001 ()) (001 requested) (001 ()) (001 ())) #d1:0)
                            #d1:1)
                          (#d1:1 (#d1:0))))
                      (#d1:1 (#d1:0))))
                  (#d1:1 (#d1:0))))
              (#d1:1 (#d1:0))))
          (#d1:1 (#d1:0))))
      (#d1:1 (#d1:0))))
  (#d1:1 (#d1:0)))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити ім'я-зв'язане-формальними-параметрами? my-params-bind-name?)
