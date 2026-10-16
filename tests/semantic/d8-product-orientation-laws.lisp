; Шість D1-контролів D8:11100001 / D8:11100011; 2 негативні орієнтації.
(list
  (equal?
    (спарувати-навпаки (list (quote а) (quote б)) (list (quote в) (quote г)))
    (list (cons (quote в) (quote а)) (cons (quote г) (quote б))))
  (equal?
    (розпарувати-навпаки
      (спарувати-навпаки (list (quote а) (quote б)) (list (quote в) (quote г))))
    (list (list (quote а) (quote б)) (list (quote в) (quote г))))
  (not?
    (equal?
      (спарувати-послідовності (list (quote а)) (list (quote в)))
      (спарувати-навпаки (list (quote а)) (list (quote в)))))
  (not?
    (equal?
      (розпарувати-навпаки
        (спарувати-послідовності (list (quote а)) (list (quote в))))
      (list (list (quote а)) (list (quote в)))))
  (equal? (спарувати-навпаки (quote ()) (quote ())) (quote ()))
  (equal?
    (розпарувати-навпаки (quote ()))
    (list (quote ()) (quote ())))
  (equal?
    (додати-асоціацію-навпаки (quote а) (quote в) (quote ()))
    (list (cons (quote в) (quote а))))
  (not?
    (equal?
      (додати-асоціацію-навпаки (quote а) (quote в) (quote ()))
      (list (cons (quote а) (quote в)))))
)
