; #506 — native-first execution bridge witness.
; Route choice, CPU execution, evaluator fallback, source parsing, non-masking.
; Ukrainian projection: Sid8/Sens8 → D3/D4/D8.

(load "lib/core.lisp")
(load "lib/machine/encoding/x86-64.lisp")
(load "lib/machine/layout/pair-x86-64.lisp")
(load "lib/machine/operands/x86-64.lisp")
(load "lib/machine/admission/x86-64.lisp")
(load "lib/machine/lowering/semantic-x86-64.lisp")
(load "lib/machine/dispatch/native-first.lisp")
(load "lib/machine/dispatch/native-first-execute.lisp")

(визначити native-first-execution-witness-check
  (функція (actual expected)
    (за-умовою
      ((однакові? actual expected) (як-є pass))
      ((однакові? actual expected) (як-є ні)
       (список (як-є fail) actual expected)))))

(визначити native-first-execution-witness
  (функція ()
    (список
      ; Supported bounded structural slice reaches the CPU.
      (native-first-execution-witness-check
        (native-first-execute-expression
          (як-є (перше (сполучити 2 3))))
        (як-є
          (execution-route native
            (status completed)
            (value 2))))

      ; Unsupported ordinary Lisp stays evaluator-owned.
      (native-first-execution-witness-check
        (native-first-execute-expression
          (як-є (+ 2 3)))
        (як-є
          (execution-route evaluator
            (status completed)
            (value 5))))

      ; Source text is parsed; each top-level form is routed separately.
      (native-first-execution-witness-check
        (native-first-execute-source
          "(+ 1 2)
(car (cons 7 9))")
        (як-є
          (source-execution
            ((execution-route evaluator
               (status completed)
               (value 3))
             (execution-route native
               (status completed)
               (value 7))))))

      ; Once a native plan exists, admission rejection stays visibly native.
      (native-first-execution-witness-check
        (native-first-execute-plan
          (як-є
            (native-plan
              ((definitely-not-an-admitted-machine-form))
              0)))
        (як-є
          (execution-route native
            (status rejected)
            (detail
              (rejected
                unadmitted-machine-form
                (definitely-not-an-admitted-machine-form))))))

      ; Malformed native plans fail closed on the native route.
      (native-first-execution-witness-check
        (native-first-execute-plan
          (як-є (native-plan ((ret)))))
        (як-є
          (execution-route native
            (status rejected)
            (detail
              (malformed-native-plan
                (native-plan ((ret)))))))))))

(native-first-execution-witness)
