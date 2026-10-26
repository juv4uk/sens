; SENS_SOURCE=tests/semantic/ідентичність-тритів-law.lisp + lib/твердження.lisp
; NATIVE_SENS_POSITIVE=lib/твердження.lisp + same-structure equality and atom equality return D1:так
; NATIVE_SENS_NEGATIVE=the mutant asserts equality for distinct structures and returns D1:ні
; D3 тотожне? compares atoms only; structures use the existing structural equality operation.
(за-умовою
  ((однакові? (як-є ()) (як-є ()))
   (за-умовою
     ((хибне? (однакові? (як-є ()) (сполучити так (як-є ()))))
      (за-умовою
        ((тотожне? так так)
         (за-умовою
           ((хибне? (тотожне? так ні))
            так)
           (так (ні))))
        (так (ні))))
     (так (ні))))
  (так (ні)))
