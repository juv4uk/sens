; #990 — fail-closed enforcement of the Lisp-owned island-math evidence verdict.

(def verdicts
  (read-all (read-file "tests/island-math-evidence-verdict.lisp")))

(def verdict (car verdicts))

(cond
  ((equal? verdict (quote (island-math-evidence-ok)))
   (structural-relation same)
   (quote island-math-evidence-ok))
  (t
   (car (quote ()))))
