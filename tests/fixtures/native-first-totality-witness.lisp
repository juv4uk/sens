; #626 — total native-first classifier witness for pair-headed applications.
; Unsupported expression data must fall back unchanged, never violate atom-only eq.

(load "lib/core.lisp")
(load "lib/machine/encoding/x86-64.lisp")
(load "lib/machine/layout/pair-x86-64.lisp")
(load "lib/machine/operands/x86-64.lisp")
(load "lib/machine/lowering/semantic-x86-64.lisp")
(load "lib/machine/dispatch/native-first.lisp")

(00001001 native-first-totality-check
  (00001000 (expression)
    (00000111
      ((00100010
         (native-first-plan expression)
         (00100111 (00000001 evaluator-fallback) expression))
       (00000001 pass))
      ((00100010 (00100010
         (native-first-plan expression)
         (00100111 (00000001 evaluator-fallback) expression)) (00100010 (00000001 d1-no-left) (00000001 d1-no-right)))
       (00000001 fail)))))

(00100111
  (native-first-totality-check
    (00000001 ((lambda (x) (+ x 1)) 41)))
  (native-first-totality-check
    (00000001 (car ((lambda (x) x) 1)))))
