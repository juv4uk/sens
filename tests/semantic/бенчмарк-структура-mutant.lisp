; SENS_SOURCE=tests/semantic/бенчмарк-структура-mutant.lisp + lib/твердження.lisp
; NATIVE_SENS_POSITIVE=not applicable: intentional negative witness
; NATIVE_SENS_NEGATIVE=lib/твердження.lisp + false identity assertion returns D1:ні
; The mutant wrongly expects equality for distinct D1 values.
(твердження-однаковості так (тотожне? так ні))
