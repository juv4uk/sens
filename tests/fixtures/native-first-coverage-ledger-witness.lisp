; #508 — executable authority witness for the native coverage ledger.
; The ledger may describe routing, but it may not create it:
;   native-supported -> classifier native-plan + CPU native route + #509 parity
;   fallback/blocked -> classifier evaluator-fallback of the unchanged source
; Blocked rows must also name a concrete prerequisite.
;
; Post-#218 discipline: this witness never treats structural result records as
; generic booleans and never feeds possibly-structural values to eq. Every
; structural comparison is reduced explicitly to the atom states pass/fail.

(load "lib/core.lisp")
(load "lib/machine/encoding/x86-64.lisp")
(load "lib/machine/layout/pair-x86-64.lisp")
(load "lib/machine/operands/x86-64.lisp")
(load "lib/machine/admission/x86-64.lisp")
(load "lib/machine/lowering/semantic-x86-64.lisp")
(load "lib/machine/dispatch/native-first.lisp")
(load "lib/machine/dispatch/native-first-execute.lisp")
(load "lib/machine/dispatch/native-first-parity.lisp")
(load "lib/machine/dispatch/native-first-coverage.lisp")

(def native-first-coverage-check
  (lambda (left right)
    (cond
      ((equal? left right) (structural-relation same) (quote pass))
      ((equal? left right) (structural-relation distinct) (quote fail)))))

(def native-first-coverage-all-pass-state
  (lambda (states)
    (cond
      ((atom? states) (structural-kind empty-list) (quote pass))
      ((atom? states) (structural-kind atom) (quote fail))
      ((atom? states) (structural-kind pair)
       (cond
         ((eq? (car states) (quote pass)) (identity-relation same)
          (native-first-coverage-all-pass-state (cdr states)))
         ((eq? (car states) (quote pass)) (identity-relation distinct)
          (quote fail)))))))

(def native-first-coverage-field
  (lambda (name row)
    (let ((found (assoc name (cdr row))))
      (cond
        ((atom? found) (structural-kind empty-list) (quote ()))
        ((atom? found) (structural-kind atom) (quote ()))
        ((atom? found) (structural-kind pair) (second found))))))

(def native-first-coverage-present-state
  (lambda (value)
    (cond
      ((equal? value (quote ())) (structural-relation same) (quote fail))
      ((equal? value (quote ())) (structural-relation distinct) (quote pass)))))

(def native-first-coverage-fallback-plan-state
  (lambda (expression)
    (native-first-coverage-check
      (native-first-plan expression)
      (list (quote evaluator-fallback) expression))))

(def native-first-coverage-native-plan-state
  (lambda (plan)
    (cond
      ((atom? plan) (structural-kind empty-list) (quote fail))
      ((atom? plan) (structural-kind atom) (quote fail))
      ((atom? plan) (structural-kind pair)
       (native-first-coverage-check
         (car plan)
         (quote native-plan))))))

(def native-first-coverage-parity-state
  (lambda (parity)
    (cond
      ((atom? parity) (structural-kind empty-list) (quote fail))
      ((atom? parity) (structural-kind atom) (quote fail))
      ((atom? parity) (structural-kind pair)
       (native-first-coverage-check
         (third parity)
         (quote pass))))))

(def native-first-coverage-native-row-state
  (lambda (row)
    (let* ((class (native-first-coverage-field (quote class) row))
           (expression
             (native-first-coverage-field
               (quote representative)
               row))
           (expected
             (native-first-coverage-field
               (quote expected)
               row))
           (effect
             (native-first-coverage-field
               (quote effect)
               row))
           (error-class
             (native-first-coverage-field
               (quote error)
               row))
           (evidence
             (native-first-coverage-field
               (quote evidence)
               row))
           (plan (native-first-plan expression))
           (outcome
             (native-first-execute-expression expression))
           (parity
             (native-first-parity-case
               (list
                 class
                 expression
                 expected
                 effect
                 error-class))))
      (native-first-coverage-all-pass-state
        (list
          (native-first-coverage-present-state class)
          (native-first-coverage-present-state expected)
          (native-first-coverage-check
            evidence
            (quote native-first-parity-witness))
          (native-first-coverage-native-plan-state plan)
          (native-first-coverage-check
            outcome
            (list
              (quote execution-route)
              (quote native)
              (quote (status completed))
              (list (quote value) expected)))
          (native-first-coverage-parity-state parity))))))

(def native-first-coverage-fallback-row-state
  (lambda (row)
    (let ((expression
            (native-first-coverage-field
              (quote representative)
              row))
          (reason
            (native-first-coverage-field
              (quote reason)
              row))
          (evidence
            (native-first-coverage-field
              (quote evidence)
              row)))
      (native-first-coverage-all-pass-state
        (list
          (native-first-coverage-present-state reason)
          (native-first-coverage-check
            evidence
            (quote native-first-dispatch-witness))
          (native-first-coverage-fallback-plan-state expression))))))

(def native-first-coverage-blocked-row-state
  (lambda (row)
    (native-first-coverage-all-pass-state
      (list
        (native-first-coverage-fallback-row-state row)
        (native-first-coverage-present-state
          (native-first-coverage-field
            (quote prerequisite)
            row))))))

