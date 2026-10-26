; SENS_SOURCE=tests/semantic/бенчмарк-умова-law.lisp
; NATIVE_SENS_POSITIVE=NOT_VERIFIED
; NATIVE_SENS_NEGATIVE=NOT_VERIFIED
;
; Бенчмарк умови: перша істинна гілка, коротка схема.
; Без Python, JSON, SHA-256.

(за-умовою
  ((тотожне? ні так)
   ні)
  ((тотожне? так так)
   (за-умовою
     ((порожній? (як-є ()))
      так)
     (так (ні))))
  (так (ні)))
