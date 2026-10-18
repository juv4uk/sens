; D8:00110000 MAPL: execute suffix callbacks, return original proper list.
; Four exact D1:YES controls; MAPLIST and MAPL must not be conflated.
(список
  (equal?
    (застосувати-до-залишків (quote ())
      (lambda (хвіст) (перше (quote ()))))
    (quote ()))
  (equal?
    (застосувати-до-залишків (список (quote ()) (список (quote ())))
      (lambda (хвіст) (перше хвіст)))
    (список (quote ()) (список (quote ()))))
  (equal?
    (застосувати-до-залишків (список (quote ())) (lambda (хвіст) хвіст))
    (список (quote ())))
  (хибне?
    (equal?
      (застосувати-до-залишків (список (quote ())) (lambda (хвіст) хвіст))
      (відобразити-залишки (список (quote ())) (lambda (хвіст) хвіст)))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити перше car)
(визначити список list)
(визначити хибне? not?)
