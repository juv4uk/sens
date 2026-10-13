; Фізичний SENS-закон всередині Lisp: D3 COND вирішує наслідки.
; Хост не встановлює truth table. Неправильний наслідок викликає D3 CAR().
; Відповідні exact heads: D3:110 COND, D3:001 QUOTE, D3:100 CAR,
; D4:0101 NULL, D4:0100 NOT, D1:1 — останній guard.
; Три незалежні точнодоменні SENS-вердикти над незмінним snapshot.
; Не вводимо D24; останній field тут символьний, не математична ревізія.
; Правильний об'єкт = (objects bindings revision).
(110
  ((101 (fs-objects (1110 (001 objects) (001 bindings) (001 revision)))
        (001 objects))
   #d1:1)
  (#d1:1 (100 (001 ()))))
(110
  ((101 (fs-bindings (1110 (001 objects) (001 bindings) (001 revision)))
        (001 bindings))
   #d1:1)
  (#d1:1 (100 (001 ()))))
(110
  ((101 (fs-revision (1110 (001 objects) (001 bindings) (001 revision)))
        (001 revision))
   #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((fs-package-has-field? (001 format) (001 ((format . wsm-fs-event))))
   (110
     ((0100 (fs-package-has-field? (001 format) (001 (broken))))
      (110
        ((0101 (fs-package-field (001 format) (001 (broken))))
         (110
           ((0100 (fs-package-has-field? (001 format) (001 (((broken-key) . value)))))
            (110
              ((0101 (fs-package-field (001 format) (001 (((broken-key) . value)))))
               (110
                 ((101 (100 (fs-journal-event-decision (001 (broken))))
                       (001 rejected))
                  (001 structural-law-pass))
                 (#d1:1 (100 (001 ())))))
              (#d1:1 (100 (001 ())))))
           (#d1:1 (100 (001 ())))))
        (#d1:1 (100 (001 ())))))
     (#d1:1 (100 (001 ())))))
  (#d1:1 (100 (001 ()))))
