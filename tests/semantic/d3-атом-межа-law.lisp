; SENS_SOURCE=tests/semantic/d3-атом-межа-law.lisp
; NATIVE_SENS_POSITIVE=NOT_VERIFIED
; NATIVE_SENS_NEGATIVE=NOT_VERIFIED
;
; Межа атома: символ — атом, пара — ні. Ідентичність у тритах.

(за-умовою
  ((атом? так)
   (за-умовою
     ((хибне? (атом? (сполучити так ні)))
      (за-умовою
        ((атом? ні)
         так)
        (так ні)))
     (так ні)))
  (так ні))
