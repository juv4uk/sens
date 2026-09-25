; #115 — fail-closed enforcement for the Lisp-owned authority verdict.
; The producer (authority-guard.lisp) must finish successfully so CI can show
; its complete verdict.  This second Lisp process reads that verdict and owns
; the non-zero failure for forbidden authority changes.

(def verdicts (read-all (read-file "tests/authority-verdict.lisp")))
(def verdict (car verdicts))
(def verdict-tag (car verdict))

(cond
  ((eq? verdict-tag (quote authority-ok)) (identity-relation same)
   (quote authority-ok))
  ((eq? verdict-tag (quote authority-ok)) (identity-relation distinct)
   (cond
     ((eq? verdict-tag (quote semantic-authority-violation)) (identity-relation same)
      (car ()))
     ((eq? verdict-tag (quote semantic-authority-violation)) (identity-relation distinct)
      (car ())))))
