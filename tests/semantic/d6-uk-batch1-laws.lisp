; D6:111000 ZIP, D6:111001 UNZIP, D6:111100 ANY, D6:111101 ALL.
; Native SENS-виконання власних мовних визначень у lib/core4.lisp.
; Закон ZIP/UNZIP — для списків однакової довжини.
; 10 результатів D1:YES, включно з негативними випадками та порожніми межами.
; Людські поверхні не надають прямої викличності D6:bits.
(list
  (equal?
    (розпарувати-пари
      (спарувати-послідовності
        (list (quote ()) (list (quote ())))
        (list (list (quote ())) (quote ()))))
    (list
      (list (quote ()) (list (quote ())))
      (list (list (quote ())) (quote ()))))
  (not?
    (equal?
      (розпарувати-пари
        (спарувати-послідовності
          (list (quote ()) (list (quote ())))
          (list (list (quote ())) (quote ()))))
      (list
        (list (list (quote ())) (quote ()))
        (list (quote ()) (list (quote ()))))))
  (equal? (спарувати-послідовності (quote ()) (quote ())) (quote ()))
  (equal? (розпарувати-пари (quote ())) (list (quote ()) (quote ())))
  (будь-яке? (0010 (x) (0101 x))
    (list (list (quote ())) (quote ())))
  (not? (будь-яке? (0010 (x) (0101 x))
    (list (list (quote ())))))
  (усі? (0010 (x) (0101 x))
    (list (quote ()) (quote ())))
  (not? (усі? (0010 (x) (0101 x))
    (list (quote ()) (list (quote ())))))
  (усі? (0010 (x) (0101 x)) (quote ()))
  (not? (будь-яке? (0010 (x) (0101 x)) (quote ()))))
