; SENS-owned semantics: two shapes of provenance narration after D6 LET -> D4 LAMBDA.
; Human names below are lexical bindings, not new domain residents.
; Head widths: D3:010/101/100/011/110, D4:0010/0011, list D4:1110.
; D1 is explicitly tagged in this mixed .lisp fixture.

(0011 оповідь--рівні?
  (0010 (a b)
    (110
      ((010 a)
       (110
         ((010 b) (101 a b))
         (#d1:1 #d1:0)))
      ((010 b) #d1:0)
      ((оповідь--рівні? (100 a) (100 b))
       (оповідь--рівні? (011 a) (011 b)))
      (#d1:1 #d1:0))))

(0011 оповідь--d4-закон
  (0010 ()
    (110
      ((оповідь--рівні?
         (narrate-answer
           (001 (planet earth))
           (001 (statement (planet earth) (source fact) (rule (planet earth))
                    (derived-from ()))))
         (001 (earth is a planet)))
       (110
         ((оповідь--рівні?
            (narrate-answer
              (001 (planet earth))
              (001 (statement (planet earth) (source rule) (rule (planet earth))
                       (derived-from
                         ((statement (planet mars) (source fact) (rule (planet mars))
                           (derived-from ())))))))
            (001 (earth is a planet because mars is a planet)))
          #d1:1)
         (#d1:1 #d1:0)))
      (#d1:1 #d1:0))))

(оповідь--d4-закон)
