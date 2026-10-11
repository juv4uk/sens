; #509 — Lisp-owned native/evaluator differential parity runner.
;
; Verification policy only, never language meaning. Every admitted native island
; must agree with BOTH the reference evaluator and independent Lisp-owned
; expected evidence. Route provenance is part of the observation so evaluator
; fallback cannot impersonate native success.

(0011 native-first-parity-pass
  (0010 (name effect-class error-class)
    (1110
      (001 native-parity-case)
      name
      (001 pass)
      (1110 (001 effect) effect-class)
      (1110 (001 error) error-class))))

(0011 native-first-parity-fail
  (0010 (name kind expected actual)
    (1110
      (001 native-parity-case)
      name
      (001 fail)
      (1110 (001 kind) kind)
      (1110 (001 expected) expected)
      (1110 (001 actual) actual))))

(0011 native-first-parity-case
  (0010 (row)
    (001001 ((name (100 row))
           (expression (1001 row))
           (expected (10011 row))
           (effect-class (100111 row))
           (error-class (110110101 row))
           (evaluator-value (0001 expression))
           (native-outcome
             (native-first-execute-expression expression))
           (expected-native-outcome
             (1110
               (001 execution-route)
               (001 native)
               (001 (status completed))
               (1110 (001 value) expected))))
      (110
        ((11110111 evaluator-value expected)
         
         (110
           ((11110111 native-outcome expected-native-outcome)
            
            (native-first-parity-pass
              name
              effect-class
              error-class))
           ((0100 (11110111 native-outcome expected-native-outcome))
            (native-first-parity-fail
              name
              (001 native-or-route-mismatch)
              expected-native-outcome
              native-outcome))))
        ((0100 (11110111 evaluator-value expected))
         (native-first-parity-fail
           name
           (001 evaluator-evidence-mismatch)
           expected
           evaluator-value))))))

(0011 native-first-parity-run
  (0010 (rows)
    (110
      
      ((010 rows) 
       (1110
         (native-first-parity-fail
           (001 malformed-corpus)
           (001 malformed-tail)
           (001 ())
           rows)))
      ((0100 (010 rows))
       (111
         (native-first-parity-case (100 rows))
         (native-first-parity-run (011 rows)))))))

(0011 native-first-parity-verdict-pass?
  (0010 (verdict)
    (110
      ((0100 (010 verdict))
       (110
         ((11110111 (10011 verdict) (001 pass))
          
          t)
         ))
      ((001 native-first-parity-verdict-fallback)
       
       (001 ())))))

(0011 native-first-parity-all-pass?
  (0010 (verdicts)
    (110
      ((0100 (010 verdicts)) t)
      ((010 verdicts)  (001 ()))
      ((0100 (010 verdicts))
       (110
         ((11110111 (native-first-parity-verdict-pass? (100 verdicts)) t)
          
          (native-first-parity-all-pass? (011 verdicts)))
         )))))
