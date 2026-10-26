; SENS_SOURCE=tests/semantic/d3-як-є-щит-mutant.lisp + lib/твердження.lisp
; NATIVE_SENS_POSITIVE=not applicable: intentional negative witness
; NATIVE_SENS_NEGATIVE=assertion expects D1:так but distinct quoted forms compare to D1:ні
; No conditional fallback: the negative witness is the real SENS structural verdict.
(твердження-однаковості
  так
  (однакові?
    (як-є (тотожне? так ні))
    (як-є (тотожне? так так))))
