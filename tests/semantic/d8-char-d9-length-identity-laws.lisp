; One native SENS witness: D8 CHAR + D9 STRING-LENGTH / IDENTITY / CDR-IMPROPER.
; Exact D1 predicate vector: (1 1 1 1 1 1 1 0 0 0).
; Three deliberate false comparisons reject index/order/count confusion.
(list
  (equal? (символ "кіт" #d24:000000000000000000000000) "к")
  (equal? (символ "кіт" #d24:000000000000000000000001) "і")
  (equal? (символ "кіт" #d24:000000000000000000000010) "т")
  (equal? (рядок-довжина "") #d24:000000000000000000000000)
  (equal? (рядок-довжина "їж") #d24:000000000000000000000010)
  (equal? (тотожність (list (quote а) (quote б)))
          (list (quote а) (quote б)))
  (канон-закон-решта-неправильний (quote а) (quote б))
  (equal? (символ "кіт" #d24:000000000000000000000001) "т")
  (equal? (рядок-довжина "їж") #d24:000000000000000000000001)
  (тотожне? (решта (сполучити (quote а) (quote б))) (quote а)))
