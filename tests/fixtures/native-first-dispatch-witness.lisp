; #505 — native-first classification witness.
; Lisp owns the routing decision. This fixture never executes raw machine code.

(load "lib/core.lisp")
(load "lib/machine/encoding/x86-64.lisp")
(load "lib/machine/layout/pair-x86-64.lisp")
(load "lib/machine/operands/x86-64.lisp")
(load "lib/machine/lowering/semantic-x86-64.lisp")
(load "lib/machine/dispatch/native-first.lisp")

(def native-first-witness-check
  (lambda (actual expected)
    (cond
      ((equal? actual expected) (1) (quote pass))
      ((quote native-first-witness-fallback)
       native-first-witness-fallback
       (list (quote fail) actual expected)))))

(list
  (native-first-witness-check
    (native-first-plan (quote (car (cons 2 3))))
    (list
      (quote native-plan)
      (x86-lower-cons-car-u64-forms 2 3)
      x86-pair-cell-bytes))
  (native-first-witness-check
    (native-first-plan (quote (+ 2 3)))
    (quote (evaluator-fallback (+ 2 3))))
  (native-first-witness-check
    (native-first-plan (quote (car (cons (+ 1 1) 3))))
    (quote (evaluator-fallback (car (cons (+ 1 1) 3)))))
  (native-first-witness-check
    (native-first-plan (quote (car (cons -1 3))))
    (quote (evaluator-fallback (car (cons -1 3)))))
  (native-first-witness-check
    (native-first-plan (quote radio))
    (quote (evaluator-fallback radio)))
  (native-first-witness-check
    (native-first-plan (quote (car . radio)))
    (quote (evaluator-fallback (car . radio)))))
