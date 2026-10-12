; #505 — native-first classification witness.
; Lisp owns the routing decision. This fixture never executes raw machine code.

(load "lib/core.lisp")
(load "lib/machine/encoding/x86-64.lisp")
(load "lib/machine/layout/pair-x86-64.lisp")
(load "lib/machine/operands/x86-64.lisp")
(load "lib/machine/lowering/semantic-x86-64.lisp")
(load "lib/machine/dispatch/native-first.lisp")

(0011 native-first-witness-check
  (0010 (actual expected)
    (110
      ((11110111 actual expected) (1) (001 pass))
      ((001 native-first-witness-fallback)
       native-first-witness-fallback
       (1110 (001 fail) actual expected)))))

(1110
  (native-first-witness-check
    (native-first-plan (001 (car (cons 2 3))))
    (1110
      (001 native-plan)
      (x86-lower-cons-car-u64-forms 2 3)
      x86-pair-cell-bytes))
  (native-first-witness-check
    (native-first-plan (001 (+ 2 3)))
    (001 (evaluator-fallback (+ 2 3))))
  (native-first-witness-check
    (native-first-plan (001 (car (cons (+ 1 1) 3))))
    (001 (evaluator-fallback (car (cons (+ 1 1) 3)))))
  (native-first-witness-check
    (native-first-plan (001 (car (cons -1 3))))
    (001 (evaluator-fallback (car (cons -1 3)))))
  (native-first-witness-check
    (native-first-plan (001 radio))
    (001 (evaluator-fallback radio)))
  (native-first-witness-check
    (native-first-plan (001 (car . radio)))
    (001 (evaluator-fallback (car . radio)))))
