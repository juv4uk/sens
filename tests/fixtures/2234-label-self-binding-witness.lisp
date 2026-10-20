; #2234 — LABEL self-binding. Ukrainian projection only.

(обчислити
  (як-є
    ((мітка self
       (функція (xs)
         (за-умовою
           ((тотожне? xs (як-є ())) (як-є done))
           (так (self (решта xs))))))
     (як-є (A))))
  (як-є ())
  (як-є ()))
