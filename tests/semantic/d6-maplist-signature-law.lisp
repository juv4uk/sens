; D6:000101 MAPLIST: documented list/function order, exact D1 law.
(list
  (equal?
    (відобразити-залишки (list (quote а) (quote б))
      (lambda (хвіст) хвіст))
    (list (list (quote а) (quote б)) (list (quote б))))
  (equal?
    (maplist (list (quote а) (quote б))
      (lambda (хвіст) (car хвіст)))
    (list (quote а) (quote б)))
  (equal?
    (відобразити-залишки (quote ())
      (lambda (хвіст) хвіст))
    (quote ())))
