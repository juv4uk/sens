; #509 — Lisp-owned native/evaluator differential parity runner.
;
; Verification policy only, never language meaning. Every admitted native island
; must agree with BOTH the reference evaluator and independent Lisp-owned
; expected evidence. Route provenance is part of the observation so evaluator
; fallback cannot impersonate native success.

(00001001 native-first-parity-pass
  (00001000 (name effect-class error-class)
    (00100111
      (00000001 native-parity-case)
      name
      (00000001 pass)
      (00100111 (00000001 effect) effect-class)
      (00100111 (00000001 error) error-class))))

(00001001 native-first-parity-fail
  (00001000 (name kind expected actual)
    (00100111
      (00000001 native-parity-case)
      name
      (00000001 fail)
      (00100111 (00000001 kind) kind)
      (00100111 (00000001 expected) expected)
      (00100111 (00000001 actual) actual))))

(00001001 native-first-parity-case
  (00001000 (row)
    (10011101 ((name (00000101 row))
           (expression (00101111 row))
           (expected (00110000 row))
           (effect-class (00110001 row))
           (error-class (00110010 row))
           (evaluator-value (01001101 expression))
           (native-outcome
             (native-first-execute-expression expression))
           (expected-native-outcome
             (00100111
               (00000001 execution-route)
               (00000001 native)
               (00000001 (status completed))
               (00100111 (00000001 value) expected))))
      (00000111
        ((00100010 evaluator-value expected)
         
         (00000111
           ((00100010 native-outcome expected-native-outcome)
            
            (native-first-parity-pass
              name
              effect-class
              error-class))
           ((0100 (00100010 native-outcome expected-native-outcome))
            (native-first-parity-fail
              name
              (00000001 native-or-route-mismatch)
              expected-native-outcome
              native-outcome))))
        ((0100 (00100010 evaluator-value expected))
         (native-first-parity-fail
           name
           (00000001 evaluator-evidence-mismatch)
           expected
           evaluator-value))))))

(00001001 native-first-parity-run
  (00001000 (rows)
    (00000111
      
      ((00000010 rows) 
       (00100111
         (native-first-parity-fail
           (00000001 malformed-corpus)
           (00000001 malformed-tail)
           (00000001 ())
           rows)))
      ((0100 (00000010 rows))
       (00000100
         (native-first-parity-case (00000101 rows))
         (native-first-parity-run (00000110 rows)))))))

(00001001 native-first-parity-verdict-pass?
  (00001000 (verdict)
    (00000111
      ((0100 (00000010 verdict))
       (00000111
         ((00100010 (00110000 verdict) (00000001 pass))
          
          t)
         (1 (00000001 ()))))
      ((00000001 native-first-parity-verdict-fallback)
       
       (00000001 ())))))

(00001001 native-first-parity-all-pass?
  (00001000 (verdicts)
    (00000111
      ((0100 (00000010 verdicts)) t)
      ((00000010 verdicts)  (00000001 ()))
      ((0100 (00000010 verdicts))
       (00000111
         ((00100010 (native-first-parity-verdict-pass? (00000101 verdicts)) t)
          
          (native-first-parity-all-pass? (00000110 verdicts)))
         (1 (00000001 ())))))))
