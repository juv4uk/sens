; D6:101110 REDUCE: real SENS D1 self-verdicts for nonempty/empty folds.
; Positive controls fail if REDUCE silently drops either head or tail.
(список
  (equal?
    (згорнути (функція (acc item) (сполучити item acc))
      (як-є ()) (список (як-є а) (як-є б) (як-є в)))
    (список (як-є в) (як-є б) (як-є а)))
  (equal?
    (згорнути (функція (acc item) (сполучити item acc))
      (як-є ()) (список (як-є а) (як-є б)))
    (список (як-є б) (як-є а)))
  (equal?
    (згорнути (функція (acc item) (сполучити item acc))
      (як-є а) (як-є ()))
    (як-є а)))
