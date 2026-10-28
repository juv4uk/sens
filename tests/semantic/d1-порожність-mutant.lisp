; SENS_SOURCE=tests/semantic/d1-порожність-mutant.lisp
; NATIVE_SENS_POSITIVE=NOT_VERIFIED
; NATIVE_SENS_NEGATIVE=NOT_VERIFIED
;
; Мутант: непорожній список вважає порожнім.

(за-умовою
  ((порожнє? (сполучити ні (як-є ())))
   так)
  (так ні))
