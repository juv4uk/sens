; SENS_SOURCE=tests/semantic/d3-як-є-щит-mutant.lisp
; NATIVE_SENS_POSITIVE=NOT_VERIFIED
; NATIVE_SENS_NEGATIVE=NOT_VERIFIED

(за-умовою
  ((тотожне? (як-є так) (як-є ні))
   так)
  (так (ні)))
