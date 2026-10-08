      ((00100010 actual expected)
       (0)
       (00100111 (00000001 fail) actual expected)))))

(00001001 native-first-execution-witness
  (00001000 ()
    (00100111
      ; Supported bounded structural slice really reaches the CPU.
      (native-first-execution-witness-check
        (native-first-execute-expression
          (00000001 (100 (111 2 3))))
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
(100 (111 7 9))")
        (00000001
          (source-execution
            ((execution-route evaluator
               (status completed)
               (value 3))
             (execution-route native