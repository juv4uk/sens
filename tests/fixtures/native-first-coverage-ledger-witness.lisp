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

(0011 native-first-coverage-check
  (0010 (left right)
    (110
      ((11110111 left right) (1) (001 pass))
      ((11110111 left right) (0) (001 fail)))))

(0011 native-first-coverage-all-pass-state
  (0010 (states)
    (110
      ((010 states) () (001 pass))
      ((010 states) (1) (001 fail))
      ((010 states) (0)
       (110
         ((101 (100 states) (001 pass)) (1)
          (native-first-coverage-all-pass-state (011 states)))
         ((101 (100 states) (001 pass)) (0)
          (001 fail)))))))

(0011 native-first-coverage-field
  (0010 (name row)
    (001000 ((found (11100 name (011 row))))
      (110
        ((010 found) () (001 ()))
        ((010 found) (1) (001 ()))
        ((010 found) (0) (1001 found))))))

(0011 native-first-coverage-present-state
  (0010 (value)
    (110
      ((11110111 value (001 ())) (1) (001 fail))
      ((11110111 value (001 ())) (0) (001 pass)))))

(0011 native-first-coverage-fallback-plan-state
  (0010 (expression)
    (native-first-coverage-check
      (native-first-plan expression)
      (1110 (001 evaluator-fallback) expression))))

(0011 native-first-coverage-native-plan-state
  (0010 (plan)
    (110
      ((010 plan) () (001 fail))
      ((010 plan) (1) (001 fail))
      ((010 plan) (0)
       (native-first-coverage-check
         (100 plan)
         (001 native-plan))))))

(0011 native-first-coverage-parity-state
  (0010 (parity)
    (110
      ((010 parity) () (001 fail))
      ((010 parity) (1) (001 fail))
      ((010 parity) (0)
       (native-first-coverage-check
         (10011 parity)
         (001 pass))))))

(0011 native-first-coverage-native-row-state
  (0010 (row)
    (001001 ((class (native-first-coverage-field (001 class) row))
           (expression
             (native-first-coverage-field
               (001 representative)
               row))
           (expected
             (native-first-coverage-field
               (001 expected)
               row))
           (effect
             (native-first-coverage-field
               (001 effect)
               row))
           (error-class
             (native-first-coverage-field
               (001 error)
               row))
           (evidence
             (native-first-coverage-field
               (001 evidence)
               row))
           (plan (native-first-plan expression))
           (outcome
             (native-first-execute-expression expression))
           (parity
             (native-first-parity-case
               (1110
                 class
                 expression
                 expected
                 effect
                 error-class))))
      (native-first-coverage-all-pass-state
        (1110
          (native-first-coverage-present-state class)
          (native-first-coverage-present-state expected)
          (native-first-coverage-check
            evidence
            (001 native-first-parity-witness))
          (native-first-coverage-native-plan-state plan)
          (native-first-coverage-check
            outcome
            (1110
              (001 execution-route)
              (001 native)
              (001 (status completed))
              (1110 (001 value) expected)))
          (native-first-coverage-parity-state parity))))))

(0011 native-first-coverage-fallback-row-state
  (0010 (row)
    (001000 ((expression
            (native-first-coverage-field
              (001 representative)
              row))
          (reason-ref
            (native-first-coverage-field
              (001 reason)
              row))
          (evidence
            (native-first-coverage-field
              (001 evidence)
              row)))
      (native-first-coverage-all-pass-state
        (1110
          (native-first-coverage-present-state reason-ref)
          (native-first-coverage-check
            evidence
            (001 native-first-dispatch-witness))
          (native-first-coverage-fallback-plan-state expression))))))

(0011 native-first-coverage-blocked-row-state
  (0010 (row)
    (native-first-coverage-all-pass-state
      (1110
        (native-first-coverage-fallback-row-state row)
        (native-first-coverage-present-state
          (native-first-coverage-field
            (001 prerequisite)
            row))))))

(0011 native-first-coverage-row-state
  (0010 (row)
    (110
      ((010 row) () (001 fail))
      ((010 row) (1) (001 fail))
      ((010 row) (0)
       (110
         ((11110111 (100 row) (001 native-coverage))
          (1)
          (001000 ((status
                  (native-first-coverage-field
                    (001 status)
                    row)))
            (110
              ((11110111 status (001 native-supported))
               (1)
               (native-first-coverage-native-row-state row))
              ((11110111 status (001 fallback-required))
               (1)
               (native-first-coverage-fallback-row-state row))
              ((11110111 status (001 blocked-runtime-prerequisite))
               (1)
               (native-first-coverage-blocked-row-state row))
              (t (001 fail)))))
         ((11110111 (100 row) (001 native-coverage))
          (0)
          (001 fail)))))))