(def native-first-coverage-row-state
  (lambda (row)
    (cond
      ((atom? row) (structural-kind empty-list) (quote fail))
      ((atom? row) (structural-kind atom) (quote fail))
      ((atom? row) (structural-kind pair)
       (cond
         ((equal? (car row) (quote native-coverage))
          (structural-relation same)
          (let ((status
                  (native-first-coverage-field
                    (quote status)
                    row)))
            (cond
              ((equal? status (quote native-supported))
               (structural-relation same)
               (native-first-coverage-native-row-state row))
              ((equal? status (quote fallback-required))
               (structural-relation same)
               (native-first-coverage-fallback-row-state row))
              ((equal? status (quote blocked-runtime-prerequisite))
               (structural-relation same)
               (native-first-coverage-blocked-row-state row))
              (t (quote fail)))))
         ((equal? (car row) (quote native-coverage))
          (structural-relation distinct)
          (quote fail)))))))

(def native-first-coverage-all-valid-state
  (lambda (rows)
    (cond
      ((atom? rows) (structural-kind empty-list) (quote pass))
      ((atom? rows) (structural-kind atom) (quote fail))
      ((atom? rows) (structural-kind pair)
       (let ((row-state
               (native-first-coverage-row-state (car rows))))
         (cond
           ((eq? row-state (quote pass)) (identity-relation same)
            (native-first-coverage-all-valid-state (cdr rows)))
           ((eq? row-state (quote pass)) (identity-relation distinct)
            (quote fail))))))))

(def native-first-coverage-expected-authority-row-state
  (lambda (row)
    (let ((status
            (native-first-coverage-field (quote status) row))
          (expected
            (native-first-coverage-field (quote expected) row)))
      (cond
        ((equal? status (quote native-supported))
         (structural-relation same)
         (native-first-coverage-present-state expected))
        ((equal? status (quote fallback-required))
         (structural-relation same)
         (native-first-coverage-check expected (quote ())))
        ((equal? status (quote blocked-runtime-prerequisite))
         (structural-relation same)
         (native-first-coverage-check expected (quote ())))
        (t (quote fail))))))

(def native-first-coverage-expected-authority-state
  (lambda (rows)
    (cond
      ((atom? rows) (structural-kind empty-list) (quote pass))
      ((atom? rows) (structural-kind atom) (quote fail))
      ((atom? rows) (structural-kind pair)
       (let ((row-state
               (native-first-coverage-expected-authority-row-state
                 (car rows))))
         (cond
           ((eq? row-state (quote pass)) (identity-relation same)
            (native-first-coverage-expected-authority-state (cdr rows)))
           ((eq? row-state (quote pass)) (identity-relation distinct)
            (quote fail))))))))

(def native-first-coverage-count-status-onto
  (lambda (rows status count)
    (cond
      ((atom? rows) (structural-kind empty-list) count)
      ((atom? rows) (structural-kind atom) count)
      ((atom? rows) (structural-kind pair)
       (cond
         ((equal?
            (native-first-coverage-field
              (quote status)
              (car rows))
            status)
          (structural-relation same)
          (native-first-coverage-count-status-onto
            (cdr rows)
            status
            (+ count 1)))
         ((equal?
            (native-first-coverage-field
              (quote status)
              (car rows))
            status)
          (structural-relation distinct)
          (native-first-coverage-count-status-onto
            (cdr rows)
            status
            count)))))))

(def native-first-coverage-count-status
  (lambda (status)
    (native-first-coverage-count-status-onto
      native-first-coverage-ledger
      status
      0)))

(def native-first-coverage-dispatch-independent-state
  (native-first-coverage-all-pass-state
    (list
      (native-first-coverage-check
        (string-contains?
          "native-first-coverage"
          (read-file "lib/machine/dispatch/native-first.lisp"))
        (quote ()))
      (native-first-coverage-check
        (string-contains?
          "native-first-coverage"
          (read-file "lib/machine/dispatch/native-first-execute.lisp"))
        (quote ()))
      (native-first-coverage-check
        (string-contains?
          "native-first-coverage"
          (read-file "lib/machine/dispatch/native-first-parity.lisp"))
        (quote ())))))

(def native-first-coverage-ledger-witness
  (lambda ()
    (let ((native-count
            (native-first-coverage-count-status
              (quote native-supported)))
          (fallback-count
            (native-first-coverage-count-status
              (quote fallback-required)))
          (blocked-count
            (native-first-coverage-count-status
              (quote blocked-runtime-prerequisite))))
      (let ((verdict
              (native-first-coverage-all-pass-state
                (list
                  native-first-coverage-dispatch-independent-state
                  (native-first-coverage-all-valid-state
                    native-first-coverage-ledger)
                  (native-first-coverage-expected-authority-state
                    native-first-coverage-ledger)
                  (native-first-coverage-check
                    (length native-first-coverage-ledger)
                    6)
                  (native-first-coverage-check native-count 1)
                  (native-first-coverage-check fallback-count 2)
                  (native-first-coverage-check blocked-count 3)))))
        (cond
          ((eq? verdict (quote pass)) (identity-relation same)
           (list
             (quote native-first-coverage-ledger-witness)
             (quote (status pass))
             (list (quote rows) 6)
             (list (quote native) native-count)
             (list (quote fallback) fallback-count)
             (list (quote blocked) blocked-count)))
          ((eq? verdict (quote pass)) (identity-relation distinct)
           (list
             (quote native-first-coverage-ledger-witness)
             (quote (status fail))
             (list (quote rows)
                   (length native-first-coverage-ledger))
             (list (quote native) native-count)
             (list (quote fallback) fallback-count)
             (list (quote blocked) blocked-count))))))))

(native-first-coverage-ledger-witness)
