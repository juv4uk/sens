; D6:000101 MAPLIST: documented list/function order, exact D1 law.
(список
  (equal?
    (відобразити-залишки (список (quote а) (quote б))
      (lambda (хвіст) хвіст))
    (список (список (quote а) (quote б)) (список (quote б))))
  (equal?
    (відобразити-залишки (список (quote а) (quote б))
      (lambda (хвіст) (перше хвіст)))
    (список (quote а) (quote б)))
  (equal?
    (відобразити-залишки (quote ())
      (lambda (хвіст) хвіст))
    (quote ())))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити перше car)
(визначити список list)
(визначити відобразити-залишки maplist)
