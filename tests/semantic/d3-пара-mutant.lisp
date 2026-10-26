; SENS_SOURCE=tests/semantic/d3-пара-mutant.lisp
; NATIVE_SENS_POSITIVE=NOT_VERIFIED
; NATIVE_SENS_NEGATIVE=NOT_VERIFIED
;
; Мутант: плутає перше і решту пари.

(за-умовою
  ((тотожне? (перше (сполучити так ні)) ні)
   так)
  (так (ні)))
