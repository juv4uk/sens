; #626 — total native-first classifier witness for pair-headed applications.
; Unsupported expression data must fall back unchanged, never violate atom-only eq.

(load "lib/core.lisp")
(load "lib/machine/encoding/x86-64.lisp")
(load "lib/machine/layout/pair-x86-64.lisp")
(load "lib/machine/operands/x86-64.lisp")
(load "lib/machine/lowering/semantic-x86-64.lisp")
(load "lib/machine/dispatch/native-first.lisp")

(def native-first-totality-check
  (lambda (expression)
    (cond
      ((equal?
         (native-first-plan expression)
         (list (quote evaluator-fallback) expression))
       (1)
       (quote pass))
      ((equal?
         (native-first-plan expression)
         (list (quote evaluator-fallback) expression))
       (0)
       (quote fail)))))

(list
  (native-first-totality-check
    (quote ((lambda (x) (+ x 1)) 41)))
  (native-first-totality-check
    (quote (car ((lambda (x) x) 1)))))
