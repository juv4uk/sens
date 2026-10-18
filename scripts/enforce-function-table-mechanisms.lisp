; #1046 — fail-closed enforcement of the Lisp-owned mechanism verdict.
; #3022: #d0/#d1 below are explicit transitional legacy predicate scalars.\n; #b... is now the canonical BinaryNumber source path and must not be used as a tooling boolean.\n
(визначити verdicts
  (110101001 (110110111 "tests/function-table-mechanisms-verdict.lisp")))

(визначити verdict (перше verdicts))

(за-умовою
  ((11110111 verdict (як-є (function-table-mechanisms-ok)))
   (як-є function-table-mechanisms-ok))
  ((атом? (як-є ()))
   (перше (як-є ()))))
