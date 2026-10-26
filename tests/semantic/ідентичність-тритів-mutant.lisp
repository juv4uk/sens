; SENS_SOURCE=tests/semantic/ідентичність-тритів-mutant.lisp + lib/твердження.lisp
; NATIVE_SENS_POSITIVE=not applicable: intentional negative witness
; NATIVE_SENS_NEGATIVE=lib/твердження.lisp + false structural-equality assertion returns D1:ні
; Мутант: стверджує тотожність порожнього і непорожнього структурних списків.
(твердження-однаковості так (однакові? (як-є ()) (сполучити так (як-є ()))))
