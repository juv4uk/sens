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

(00001001 native-first-execution-witness-check
  (00001000 (actual expected)
    (00000111
      ((00100010 actual expected)
       (00000001 pass))
      ((00100010 (00100010 actual expected)
     (00100010 (00000001 d1-no-left) (00000001 d1-no-right)))
       (00100111 (00000001 fail) actual expected)))))

(00001001 native-first-execution-witness
  (00001000 ()
    (00100111
      ; Supported bounded structural slice really reaches the CPU.
      (native-first-execution-witness-check
        (native-first-execute-expression
          (00000001 (car (cons 2 3))))
        (00000001
          (execution-route native
            (status completed)
            (value 2))))

      ; Unsupported ordinary Lisp is not an error: it stays evaluator-owned.
      (native-first-execution-witness-check
        (native-first-execute-expression
          (00000001 (+ 2 3)))
        (00000001
          (execution-route evaluator
            (status completed)
            (value 5))))

      ; Source text is parsed, then every top-level form is routed separately.
      (native-first-execution-witness-check
        (native-first-execute-source
          "(+ 1 2)
(car (cons 7 9))")
        (00000001
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
          (00000001
            (native-plan
              ((definitely-not-an-admitted-machine-form))
              0)))
        (00000001
          (execution-route native
            (status rejected)
            (detail
              (rejected
                unadmitted-machine-form
                (definitely-not-an-admitted-machine-form))))))

      ; Malformed native plans also fail closed on the native route.
      (native-first-execution-witness-check
        (native-first-execute-plan
          (00000001 (native-plan ((ret)))))
        (00000001
          (execution-route native
            (status rejected)
            (detail
              (malformed-native-plan
                (native-plan ((ret)))))))))))

(native-first-execution-witness)
