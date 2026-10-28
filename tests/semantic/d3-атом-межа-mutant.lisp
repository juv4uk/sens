; SENS_SOURCE=tests/semantic/d3-атом-межа-mutant.lisp
; NATIVE_SENS_POSITIVE=NOT_VERIFIED
; NATIVE_SENS_NEGATIVE=NOT_VERIFIED
;
; Мутант: пара вважається атомом.

(за-умовою
  ((атом? (сполучити так ні))
   так)
  (так ні))
