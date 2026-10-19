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
  (функція (сирий-результат)
    (друге сирий-результат)))

(визначити process-raw-stdout-bytes
  (функція (сирий-результат)
    (третє сирий-результат)))

(визначити process-raw-stderr-bytes
  (функція (сирий-результат)
    (перше (решта (решта (решта сирий-результат))))))

(визначити процес-результат-текст
  (функція (сирий-результат)
    (за-умовою
      ((хибне? (тотожне? (перше сирий-результат) (як-є process-result)))
       (список (як-є rejected) (як-є invalid-process-result)))
      ((тотожне? (перше сирий-результат) (як-є process-result))
       ((функція (результат-виводу результат-помилок)
        (за-умовою
           ((хибне? (тотожне? (перше результат-виводу) (як-є decoded)))
            (список (як-є rejected) (як-є stdout-invalid-utf8)))
           ((тотожне? (перше результат-виводу) (як-є decoded))
            (за-умовою
              ((хибне? (тотожне? (перше результат-помилок) (як-є decoded)))
               (список (як-є rejected) (як-є stderr-invalid-utf8)))
              ((тотожне? (перше результат-помилок) (як-є decoded))
               (список
                 (як-є decoded-process)
                 (process-raw-exit-code сирий-результат)
                 (друге результат-виводу)
                 (друге результат-помилок)))
              (так
               (список (як-є rejected) (як-є stderr-invalid-utf8)))))
           (так
            (список (як-є rejected) (як-є stdout-invalid-utf8)))))
       (кодування-юнікод-8-декодувати-рядок (process-raw-stdout-bytes сирий-результат))
       (кодування-юнікод-8-декодувати-рядок (process-raw-stderr-bytes сирий-результат))))
      (так
       (список (як-є rejected) (як-є invalid-process-result))))))

(визначити процес-запустити-текст
  (функція (програма аргументи)
    (процес-результат-текст (process-run-raw програма аргументи))))

; Public compatibility surface. Valid UTF-8 preserves the historical
; 3-element result shape. Invalid UTF-8 returns explicit rejection.
(визначити процес-публічний-вихід-код
  (функція (код)
    (за-умовою
      ((тотожне? код (як-є ())) -1)
      ((хибне? (тотожне? код (як-є ()))) код)
      (так -1))))

(визначити процес-запустити
  (функція (програма аргументи)
    ((функція (результат)
        (за-умовою
        ((тотожне? (перше результат) (як-є decoded-process))
         (список
           (процес-публічний-вихід-код (друге результат))
           (третє результат)
           (перше (решта (решта (решта результат))))))
        ((хибне? (тотожне? (перше результат) (як-є decoded-process)))
         результат)
        (так результат)))
       (процес-запустити-текст програма аргументи))))

; #469: numeric identity only. The registry-derived bootstrap cache decides
; whether this post-core closure currently has any additional stable peers.
(як-є (postcore-materialization-debug skipped))
