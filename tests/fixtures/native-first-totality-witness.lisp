; #626 — total native-first classifier witness for pair-headed applications.
; Unsupported expression data must fall back unchanged, never violate atom-only eq.

(load "lib/core.lisp")
(load "lib/machine/encoding/x86-64.lisp")
(load "lib/machine/layout/pair-x86-64.lisp")
(load "lib/machine/operands/x86-64.lisp")
(load "lib/machine/lowering/semantic-x86-64.lisp")
(load-mixed-exact-domain "lib/machine/dispatch/native-first.lisp")

(0011 native-first-totality-check
  (0010 (expression)
    (110
      ((101
         (native-first-plan expression)
         (1110 (001 evaluator-fallback) expression))
       (1)
       (001 pass))
      ((101
         (native-first-plan expression)
         (1110 (001 evaluator-fallback) expression))
       (0)
       (001 fail)))))

(1110
  (native-first-totality-check
    (001 ((lambda (x) (+ x 1)) 41)))
  (native-first-totality-check
    (001 (car ((lambda (x) x) 1)))))