(0011 native-first-coverage-all-valid-state
  (0010 (rows)
    (110
      ((010 rows) () (001 pass))
      ((010 rows) (1) (001 fail))
      ((010 rows) (0)
       (001000 ((row-state
               (native-first-coverage-row-state (100 rows))))
         (110
           ((101 row-state (001 pass)) (1)
            (native-first-coverage-all-valid-state (011 rows)))
           ((101 row-state (001 pass)) (0)
            (001 fail))))))))

(0011 native-first-coverage-expected-authority-row-state
  (0010 (row)
    (001000 ((status
            (native-first-coverage-field (001 status) row))
          (expected
            (native-first-coverage-field (001 expected) row)))
      (110
        ((11110111 status (001 native-supported))
         (1)
         (native-first-coverage-present-state expected))
        ((11110111 status (001 fallback-required))
         (1)
         (native-first-coverage-check expected (001 ())))
        ((11110111 status (001 blocked-runtime-prerequisite))
         (1)
         (native-first-coverage-check expected (001 ())))
        (t (001 fail))))))

(0011 native-first-coverage-expected-authority-state
  (0010 (rows)
    (110
      ((010 rows) () (001 pass))
      ((010 rows) (1) (001 fail))
      ((010 rows) (0)
       (001000 ((row-state
               (native-first-coverage-expected-authority-row-state
                 (100 rows))))
         (110
           ((101 row-state (001 pass)) (1)
            (native-first-coverage-expected-authority-state (011 rows)))
           ((101 row-state (001 pass)) (0)
            (001 fail))))))))

(0011 native-first-coverage-count-status-onto
  (0010 (rows status count)
    (110
      ((010 rows) () count)
      ((010 rows) (1) count)
      ((010 rows) (0)
       (110
         ((11110111
            (native-first-coverage-field
              (001 status)
              (100 rows))
            status)
          (1)
          (native-first-coverage-count-status-onto
            (011 rows)
            status
            (01010 count 1)))
         ((11110111
            (native-first-coverage-field
              (001 status)
              (100 rows))
            status)
          (0)
          (native-first-coverage-count-status-onto
            (011 rows)
            status
            count)))))))

(0011 native-first-coverage-count-status
  (0010 (status)
    (native-first-coverage-count-status-onto
      native-first-coverage-ledger
      status
      0)))

(0011 native-first-coverage-dispatch-independent-state
  (native-first-coverage-all-pass-state
    (1110
      (native-first-coverage-check
        (110101000
          "native-first-coverage"
          (110110111 "lib/machine/dispatch/native-first.lisp"))
        (001 ()))
      (native-first-coverage-check
        (110101000
          "native-first-coverage"
          (110110111 "lib/machine/dispatch/native-first-execute.lisp"))
        (001 ()))
      (native-first-coverage-check
        (110101000
          "native-first-coverage"
          (110110111 "lib/machine/dispatch/native-first-parity.lisp"))
        (001 ())))))

(0011 native-first-coverage-ledger-witness
  (0010 ()
    (001000 ((native-count
            (native-first-coverage-count-status
              (001 native-supported)))
          (fallback-count
            (native-first-coverage-count-status
              (001 fallback-required)))
          (blocked-count
            (native-first-coverage-count-status
              (001 blocked-runtime-prerequisite))))
      (001000 ((verdict
              (native-first-coverage-all-pass-state
                (1110
                  native-first-coverage-dispatch-independent-state
                  (native-first-coverage-all-valid-state
                    native-first-coverage-ledger)
                  (native-first-coverage-expected-authority-state
                    native-first-coverage-ledger)
                  (native-first-coverage-check
                    (000000 native-first-coverage-ledger)
                    6)
                  (native-first-coverage-check native-count 1)
                  (native-first-coverage-check fallback-count 2)
                  (native-first-coverage-check blocked-count 3)))))
        (110
          ((101 verdict (001 pass)) (1)
           (1110
             (001 native-first-coverage-ledger-witness)
             (001 (status pass))
             (1110 (001 rows) 6)
             (1110 (001 native) native-count)
             (1110 (001 fallback) fallback-count)
             (1110 (001 blocked) blocked-count)))
          ((101 verdict (001 pass)) (0)
           (1110
             (001 native-first-coverage-ledger-witness)
             (001 (status fail))
             (1110 (001 rows)
                   (000000 native-first-coverage-ledger))
             (1110 (001 native) native-count)
             (1110 (001 fallback) fallback-count)
             (1110 (001 blocked) blocked-count))))))))

(native-first-coverage-ledger-witness)
