; Process-result interpretation owned by Lisp.
; Інтерпретація результату процесу, якою володіє Lisp.
;
; Two-field D3 COND with exact direct D1:1 fallback values; D3 () stays data.
; Reuses utf8-decode-string from lib/utf8.lisp and process-run-raw host.
; Width is identity; every bit of the domain address is valued.
;
; Host capability `process-run-raw` owns only process execution, allowlisting,
; exit observation, and byte capture. This layer owns UTF-8 interpretation.
; Load `lib/utf8.lisp` before this file.

(визначити process-raw-exit-code
  (функція (raw)
    (друге raw)))

(визначити process-raw-stdout-bytes
  (функція (raw)
    (третє raw)))

(визначити process-raw-stderr-bytes
  (функція (raw)
    (перше (решта (решта (решта raw))))))

(визначити process-result->text
  (функція (raw)
    (за-умовою
      ((хибне? (тотожне? (перше raw) (як-є process-result)))
       (список (як-є rejected) (як-є invalid-process-result)))
      ((тотожне? (перше raw) (як-є process-result))
       ((функція (stdout-result stderr-result)
        (за-умовою
           ((хибне? (тотожне? (перше stdout-result) (як-є decoded)))
            (список (як-є rejected) (як-є stdout-invalid-utf8)))
           ((тотожне? (перше stdout-result) (як-є decoded))
            (за-умовою
              ((хибне? (тотожне? (перше stderr-result) (як-є decoded)))
               (список (як-є rejected) (як-є stderr-invalid-utf8)))
              ((тотожне? (перше stderr-result) (як-є decoded))
               (список
                 (як-є decoded-process)
                 (process-raw-exit-code raw)
                 (друге stdout-result)
                 (друге stderr-result)))
              (так
               (список (як-є rejected) (як-є stderr-invalid-utf8)))))
           (так
            (список (як-є rejected) (як-є stdout-invalid-utf8)))))
       (кодування-юнікод-8-декодувати-рядок (process-raw-stdout-bytes raw))
       (кодування-юнікод-8-декодувати-рядок (process-raw-stderr-bytes raw))))
      (так
       (список (як-є rejected) (як-є invalid-process-result))))))

(визначити process-run-text
  (функція (program args)
    (process-result->text (process-run-raw program args))))

; Public compatibility surface. Valid UTF-8 preserves the historical
; 3-element result shape. Invalid UTF-8 returns explicit rejection.
(визначити process-public-exit-code
  (функція (code)
    (за-умовою
      ((тотожне? code (як-є ())) -1)
      ((хибне? (тотожне? code (як-є ()))) code)
      (так -1))))

(визначити process-run
  (функція (program args)
    ((функція (result)
        (за-умовою
        ((тотожне? (перше result) (як-є decoded-process))
         (список
           (process-public-exit-code (друге result))
           (третє result)
           (перше (решта (решта (решта result))))))
        ((хибне? (тотожне? (перше result) (як-є decoded-process)))
         result)
        (так result)))
       (process-run-text program args))))

; #469: numeric identity only. The registry-derived bootstrap cache decides
; whether this post-core closure currently has any additional stable peers.
(як-є (postcore-materialization-debug skipped))
