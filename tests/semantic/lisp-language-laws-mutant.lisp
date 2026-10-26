; SENS_SOURCE=tests/semantic/lisp-language-laws-mutant.lisp
; NATIVE_SENS_POSITIVE=NOT_VERIFIED
; NATIVE_SENS_NEGATIVE=NOT_VERIFIED
;
; Мутант: порожнє вважає непорожнім.

(за-умовою
  ((порожнє? (сполучити так (як-є ())))
   так)
  (так (ні)))
