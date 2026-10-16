; 8 незалежних SENS D1-відповідей для D6 f13 ZIP/UNZIP та D5 reverse.
; Однакові довжини списків; негативні приклади змінюють тільки орієнтацію.
(list
  (equal?
    (спарувати-послідовності
      (list (quote а) (quote б)) (list (quote х) (quote у)))
    (list (cons (quote а) (quote х)) (cons (quote б) (quote у))))
  (хибне? (equal?
    (спарувати-послідовності
      (list (quote а) (quote б)) (list (quote х) (quote у)))
    (list (cons (quote х) (quote а)) (cons (quote у) (quote б)))))
  (equal?
    (розпарувати-пари
      (спарувати-послідовності
        (list (quote а) (quote б)) (list (quote х) (quote у))))
    (cons (list (quote а) (quote б)) (list (quote х) (quote у))))
  (хибне? (equal?
    (розпарувати-пари
      (спарувати-послідовності
        (list (quote а) (quote б)) (list (quote х) (quote у))))
    (cons (list (quote х) (quote у)) (list (quote а) (quote б)))))
  (equal?
    (розпарувати-пари
      (спарувати-послідовності (quote ()) (quote ())))
    (cons (quote ()) (quote ())))
  (equal?
    (розпарувати-пари
      (спарувати-послідовності (list (quote а)) (list (quote х))))
    (cons (list (quote а)) (list (quote х))))
  (equal? (зворот (list (quote а) (quote б)))
          (list (quote б) (quote а)))
  (хибне? (equal? (зворот (list (quote а) (quote б)))
                   (list (quote а) (quote б)))))
