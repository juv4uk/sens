; #509 — Lisp-owned native/evaluator differential parity runner.
;
; Verification policy only, never language meaning. Every admitted native island
; must agree with BOTH the reference evaluator and independent Lisp-owned
; expected evidence. Route provenance is part of the observation so evaluator
; fallback cannot impersonate native success.

(визначити native-first-parity-pass
  (функція (назва клас-ефекту клас-помилки)
    (список
      (як-є native-parity-case)
      назва
      (як-є pass)
      (список (як-є effect) клас-ефекту)
      (список (як-є error) клас-помилки))))

(визначити native-first-parity-fail
  (функція (назва різновид очікуване фактичне)
    (список
      (як-є native-parity-case)
      назва
      (як-є fail)
      (список (як-є kind) різновид)
      (список (як-є expected) очікуване)
      (список (як-є actual) фактичне))))

(визначити native-first-parity-case
  (функція (рядок)
    (нехай-послідовно ((назва (перше рядок))
           (вираз (друге рядок))
           (очікуване (третє рядок))
           (клас-ефекту (четверте рядок))
           (клас-помилки (перше (решта (решта (решта (решта рядок))))))
           (результат-обчислювача (обчислити вираз))
           (результат-машини
             (native-first-execute-expression вираз))
           (очікуваний-результат-машини
             (список
               (як-є execution-route)
               (як-є native)
               (як-є (status completed))
               (список (як-є value) очікуване))))
      (за-умовою
        ((однакові? результат-обчислювача очікуване)
         
         (за-умовою
           ((однакові? результат-машини очікуваний-результат-машини)
            
            (native-first-parity-pass
              назва
              клас-ефекту
              клас-помилки))
           (так
            (native-first-parity-fail
              назва
              (як-є native-or-route-mismatch)
              очікуваний-результат-машини
              результат-машини))))
        (так
         (native-first-parity-fail
           назва
           (як-є evaluator-evidence-mismatch)
           очікуване
           результат-обчислювача))))))

(визначити native-first-parity-run
  (функція (рядки)
    (за-умовою
      
      ((атом? рядки) 
       (список
         (native-first-parity-fail
           (як-є malformed-corpus)
           (як-є malformed-tail)
           (як-є ())
           рядки)))
      ((хибне? (атом? рядки))
       (сполучити
         (native-first-parity-case (перше рядки))
         (native-first-parity-run (решта рядки)))))))

(визначити native-first-parity-verdict-pass?
  (функція (вердикт)
    (за-умовою
      ((хибне? (атом? вердикт))
       (за-умовою
         ((однакові? (третє вердикт) (як-є pass))
          
          t)
         ))
      ((як-є native-first-parity-verdict-fallback)
       
       (як-є ())))))

(визначити native-first-parity-all-pass?
  (функція (вердикти)
    (за-умовою
      ((хибне? (атом? вердикти)) t)
      ((атом? вердикти)  (як-є ()))
      ((хибне? (атом? вердикти))
       (за-умовою
         ((однакові? (native-first-parity-verdict-pass? (перше вердикти)) t)
          
          (native-first-parity-all-pass? (решта вердикти)))
         )))))
