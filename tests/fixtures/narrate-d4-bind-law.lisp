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

(0011 оповідь--старе-нове?
  (0010 (proof)
    (оповідь--рівні?
      (provenance-derived-from (provenance proof))
      (provenance-list (100111 proof)))))

(0011 оповідь--d4-закон
  (0010 ()
    (110
      ((оповідь--рівні?
         (narrate-answer
           (001 (planet earth))
           (001 (proved (planet earth) (planet earth) ())))
         (001 (earth is a planet)))
       (110
         ((оповідь--рівні?
            (narrate-answer
              (001 (planet earth))
              (001 (proved (planet earth) (planet earth)
                       ((proved (planet mars) (planet mars) ())))))
            (001 (earth is a planet because mars is a planet)))
          (110
            ((оповідь--старе-нове?
               (001 (proved (planet earth) (planet earth)
                       ((proved (planet mars) (planet mars) ())))))
             #d1:1)
            (#d1:1 #d1:0)))
         (#d1:1 #d1:0)))
      (#d1:1 #d1:0))))

; D3 atom/eq dispatch must reject numeric and pair tags WITHOUT D9 SYMBOL?.
; SENS itself compares expected and actual; the host observes only final D1.
(0011 оповідь--перевірка-тегів
  (0010 (rows)
    (110
      ((010 rows) #d1:1)
      ((оповідь--рівні? (100 (100 rows)) (1001 (100 rows)))
       (оповідь--перевірка-тегів (011 rows)))
      (#d1:1 #d1:0))))

(0011 оповідь--теги-закон
  (0010 ()
    (оповідь--перевірка-тегів
      (1110
        (1110 (narrate-outcome (001 (42 payload)))
              (001 (invalid outcome-tag 42)))
        (1110 (narrate-outcome (001 ((bad-tag) payload)))
              (001 (invalid outcome-tag (bad-tag))))
        (1110 (narrate-outcome (001 (mystery payload)))
              (001 (invalid outcome-tag mystery)))
        (1110 (narrate-outcome (001 (() payload)))
              (001 (invalid outcome-tag ())))
        (1110 (narrate-outcome (001 (unknown)))
              (001 (invalid outcome-shape (unknown))))
        (1110 (narrate-outcome (001 (blocked dependency)))
              (001 (blocked because dependency)))
        (1110 (narrate-outcome (001 (unknown subject)))
              (001 (unknown because no-proof-found-for subject)))))))

(0011 оповідь--загальний-закон
  (0010 ()
    (110
      ((оповідь--теги-закон) (оповідь--d4-закон))
      (#d1:1 #d1:0))))

(оповідь--загальний-закон)
