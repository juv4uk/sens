; #626 — total native-first classifier witness for pair-headed applications.
; Unsupported expression data must fall back unchanged.
; Ukrainian projection: Sid8/Sens8 → D3/D4/D8.

(load "lib/core.lisp")
(load "lib/machine/encoding/x86-64.lisp")
(load "lib/machine/layout/pair-x86-64.lisp")
(load "lib/machine/operands/x86-64.lisp")
(load "lib/machine/lowering/semantic-x86-64.lisp")
(load "lib/machine/dispatch/native-first.lisp")

(визначити native-first-totality-check
  (функція (expression)
    (за-умовою
      ((однакові?
         (native-first-plan expression)
         (список (як-є evaluator-fallback) expression))
       (як-є pass))
      ((однакові?
         (native-first-plan expression)
         (список (як-є evaluator-fallback) expression))
       (як-є fail)))))

(список
  (native-first-totality-check
    (як-є ((функція (x) (+ x 1)) 41)))
  (native-first-totality-check
    (як-є (перше ((функція (x) x) 1)))))
