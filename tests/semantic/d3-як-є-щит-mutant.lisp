; SENS_SOURCE=tests/semantic/d3-як-є-щит-mutant.lisp + lib/твердження.lisp
; NATIVE_SENS_POSITIVE=not applicable: intentional negative witness
; NATIVE_SENS_NEGATIVE=mutant claims distinct quoted forms are equal; exact output must be D1:ні
(твердження-однаковості
  так
  (за-умовою
    ((однакові?
       (як-є (тотожне? так ні))
       (як-є (тотожне? так так)))
     так)
    (так (ні))))
