; A MAPL callback really runs on nonempty input; CAR(()) must be rejected.
(застосувати-до-залишків (list (quote ()))
  (lambda (хвіст) (car (quote ()))))
