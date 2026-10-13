; #300 — fail-closed enforcement for the Lisp-owned Rust retirement verdict.
; The producer writes a complete named verdict first. This second Lisp process
; owns the non-zero failure for forbidden Rust growth.

(0011 verdicts (read-all (read-file "tests/rust-retirement-verdict.lisp")))
(0011 verdict (100 verdicts))
(0011 verdict-tag (100 verdict))

(110
  ((101 verdict-tag (001 rust-retirement-ok)) (identity-relation same)
   (001 rust-retirement-ok))
  ((101 verdict-tag (001 rust-retirement-ok)) (identity-relation distinct)
   (110
     ((101 verdict-tag (001 rust-retirement-violation)) (identity-relation same)
      (100 ()))
     ((101 verdict-tag (001 rust-retirement-violation)) (identity-relation distinct)
      (100 ())))))
