; SENS_SOURCE=tests/semantic/d5-assoc-late-record-negative.lisp
; NATIVE_SENS_POSITIVE=not applicable: this witness asserts malformed-record rejection
; NATIVE_SENS_NEGATIVE=must raise D3 CAR Type for a malformed late ASSOC record
; Пошкоджений пізній запис не є повноцінною парою.
(знайти-за-ключем
  (як-є а)
  (список
    (сполучити (як-є а) (як-є один))
    ні))
