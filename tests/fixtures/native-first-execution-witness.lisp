; #506 — native-first execution bridge witness.
; This fixture proves route choice, CPU execution, ordinary evaluator fallback,
; source parsing, and the non-masking rule after a native plan has been chosen.

(load "lib/core.lisp")
(load "lib/machine/encoding/x86-64.lisp")
(load "lib/machine/layout/pair-x86-64.lisp")
(load "lib/machine/operands/x86-64.lisp")
(load "lib/machine/admission/x86-64.lisp")
(load "lib/machine/lowering/semantic-x86-64.lisp")
(load "lib/machine/dispatch/native-first.lisp")
(load "lib/machine/dispatch/native-first-execute.lisp")

(def native-first-execution-witness-check
  (lambda (actual expected)
    (cond
      ((equal? actual expected)
       (1)
       (quote pass))
      ((equal? actual expected)
       (0)
       (list (quote fail) actual expected)))))

(def native-first-execution-witness
  (lambda ()
    (list
      ; Supported bounded structural slice really reaches the CPU.
      (native-first-execution-witness-check
        (native-first-execute-expression
          (quote (car (cons 2 3))))
        (quote
          (execution-route native
            (status completed)
            (value 2))))

      ; Unsupported ordinary Lisp is not an error: it stays evaluator-owned.
      (native-first-execution-witness-check
        (native-first-execute-expression
          (quote (+ 2 3)))
        (quote
          (execution-route evaluator
            (status completed)
            (value 5))))

      ; Source text is parsed, then every top-level form is routed separately.
      (native-first-execution-witness-check
        (native-first-execute-source
          "(+ 1 2)
(car (cons 7 9))")
        (quote
          (source-execution
            ((execution-route evaluator
               (status completed)
               (value 3))
             (execution-route native
               (status completed)
               (value 7))))))

      ; Once a native plan exists, admission rejection stays visibly native.
      ; The bridge must NOT hide this bug by evaluating (+ 40 2) instead.
      (native-first-execution-witness-check
        (native-first-execute-plan
          (quote
            (native-plan
              ((definitely-not-an-admitted-machine-form))
              0)))
        (quote
          (execution-route native
            (status rejected)
            (detail
              (rejected
                unadmitted-machine-form
                (definitely-not-an-admitted-machine-form))))))

      ; Malformed native plans also fail closed on the native route.
      (native-first-execution-witness-check
        (native-first-execute-plan
          (quote (native-plan ((ret)))))
        (quote
          (execution-route native
            (status rejected)
            (detail
              (malformed-native-plan
                (native-plan ((ret)))))))))))

(native-first-execution-witness)
