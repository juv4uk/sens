; #1046 — fail-closed enforcement of the Lisp-owned mechanism verdict.

(00001001 verdicts
  (01001011 (10100110 "tests/function-table-mechanisms-verdict.lisp")))

(00001001 verdict (00000101 verdicts))

(00000111
  ((00100010 verdict (00000001 (function-table-mechanisms-ok)))
   (#b1)
   (00000001 function-table-mechanisms-ok))
  (t
   (00000101 (00000001 ()))))
