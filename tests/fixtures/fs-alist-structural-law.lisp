; Фізичний SENS-закон всередині Lisp: D3 COND вирішує наслідки.
; Хост не встановлює truth table. Неправильний наслідок викликає D3 CAR().
; Відповідні exact heads: D3:110 COND, D3:001 QUOTE, D3:100 CAR,
; D4:0101 NULL, D4:0100 NOT, D1:1 — останній guard.
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
