; SENS_SOURCE=tests/semantic/d5-member-hidden-tail-negative.lisp
; NATIVE_SENS_POSITIVE=not applicable: this witness asserts improper-tail rejection
; NATIVE_SENS_NEGATIVE=must raise D3 CAR Type for D1 false tail after a prior MEMBER match
; Позитивний перший збіг не приховує неправильний D1-хвіст.
(значення-у-списку?
  (як-є а)
  (сполучити (як-є а) (сполучити (як-є б) ні)))
