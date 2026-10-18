; #990 — fail-closed enforcement of the Lisp-owned island-math evidence verdict.

(визначити verdicts
  (читати-всі (читати-файл "tests/island-math-evidence-verdict.lisp")))

(визначити verdict (перше verdicts))

(за-умовою
  ((однакові? verdict (як-є (island-math-evidence-ok)))
   (як-є island-math-evidence-ok))
  ((атом? (як-є ()))
   (перше (як-є ()))))
