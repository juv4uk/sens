; SENS_SOURCE=tests/semantic/d3-як-є-щит-law.lisp + lib/твердження.lisp
; NATIVE_SENS_POSITIVE=quoted call-shaped data compares equal and returns D1:так via SENS/Zig/T5M
; NATIVE_SENS_NEGATIVE=the distinct quoted form in the same law is unequal; its false branch returns D1:ні
; D3 тотожне? remains atom-only. Existing structural equality compares inert quoted forms.
(твердження-однаковості
  так
  (за-умовою
    ((однакові?
       (як-є (тотожне? так ні))
       (як-є (тотожне? так ні)))
     (за-умовою
       ((хибне?
          (однакові?
            (як-є (тотожне? так ні))
            (як-є (тотожне? так так))))
        так)
       (так (ні))))
    (так (ні))))
