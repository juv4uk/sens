; A MAPL callback really runs on nonempty input; CAR(()) must be rejected.
(застосувати-до-залишків (список (як-є ()))
  (функція (хвіст) (перше (як-є ()))))
