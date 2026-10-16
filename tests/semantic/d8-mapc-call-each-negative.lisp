; D8:10110100 MAPC negative — malformed second callback must reject.
; First callback CAR(pair) succeeds, second CAR(atom) must fail at layer=eval.
(застосувати-до-всіх
  (функція (елемент) (100 елемент))
  (список (список (як-є а)) (як-є б)))
