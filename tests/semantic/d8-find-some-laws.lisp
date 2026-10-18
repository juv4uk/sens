; D8:11011111 FIND та D8:10100101 SOME, тільки SENS-owned D1 verdicts.
(список
  (equal?
    (знайти-перший-збіг (quote б) (список (quote а) (quote б) (quote в)))
    (quote б))
  (порожній?
    (знайти-перший-збіг (quote г) (список (quote а) (quote б) (quote в))))
  (equal?
    (знайти-перший-збіг (quote а) (список (quote а) (quote б)))
    (quote а))
  (equal?
    (знайти-перший-збіг (список (quote а) (quote б))
      (список (quote в) (список (quote а) (quote б))))
    (список (quote а) (quote б)))
  (існує-збіг?
    (lambda (x) (equal? x (quote б)))
    (список (quote а) (quote б)))
  (хибне?
    (існує-збіг?
      (lambda (x) (equal? x (quote б)))
      (список (quote а) (quote в))))
  (хибне?
    (існує-збіг? (lambda (x) (equal? x (quote б))) (quote ()))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
(визначити хибне? not?)
(визначити порожній? null?)
