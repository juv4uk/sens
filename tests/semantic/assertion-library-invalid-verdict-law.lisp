; SENS_SOURCE: tests/semantic/assertion-library-invalid-verdict-law.lisp + lib/твердження.lisp
; NATIVE_SENS_POSITIVE: the runner records one completed test.
; NATIVE_SENS_NEGATIVE: D3:() is ERROR, not D1:ні and not PASS.
((функція (звіт)
  (та
    (однакові? (перше звіт) (сполучити так (як-є ())))
    (однакові? (друге звіт) (як-є ()))
    (однакові? (третє звіт) (як-є ()))
    (однакові? (четверте звіт) (як-є ()))
    (однакові?
      (перше (решта (решта (решта (решта звіт)))))
      (сполучити (як-є не-д1-вердикт) (як-є ())))))
 (запустити-твердження
    (список
      (список (як-є не-д1-вердикт)
        (функція () (як-є ()))))))
