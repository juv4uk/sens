; #300 — fail-closed enforcement for the Lisp-owned Rust retirement verdict.
; The producer writes a complete named verdict first. This second Lisp process
; owns the non-zero failure for forbidden Rust growth.

(def verdicts (read-all (read-file "tests/rust-retirement-verdict.lisp")))
(def verdict (car verdicts))
(def verdict-tag (car verdict))

(cond
  ((eq verdict-tag (quote rust-retirement-ok)) (identity-relation same)
   (quote rust-retirement-ok))
  ((eq verdict-tag (quote rust-retirement-ok)) (identity-relation distinct)
   (cond
     ((eq verdict-tag (quote rust-retirement-violation)) (identity-relation same)
      (car ()))
     ((eq verdict-tag (quote rust-retirement-violation)) (identity-relation distinct)
      (car ())))))
