; SENS_SOURCE=tests/semantic/бенчмарк-умова-mutant.lisp
; NATIVE_SENS_POSITIVE=NOT_VERIFIED
; NATIVE_SENS_NEGATIVE=NOT_VERIFIED
;
; Мутант: завжди обирає хибну гілку.

(за-умовою
  ((тотожне? так так)
   ні)
  (так (так)))
