; #509 — Lisp-owned native/evaluator differential parity runner.
;
; Verification policy only, never language meaning. Every admitted native island
; must agree with BOTH the reference evaluator and independent Lisp-owned
; expected evidence. Route provenance is part of the observation so evaluator
; fallback cannot impersonate native success.

(00001001 native-first-parity-pass
  (00001000 (name effect-class error-class)
    (list
      (00000001 native-parity-case)
      name
      (00000001 pass)
      (list (00000001 effect) effect-class)
      (list (00000001 error) error-class))))

(00001001 native-first-parity-fail
  (00001000 (name kind expected actual)
    (list
      (00000001 native-parity-case)
      name
      (00000001 fail)
      (list (00000001 kind) kind)
      (list (00000001 expected) expected)
      (list (00000001 actual) actual))))

(00001001 native-first-parity-case
  (00001000 (row)
    (let* ((name (00000101 row))
           (expression (second row))
           (expected (third row))
           (effect-class (fourth row))
           (error-class (fifth row))
           (evaluator-value (eval expression))
           (native-outcome
             (native-first-execute-expression expression))
           (expected-native-outcome
             (list
               (00000001 execution-route)
               (00000001 native)
               (00000001 (status completed))
               (list (00000001 value) expected))))
      (00000111
        ((equal? evaluator-value expected)
         (structural-relation same)
         (00000111
           ((equal? native-outcome expected-native-outcome)
            (structural-relation same)
            (native-first-parity-pass
              name
              effect-class
              error-class))
           ((equal? native-outcome expected-native-outcome)
            (structural-relation distinct)
            (native-first-parity-fail
              name
              (00000001 native-or-route-mismatch)
              expected-native-outcome
              native-outcome))))
        ((equal? evaluator-value expected)
         (structural-relation distinct)
         (native-first-parity-fail
           name
           (00000001 evaluator-evidence-mismatch)
           expected
           evaluator-value))))))

(00001001 native-first-parity-run
  (00001000 (rows)
    (00000111
      ((00000010 rows) (structural-kind empty-list) (00000001 ()))
      ((00000010 rows) (structural-kind atom)
       (list
         (native-first-parity-fail
           (00000001 malformed-corpus)
           (00000001 malformed-tail)
           (00000001 ())
           rows)))
      ((00000010 rows) (structural-kind pair)
       (00000100
         (native-first-parity-case (00000101 rows))
         (native-first-parity-run (00000110 rows)))))))

(00001001 native-first-parity-verdict-pass?
  (00001000 (verdict)
    (00000111
      ((00000010 verdict) (structural-kind pair)
       (00000111
         ((equal? (third verdict) (00000001 pass))
          (structural-relation same)
          t)
         ((equal? (third verdict) (00000001 pass))
          (structural-relation distinct)
          (00000001 ()))))
      ((00000001 native-first-parity-verdict-fallback)
       native-first-parity-verdict-fallback
       (00000001 ())))))

(00001001 native-first-parity-all-pass?
  (00001000 (verdicts)
    (00000111
      ((00000010 verdicts) (structural-kind empty-list) t)
      ((00000010 verdicts) (structural-kind atom) (00000001 ()))
      ((00000010 verdicts) (structural-kind pair)
       (00000111
         ((equal? (native-first-parity-verdict-pass? (00000101 verdicts)) t)
          (structural-relation same)
          (native-first-parity-all-pass? (00000110 verdicts)))
         ((equal? (native-first-parity-verdict-pass? (00000101 verdicts)) t)
          (structural-relation distinct)
          (00000001 ())))))))
