; D9:010011100 CAR-CONS, D9:001000110 CDR-CONS, D9:010000111 ATOM-CONS.
; Three positive D1 laws and three semantic negatives (incorrect projection).
; Expected D1 vector: (1 1 1 0 0 0), exact host-free SENS evaluation.
(список
  (канон-закон-перше-пара (як-є а) (як-є б))
  (канон-закон-решта-пара (як-є а) (як-є б))
  (канон-закон-атом-пара (як-є а) (як-є б))
  (101 (100 (111 (як-є а) (як-є б))) (як-є б))
  (101 (011 (111 (як-є а) (як-є б))) (як-є а))
  (010 (111 (як-є а) (як-є б))))
