; #509 — Lisp-owned native/evaluator differential parity runner.
;
; Verification policy only, never language meaning. Every admitted native island
; must agree with BOTH the reference evaluator and independent Lisp-owned
; expected evidence. Route provenance is part of the observation so evaluator
; fallback cannot impersonate native success.

(def native-first-parity-pass
  (lambda (name effect-class error-class)
    (list
      (quote native-parity-case)
      name
      (quote pass)
      (list (quote effect) effect-class)
      (list (quote error) error-class))))

(def native-first-parity-fail
  (lambda (name kind expected actual)
    (list
      (quote native-parity-case)
      name
      (quote fail)
      (list (quote kind) kind)
      (list (quote expected) expected)
      (list (quote actual) actual))))

(def native-first-parity-case
  (lambda (row)
    (let* ((name (car row))
           (expression (second row))
           (expected (third row))
           (effect-class (fourth row))
           (error-class (fifth row))
           (evaluator-value (eval expression))
           (native-outcome
             (native-first-execute-expression expression))
           (expected-native-outcome
             (list
               (quote execution-route)
               (quote native)
               (quote (status completed))
               (list (quote value) expected))))
      (cond
        ((equal? evaluator-value expected)
         (structural-relation same)
         (cond
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
              (quote native-or-route-mismatch)
              expected-native-outcome
              native-outcome))))
        ((equal? evaluator-value expected)
         (structural-relation distinct)
         (native-first-parity-fail
           name
           (quote evaluator-evidence-mismatch)
           expected
           evaluator-value))))))

(def native-first-parity-run
  (lambda (rows)
    (cond
      ((atom? rows) (structural-kind empty-list) (quote ()))
      ((atom? rows) (structural-kind atom)
       (list
         (native-first-parity-fail
           (quote malformed-corpus)
           (quote malformed-tail)
           (quote ())
           rows)))
      ((atom? rows) (structural-kind pair)
       (cons
         (native-first-parity-case (car rows))
         (native-first-parity-run (cdr rows)))))))

(def native-first-parity-verdict-pass?
  (lambda (verdict)
    (cond
      ((atom? verdict) (structural-kind pair)
       (cond
         ((equal? (third verdict) (quote pass))
          (structural-relation same)
          t)
         ((equal? (third verdict) (quote pass))
          (structural-relation distinct)
          (quote ()))))
      ((quote native-first-parity-verdict-fallback)
       native-first-parity-verdict-fallback
       (quote ())))))

(def native-first-parity-all-pass?
  (lambda (verdicts)
    (cond
      ((atom? verdicts) (structural-kind empty-list) t)
      ((atom? verdicts) (structural-kind atom) (quote ()))
      ((atom? verdicts) (structural-kind pair)
       (cond
         ((equal? (native-first-parity-verdict-pass? (car verdicts)) t)
          (structural-relation same)
          (native-first-parity-all-pass? (cdr verdicts)))
         ((equal? (native-first-parity-verdict-pass? (car verdicts)) t)
          (structural-relation distinct)
          (quote ())))))))
