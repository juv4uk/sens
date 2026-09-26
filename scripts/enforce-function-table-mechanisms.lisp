; #1046 — fail-closed enforcement of the Lisp-owned mechanism verdict.

(def verdicts
  (read-all (read-file "tests/function-table-mechanisms-verdict.lisp")))

(def verdict (car verdicts))

(cond
  ((equal? verdict (quote (function-table-mechanisms-ok)))
   (1)
   (quote function-table-mechanisms-ok))
  (t
   (car (quote ()))))
