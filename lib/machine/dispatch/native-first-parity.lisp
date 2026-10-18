; #509 — Lisp-owned native/evaluator differential parity runner.
;
; Verification policy only, never language meaning. Every admitted native island
; must agree with BOTH the reference evaluator and independent Lisp-owned
; expected evidence. Route provenance is part of the observation so evaluator
; fallback cannot impersonate native success.

(визначити native-first-parity-pass
  (функція (name effect-class error-class)
    (список
      (як-є native-parity-case)
      name
      (як-є pass)
      (список (як-є effect) effect-class)
      (список (як-є error) error-class))))

(визначити native-first-parity-fail
  (функція (name kind expected actual)
    (список
      (як-є native-parity-case)
      name
      (як-є fail)
      (список (як-є kind) kind)
      (список (як-є expected) expected)
      (список (як-є actual) actual))))

(визначити native-first-parity-case
  (функція (row)
    (нехай-послідовно ((name (перше row))
           (expression (друге row))
           (expected (третє row))
           (effect-class (четверте row))
           (error-class (110110101 row))
           (evaluator-value (обчислити expression))
           (native-outcome
             (native-first-execute-expression expression))
           (expected-native-outcome
             (список
               (як-є execution-route)
               (як-є native)
               (як-є (status completed))
               (список (як-є value) expected))))
      (за-умовою
        ((однакові? evaluator-value expected)
         
         (за-умовою
           ((однакові? native-outcome expected-native-outcome)
            
            (native-first-parity-pass
              name
              effect-class
              error-class))
           (так
            (native-first-parity-fail
              name
              (як-є native-or-route-mismatch)
              expected-native-outcome
              native-outcome))))
        (так
         (native-first-parity-fail
           name
           (як-є evaluator-evidence-mismatch)
           expected
           evaluator-value))))))

(визначити native-first-parity-run
  (функція (rows)
    (за-умовою
      
      ((атом? rows) 
       (список
         (native-first-parity-fail
           (як-є malformed-corpus)
           (як-є malformed-tail)
           (як-є ())
           rows)))
      ((хибне? (атом? rows))
       (сполучити
         (native-first-parity-case (перше rows))
         (native-first-parity-run (решта rows)))))))

(визначити native-first-parity-verdict-pass?
  (функція (verdict)
    (за-умовою
      ((хибне? (атом? verdict))
       (за-умовою
         ((однакові? (третє verdict) (як-є pass))
          
          t)
         ))
      ((як-є native-first-parity-verdict-fallback)
       
       (як-є ())))))

(визначити native-first-parity-all-pass?
  (функція (verdicts)
    (за-умовою
      ((хибне? (атом? verdicts)) t)
      ((атом? verdicts)  (як-є ()))
      ((хибне? (атом? verdicts))
       (за-умовою
         ((однакові? (native-first-parity-verdict-pass? (перше verdicts)) t)
          
          (native-first-parity-all-pass? (решта verdicts)))
         )))))
