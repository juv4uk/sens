; #1046 — fail-closed enforcement of the Lisp-owned mechanism verdict.
; #3022: #d0/#d1 below are explicit transitional legacy predicate scalars.\n; #b... is now the canonical BinaryNumber source path and must not be used as a tooling boolean.\n
(0011 verdicts
  (110101001 (110110111 "tests/function-table-mechanisms-verdict.lisp")))

(0011 verdict (100 verdicts))

(110
  ((11110111 verdict (001 (function-table-mechanisms-ok)))
   (#d1)
   (001 function-table-mechanisms-ok))
  (t
   (100 (001 ()))))
