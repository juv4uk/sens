; SENS_SOURCE=tests/semantic/бенчмарк-структура-law.lisp + lib/твердження.lisp
; NATIVE_SENS_POSITIVE=lib/твердження.lisp + this structural law returns D1:так
; NATIVE_SENS_NEGATIVE=the false-identity assertion in the mutant returns D1:ні
; Structural checks stay in SENS; exact verdict comparison is byte-level cmp.
(твердження-однаковості
  так
  (за-умовою
    ((порожній? (як-є ()))
     (за-умовою
       ((хибне? (порожній? (сполучити так (як-є ()))))
        (за-умовою
          ((порожній? (решта (сполучити так (як-є ()))))
           (за-умовою
             ((тотожне? так так)
              (за-умовою
                ((хибне? (тотожне? так ні))
                 так)
                (так (ні))))
             (так (ні))))
          (так (ні))))
       (так (ні))))
    (так (ні))))
