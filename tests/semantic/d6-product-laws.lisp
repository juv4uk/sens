; Партія #5854: D6 ZIP/UNZIP, D8 SWAPPED, D6 RASSOC і D5 REVERSE-ONTO.
; 10 незалежних D1 YES; негативи перевіряють неправильну орієнтацію.
; Лише SENS-вирази та українські проєкції чинних ратифікованих кодів.
(list
  (equal?
    (спарувати-послідовності (list (quote а) (quote б))
                             (list (quote в) (quote г)))
    (list (cons (quote а) (quote в)) (cons (quote б) (quote г))))
  (equal?
    (розпарувати-послідовності
      (спарувати-послідовності (list (quote а) (quote б))
                               (list (quote в) (quote г))))
    (list (list (quote а) (quote б)) (list (quote в) (quote г))))
  (not?
    (equal?
      (спарувати-послідовності (list (quote а)) (list (quote в)))
      (спарувати-навпаки (list (quote а)) (list (quote в)))))
  (equal?
    (спарувати-навпаки (list (quote а)) (list (quote в)))
    (list (cons (quote в) (quote а))))
  (equal?
    (розпарувати-навпаки
      (спарувати-навпаки (list (quote а) (quote б))
                         (list (quote в) (quote г))))
    (list (list (quote а) (quote б)) (list (quote в) (quote г))))
  (not?
    (equal?
      (розпарувати-навпаки
        (спарувати-послідовності (list (quote а)) (list (quote в))))
      (list (list (quote а)) (list (quote в)))))
  (equal?
    (знайти-за-значенням (quote в)
      (list (cons (quote а) (quote в)) (cons (quote б) (quote г))))
    (cons (quote а) (quote в)))
  (null?
    (знайти-за-значенням (quote а)
      (list (cons (quote а) (quote в)))))
  (equal?
    (зворот-до (list (quote а) (quote б)) (list (quote в)))
    (list (quote б) (quote а) (quote в)))
  (equal?
    (зворот-до (quote ()) (list (quote в)))
    (list (quote в))))
