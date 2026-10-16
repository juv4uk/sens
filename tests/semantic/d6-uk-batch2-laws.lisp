; Друга партія похідних D6:001100 RASSOC, D6:110010 DO, D6:110011 WHILE.
; 7 результатів точного D1:YES, позитивні й негативні семантичні випадки.
; Усі lambda/null?/cdr/cons — допущені текстові проєкції чинних доменів.
(list
  (equal?
    (знайти-за-значенням (quote ())
      (list (cons (quote ()) (list (quote ())))
            (cons (list (quote ())) (quote ()))))
    (cons (list (quote ())) (quote ())))
  (null?
    (знайти-за-значенням (list (quote ()))
      (list (cons (quote ()) (quote ())))))
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
