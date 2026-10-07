; #505 — native-first classification witness.
; Lisp owns the routing decision. This fixture never executes raw machine code.

(load "lib/core.lisp")
(load "lib/machine/encoding/x86-64.lisp")
(load "lib/machine/layout/pair-x86-64.lisp")
(load "lib/machine/operands/x86-64.lisp")
(load "lib/machine/lowering/semantic-x86-64.lisp")
(load-mixed-exact-domain "lib/machine/dispatch/native-first.lisp")

(00001001 native-first-witness-check
  (00001000 (actual expected)
    (00000111
      ((00100010 actual expected) (1) (00000001 pass))
      ((00000001 native-first-witness-fallback)
       native-first-witness-fallback
       (00100111 (00000001 fail) actual expected)))))

(00100111
  (native-first-witness-check
    (native-first-plan (00000001 (car (cons 2 3))))
    (00100111
      (00000001 native-plan)
      (x86-lower-cons-car-u64-forms 2 3)
      x86-pair-cell-bytes))
  (native-first-witness-check
    (native-first-plan (00000001 (+ 2 3)))
    (00000001 (evaluator-fallback (+ 2 3))))
  (native-first-witness-check
    (native-first-plan (00000001 (car (cons (+ 1 1) 3))))
    (00000001 (evaluator-fallback (car (cons (+ 1 1) 3)))))
  (native-first-witness-check
    (native-first-plan (00000001 (car (cons -1 3))))
    (00000001 (evaluator-fallback (car (cons -1 3)))))
  (native-first-witness-check
    (native-first-plan (00000001 radio))
    (00000001 (evaluator-fallback radio)))
  (native-first-witness-check
    (native-first-plan (00000001 (car . radio)))
    (00000001 (evaluator-fallback (car . radio)))))
