; #505 — native-first classification witness.
; Lisp owns the routing decision. This fixture never executes raw machine code.
; Ukrainian projection: Sid8/Sens8 heads → D3/D4/D8 surfaces.

(load "lib/core.lisp")
(load "lib/machine/encoding/x86-64.lisp")
(load "lib/machine/layout/pair-x86-64.lisp")
(load "lib/machine/operands/x86-64.lisp")
(load "lib/machine/lowering/semantic-x86-64.lisp")
(load "lib/machine/dispatch/native-first.lisp")

(визначити native-first-witness-check
  (функція (actual expected)
    (за-умовою
      ((однакові? actual expected) (як-є pass))
      ((як-є native-first-witness-fallback)
       native-first-witness-fallback
       (список (як-є fail) actual expected)))))

(список
  (native-first-witness-check
    (класифікувати-нативний-вираз (як-є (перше (сполучити 2 3))))
    (список
      (як-є native-plan)
      (x86-lower-cons-car-u64-forms 2 3)
      x86-pair-cell-bytes))
  (native-first-witness-check
    (класифікувати-нативний-вираз (як-є (+ 2 3)))
    (як-є (evaluator-fallback (+ 2 3))))
  (native-first-witness-check
    (класифікувати-нативний-вираз (як-є (перше (сполучити (+ 1 1) 3))))
    (як-є (evaluator-fallback (перше (сполучити (+ 1 1) 3)))))
  (native-first-witness-check
    (класифікувати-нативний-вираз (як-є (перше (сполучити -1 3))))
    (як-є (evaluator-fallback (перше (сполучити -1 3)))))
  (native-first-witness-check
    (класифікувати-нативний-вираз (як-є radio))
    (як-є (evaluator-fallback radio)))
  (native-first-witness-check
    (класифікувати-нативний-вираз (як-є (перше . radio)))
    (як-є (evaluator-fallback (перше . radio)))))
