; SENS_SOURCE=tests/semantic/d5-assoc-hidden-tail-negative.lisp
; NATIVE_SENS_POSITIVE=not applicable: this witness asserts improper-tail rejection
; NATIVE_SENS_NEGATIVE=must raise D3 CAR Type for D1 false tail after a prior ASSOC match
; Навіть знайдений перший ключ не може приховати D1-хвіст.
(знайти-за-ключем
  (як-є а)
  (сполучити
    (сполучити (як-є а) (як-є один))
    ні))
