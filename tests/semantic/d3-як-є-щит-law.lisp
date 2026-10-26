; SENS_SOURCE=tests/semantic/d3-як-є-щит-law.lisp
; NATIVE_SENS_POSITIVE=NOT_VERIFIED
; NATIVE_SENS_NEGATIVE=NOT_VERIFIED
;
; як-є захищає форму як дані. Без квитанцій.

(за-умовою
  ((тотожне? (як-є так) (як-є так))
   (за-умовою
     ((хибне? (тотожне? (як-є так) (як-є ні)))
      так)
     (так (ні))))
  (так (ні)))
