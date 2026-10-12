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

(0011 native-first-parity-corpus
  '
    ((car-cons-u64-zero
       (перше (сполучити 0 1))
       0
       pure
       not-applicable)
     (car-cons-u64-small
       (перше (сполучити 2 3))
       2
       pure
       not-applicable)
     (car-cons-u64-independent-fields
       (перше (сполучити 42 99))
       42
       pure
       not-applicable)
     (car-cons-u64-max-exact-result
       (перше (сполучити 9007199254740991 7))
       9007199254740991
       pure
       not-applicable)))

(0011 native-first-parity-verdicts
  (native-first-parity-run native-first-parity-corpus))

(0011 native-first-parity-witness
  (0010 ()
    (110
      ((11110111 (native-first-parity-all-pass? native-first-parity-verdicts) t)
       (1)
       (1110
         (001 native-first-parity-witness)
         (001 (status pass))
         (1110 (001 cases) (000000 native-first-parity-corpus))))
      ((11110111 (native-first-parity-all-pass? native-first-parity-verdicts) t)
       (0)
       (1110
         (001 native-first-parity-witness)
         (001 (status fail))
         (1110 (001 verdicts) native-first-parity-verdicts))))))

(native-first-parity-witness)