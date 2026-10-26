; SENS_SOURCE: M1 negative witness — improper D3 tail.
; NATIVE_SENS_NEGATIVE: native evaluator must fail with D3 Type, not pass.
; Use an already admitted symbol; the test targets the improper tail, not Text7 lookup.
(запустити-твердження
  (сполучити
    (список (як-є єдиний-тест)
      (функція () (атом? (як-є ()))))
    (як-є єдиний-тест)))
