; D8:00110000 MAPL: execute suffix callbacks, return original proper list.
; Four exact D1:YES controls; MAPLIST and MAPL must not be conflated.
(list
  (equal?
    (застосувати-до-залишків (quote ())
      (lambda (хвіст) (car (quote ()))))
    (quote ()))
  (equal?
    (застосувати-до-залишків (list (quote ()) (list (quote ())))
      (lambda (хвіст) (car хвіст)))
    (list (quote ()) (list (quote ()))))
  (equal?
    (застосувати-до-залишків (list (quote ())) (lambda (хвіст) хвіст))
    (list (quote ())))
  (not?
    (equal?
      (застосувати-до-залишків (list (quote ())) (lambda (хвіст) хвіст))
      (відобразити-залишки (list (quote ())) (lambda (хвіст) хвіст)))))
