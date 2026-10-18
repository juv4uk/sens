; A MAPL callback really runs on nonempty input; CAR(()) must be rejected.
(застосувати-до-залишків (список (як-є ()))
  (функція (хвіст) (перше (як-є ()))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити перше car)
(визначити список list)
