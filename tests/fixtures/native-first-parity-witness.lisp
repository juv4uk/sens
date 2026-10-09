; #509 — native/evaluator differential parity gate for every currently
; admitted native-first island. Independent expected values prevent the native
; route and the evaluator from serving as each other's only oracle.

(load "lib/core.lisp")
(load "lib/machine/encoding/x86-64.lisp")
(load "lib/machine/layout/pair-x86-64.lisp")
(load "lib/machine/operands/x86-64.lisp")
(load "lib/machine/admission/x86-64.lisp")
(load "lib/machine/lowering/semantic-x86-64.lisp")
(load "lib/machine/dispatch/native-first.lisp")
(load "lib/machine/dispatch/native-first-execute.lisp")
(load "lib/machine/dispatch/native-first-parity.lisp")

(00001001 native-first-parity-corpus
  (00000001
    ((car-cons-u64-zero
       (car (cons 0 1))
       0
       pure
       not-applicable)
     (car-cons-u64-small
       (car (cons 2 3))
       2
       pure
       not-applicable)
     (car-cons-u64-independent-fields
       (car (cons 42 99))
       42
       pure
       not-applicable)
     (car-cons-u64-max-exact-result
       (car (cons 9007199254740991 7))
       9007199254740991
       pure
       not-applicable))))

(00001001 native-first-parity-verdicts
  (native-first-parity-run native-first-parity-corpus))

(00001001 native-first-parity-witness
  (00001000 ()
    (00000111
      ((00100010 (native-first-parity-all-pass? native-first-parity-verdicts) t)
       (00100111
         (00000001 native-first-parity-witness)
         (00000001 (status pass))
         (00100111 (00000001 cases) (00101000 native-first-parity-corpus))))
      ((00100010 (00100010 (native-first-parity-all-pass? native-first-parity-verdicts) t) (00100010 (00000001 d1-no-left) (00000001 d1-no-right)))
       (00100111
         (00000001 native-first-parity-witness)
         (00000001 (status fail))
         (00100111 (00000001 verdicts) native-first-parity-verdicts))))))

(native-first-parity-witness)
