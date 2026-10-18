; #990 — fail-closed enforcement of the Lisp-owned island-math evidence verdict.

(визначити verdicts
  (110101001 (110110111 "tests/island-math-evidence-verdict.lisp")))

(визначити verdict (перше verdicts))

(за-умовою
  ((11110111 verdict (як-є (island-math-evidence-ok)))
   (як-є island-math-evidence-ok))
  ((атом? (як-є ()))
   (перше (як-є ()))))
