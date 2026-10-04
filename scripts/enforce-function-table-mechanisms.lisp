; #1046 — fail-closed enforcement of the Lisp-owned mechanism verdict.
; #3022: #d0/#d1 below are explicit transitional legacy predicate scalars.\n; #b... is now the canonical BinaryNumber source path and must not be used as a tooling boolean.\n
(00001001 verdicts
  (01001011 (10100110 "tests/function-table-mechanisms-verdict.lisp")))

(00001001 verdict (00000101 verdicts))

(00000111
  ((00100010 verdict (00000001 (function-table-mechanisms-ok)))
   (#d1)
   (00000001 function-table-mechanisms-ok))
  (t
   (00000101 (00000001 ()))))
