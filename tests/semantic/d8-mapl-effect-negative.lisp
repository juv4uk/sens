; A MAPL callback really runs on nonempty input; CAR(()) must be rejected.
(застосувати-до-залишків (список (quote ()))
  (lambda (хвіст) (перше (quote ()))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити перше car)
(визначити список list)
