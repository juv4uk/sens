; SENS_SOURCE=tests/semantic/d4-selector-width-mutant.lisp
; NATIVE_SENS_POSITIVE=NOT_VERIFIED
; NATIVE_SENS_NEGATIVE=NOT_VERIFIED
;
; Мутант: плутає перше і решту.

(за-умовою
  ((тотожне?
     (перше (сполучити так (сполучити ні (як-є ()))))
     ні)
   так)
  (так ні))
