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

(00001001 native-first-coverage-check
  (00001000 (left right)
    (00000111
      ((00100010 left right) (00000001 pass))
      ((00100010 (00100010 left right) (00100010 (00000001 d1-no-left) (00000001 d1-no-right))) (00000001 fail)))))

(00001001 native-first-coverage-all-pass-state
  (00001000 (states)
    (00000111
      ((00000010 states) () (00000001 pass))
      ((00000010 states) (1) (00000001 fail))
      ((00000010 states) (0)
       (00000111
         ((00000011 (00000101 states) (00000001 pass)) (1)
          (native-first-coverage-all-pass-state (00000110 states)))
         ((00000011 (00000101 states) (00000001 pass)) (0)
          (00000001 fail)))))))

(00001001 native-first-coverage-field
  (00001000 (name row)
    (10011100 ((found (00101101 name (00000110 row))))
      (00000111
        ((00000010 found) () (00000001 ()))
        ((00000010 found) (1) (00000001 ()))
        ((00000010 found) (0) (00101111 found))))))

(00001001 native-first-coverage-present-state
  (00001000 (value)
    (00000111
      ((00100010 value (00000001 ())) (00000001 fail))
      ((00100010 (00100010 value (00000001 ())) (00100010 (00000001 d1-no-left) (00000001 d1-no-right))) (00000001 pass)))))

(00001001 native-first-coverage-fallback-plan-state
  (00001000 (expression)
    (native-first-coverage-check
      (native-first-plan expression)
      (00100111 (00000001 evaluator-fallback) expression))))

(00001001 native-first-coverage-native-plan-state
  (00001000 (plan)
    (00000111
      ((00000010 plan) () (00000001 fail))
      ((00000010 plan) (1) (00000001 fail))
      ((00000010 plan) (0)
       (native-first-coverage-check
         (00000101 plan)
         (00000001 native-plan))))))

(00001001 native-first-coverage-parity-state
  (00001000 (parity)
    (00000111
      ((00000010 parity) () (00000001 fail))
      ((00000010 parity) (1) (00000001 fail))
      ((00000010 parity) (0)
       (native-first-coverage-check
         (00110000 parity)
         (00000001 pass))))))

(00001001 native-first-coverage-native-row-state
  (00001000 (row)
    (10011101 ((class (native-first-coverage-field (00000001 class) row))
           (expression
             (native-first-coverage-field
               (00000001 representative)
               row))
           (expected
             (native-first-coverage-field
               (00000001 expected)
               row))
           (effect
             (native-first-coverage-field
               (00000001 effect)
               row))
           (error-class
             (native-first-coverage-field
               (00000001 error)
               row))
           (evidence
             (native-first-coverage-field
               (00000001 evidence)
               row))
           (plan (native-first-plan expression))
           (outcome
             (native-first-execute-expression expression))
           (parity
             (native-first-parity-case
               (00100111
                 class
                 expression
                 expected
                 effect
                 error-class))))
      (native-first-coverage-all-pass-state
        (00100111
          (native-first-coverage-present-state class)
          (native-first-coverage-present-state expected)
          (native-first-coverage-check
            evidence
            (00000001 native-first-parity-witness))
          (native-first-coverage-native-plan-state plan)
          (native-first-coverage-check
            outcome
            (00100111
              (00000001 execution-route)
              (00000001 native)
              (00000001 (status completed))
              (00100111 (00000001 value) expected)))
          (native-first-coverage-parity-state parity))))))

(00001001 native-first-coverage-fallback-row-state
  (00001000 (row)
    (10011100 ((expression
            (native-first-coverage-field
              (00000001 representative)
              row))
          (reason-ref
            (native-first-coverage-field
              (00000001 reason)
              row))
          (evidence
            (native-first-coverage-field
              (00000001 evidence)
              row)))
      (native-first-coverage-all-pass-state
        (00100111
          (native-first-coverage-present-state reason-ref)
          (native-first-coverage-check
            evidence
            (00000001 native-first-dispatch-witness))
          (native-first-coverage-fallback-plan-state expression))))))

(00001001 native-first-coverage-blocked-row-state
  (00001000 (row)
    (native-first-coverage-all-pass-state
      (00100111
        (native-first-coverage-fallback-row-state row)
        (native-first-coverage-present-state
          (native-first-coverage-field
            (00000001 prerequisite)
            row))))))

(00001001 native-first-coverage-row-state
  (00001000 (row)
    (00000111
      ((00000010 row) () (00000001 fail))
      ((00000010 row) (1) (00000001 fail))
      ((00000010 row) (0)
       (00000111
         ((00100010 (00000101 row) (00000001 native-coverage))
          (10011100 ((status
                  (native-first-coverage-field
                    (00000001 status)
                    row)))
            (00000111
              ((00100010 status (00000001 native-supported))
               (native-first-coverage-native-row-state row))
              ((00100010 status (00000001 fallback-required))
               (native-first-coverage-fallback-row-state row))
              ((00100010 status (00000001 blocked-runtime-prerequisite))
               (native-first-coverage-blocked-row-state row))
              (t (00000001 fail)))))
         ((00100010 (00100010 (00000101 row) (00000001 native-coverage)) (00100010 (00000001 d1-no-left) (00000001 d1-no-right)))
          (00000001 fail)))))))

