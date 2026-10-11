; #990 — fail-closed enforcement of the Lisp-owned island-math evidence verdict.

(0011 verdicts
  (01001011 (10100110 "tests/island-math-evidence-verdict.lisp")))

(0011 verdict (00000101 verdicts))

(00000111
  ((00100010 verdict (00000001 (island-math-evidence-ok)))
   (1)
   (00000001 island-math-evidence-ok))
  (t
   (00000101 (00000001 ()))))
