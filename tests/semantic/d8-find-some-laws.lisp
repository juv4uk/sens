; D8:11011111 FIND та D8:10100101 SOME, тільки SENS-owned D1 verdicts.
(list
  (equal?
    (знайти-перший-збіг (quote б) (list (quote а) (quote б) (quote в)))
    (quote б))
  (null?
    (знайти-перший-збіг (quote г) (list (quote а) (quote б) (quote в))))
  (equal?
    (знайти-перший-збіг (quote а) (list (quote а) (quote б)))
    (quote а))
  (equal?
    (знайти-перший-збіг (list (quote а) (quote б))
      (list (quote в) (list (quote а) (quote б))))
    (list (quote а) (quote б)))
  (існує-збіг?
    (lambda (x) (equal? x (quote б)))
    (list (quote а) (quote б)))
  (not?
    (існує-збіг?
      (lambda (x) (equal? x (quote б)))
      (list (quote а) (quote в))))
  (not?
    (існує-збіг? (lambda (x) (equal? x (quote б))) (quote ()))))