(00001001 native-first-coverage-all-valid-state
  (00001000 (rows)
    (00000111
      ((00000010 rows) () (00000001 pass))
      ((00000010 rows) (1) (00000001 fail))
      ((00000010 rows) (0)
       (10011100 ((row-state
               (native-first-coverage-row-state (00000101 rows))))
         (00000111
           ((00000011 row-state (00000001 pass)) (1)
            (native-first-coverage-all-valid-state (00000110 rows)))
           ((00000011 row-state (00000001 pass)) (0)
            (00000001 fail))))))))

(00001001 native-first-coverage-expected-authority-row-state
  (00001000 (row)
    (10011100 ((status
            (native-first-coverage-field (00000001 status) row))
          (expected
            (native-first-coverage-field (00000001 expected) row)))
      (00000111
        ((00100010 status (00000001 native-supported))
         (native-first-coverage-present-state expected))
        ((00100010 status (00000001 fallback-required))
         (native-first-coverage-check expected (00000001 ())))
        ((00100010 status (00000001 blocked-runtime-prerequisite))
         (native-first-coverage-check expected (00000001 ())))
        (t (00000001 fail))))))

(00001001 native-first-coverage-expected-authority-state
  (00001000 (rows)
    (00000111
      ((00000010 rows) () (00000001 pass))
      ((00000010 rows) (1) (00000001 fail))
      ((00000010 rows) (0)
       (10011100 ((row-state
               (native-first-coverage-expected-authority-row-state
                 (00000101 rows))))
         (00000111
           ((00000011 row-state (00000001 pass)) (1)
            (native-first-coverage-expected-authority-state (00000110 rows)))
           ((00000011 row-state (00000001 pass)) (0)
            (00000001 fail))))))))

(00001001 native-first-coverage-count-status-onto
  (00001000 (rows status count)
    (00000111
      ((00000010 rows) () count)
      ((00000010 rows) (1) count)
      ((00000010 rows) (0)
       (00000111
         ((00100010
            (native-first-coverage-field
              (00000001 status)
              (00000101 rows))
            status)
          (native-first-coverage-count-status-onto
            (00000110 rows)
            status
            (00001100 count 1)))
         ((00100010 (00100010
            (native-first-coverage-field
              (00000001 status)
              (00000101 rows))
            status) (00100010 (00000001 d1-no-left) (00000001 d1-no-right)))
          (native-first-coverage-count-status-onto
            (00000110 rows)
            status
            count)))))))

(00001001 native-first-coverage-count-status
  (00001000 (status)
    (native-first-coverage-count-status-onto
      native-first-coverage-ledger
      status
      0)))

(00001001 native-first-coverage-dispatch-independent-state
  (native-first-coverage-all-pass-state
    (00100111
      (native-first-coverage-check
        (00111110
          "native-first-coverage"
          (10100110 "lib/machine/dispatch/native-first.lisp"))
        (00000001 ()))
      (native-first-coverage-check
        (00111110
          "native-first-coverage"
          (10100110 "lib/machine/dispatch/native-first-execute.lisp"))
        (00000001 ()))
      (native-first-coverage-check
        (00111110
          "native-first-coverage"
          (10100110 "lib/machine/dispatch/native-first-parity.lisp"))
        (00000001 ())))))

(00001001 native-first-coverage-ledger-witness
  (00001000 ()
    (10011100 ((native-count
            (native-first-coverage-count-status
              (00000001 native-supported)))
          (fallback-count
            (native-first-coverage-count-status
              (00000001 fallback-required)))
          (blocked-count
            (native-first-coverage-count-status
              (00000001 blocked-runtime-prerequisite))))
      (10011100 ((verdict
              (native-first-coverage-all-pass-state
                (00100111
                  native-first-coverage-dispatch-independent-state
                  (native-first-coverage-all-valid-state
                    native-first-coverage-ledger)
                  (native-first-coverage-expected-authority-state
                    native-first-coverage-ledger)
                  (native-first-coverage-check
                    (00101000 native-first-coverage-ledger)
                    6)
                  (native-first-coverage-check native-count 1)
                  (native-first-coverage-check fallback-count 2)
                  (native-first-coverage-check blocked-count 3)))))
        (00000111
          ((00000011 verdict (00000001 pass)) (1)
           (00100111
             (00000001 native-first-coverage-ledger-witness)
             (00000001 (status pass))
             (00100111 (00000001 rows) 6)
             (00100111 (00000001 native) native-count)
             (00100111 (00000001 fallback) fallback-count)
             (00100111 (00000001 blocked) blocked-count)))
          ((00000011 verdict (00000001 pass)) (0)
           (00100111
             (00000001 native-first-coverage-ledger-witness)
             (00000001 (status fail))
             (00100111 (00000001 rows)
                   (00101000 native-first-coverage-ledger))
             (00100111 (00000001 native) native-count)
             (00100111 (00000001 fallback) fallback-count)
             (00100111 (00000001 blocked) blocked-count))))))))

(native-first-coverage-ledger-witness)
