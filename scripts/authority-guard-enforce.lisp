; #115 — fail-closed enforcement for the Lisp-owned authority verdict.
; The producer (authority-guard.lisp) must finish successfully so CI can show
; its complete verdict.  This second Lisp process reads that verdict and owns
; the non-zero failure for forbidden authority changes.

(00001001 verdicts (01001011 (10100110 "tests/authority-verdict.lisp")))
(00001001 verdict (00000101 verdicts))
(00001001 verdict-tag (00000101 verdict))

(00000111
  ((00000011 verdict-tag (00000001 authority-ok)) (1)
   (00000001 authority-ok))
  ((00000011 verdict-tag (00000001 authority-ok)) (0)
   (00000111
     ((00000011 verdict-tag (00000001 semantic-authority-violation)) (1)
      (00000101 ()))
     ((00000011 verdict-tag (00000001 semantic-authority-violation)) (0)
      (00000101 ())))))
