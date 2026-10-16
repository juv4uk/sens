; D6:110010 DO та D6:110011 WHILE · закон ітерації #3370.
; П'ять D1-перевірок: реальна ітерація, нуль ітерацій, негативний ранній stop.
(list
  (null?
    (поки
      (lambda (x) (not? (null? x)))
      (lambda (x) (cdr x))
      (list (quote ()) (quote ()))))
  (equal?
    (поки
      (lambda (x) (null? x))
      (lambda (x) (cons (quote ()) x))
      (list (quote ())))
    (list (quote ())))
  (null?
    (робити
      (lambda (x) (cdr x))
      (lambda (x) (null? x))
      (lambda (x) x)
      (list (quote ()) (quote ()))))
  (not? (null?
    (робити
      (lambda (x) (cdr x))
      (lambda (x) (not? (null? x)))
      (lambda (x) x)
      (list (quote ()) (quote ())))))
  (equal?
    (робити
      (lambda (x) (cdr x))
      (lambda (x) (null? x))
      (lambda (x) (cons (quote ()) x))
      (quote ()))
    (list (quote ()))))
