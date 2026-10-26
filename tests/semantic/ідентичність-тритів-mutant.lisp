; SENS_SOURCE=tests/semantic/ідентичність-тритів-mutant.lisp
; NATIVE_SENS_POSITIVE=NOT_VERIFIED
; NATIVE_SENS_NEGATIVE=NOT_VERIFIED
;
; Мутант: стверджує тотожність порожнього і непорожнього.

(за-умовою
  ((тотожне? (як-є ()) (сполучити так (як-є ())))
   так)
  (так (ні)))
