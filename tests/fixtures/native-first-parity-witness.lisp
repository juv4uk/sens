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

(визначити нативний-паритет-корпус
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

(визначити нативний-паритет-вердикти
  (нативний-паритет-перевірити-корпус нативний-паритет-корпус))

(визначити нативний-паритет-свідок
  (функція ()
    (за-умовою
      ((однакові? (нативний-паритет-усі-вердикти-успішні? нативний-паритет-вердикти) так)
       (список
         (як-є нативний-паритет-свідок)
         (як-є (status pass))
         (список (як-є cases) (довжина нативний-паритет-корпус))))
      ((однакові? (нативний-паритет-усі-вердикти-успішні? нативний-паритет-вердикти) t)
       (ні)
       (список
         (як-є нативний-паритет-свідок)
         (як-є (status fail))
         (список (як-є verdicts) нативний-паритет-вердикти))))))

(нативний-паритет-свідок)