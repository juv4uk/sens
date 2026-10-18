; #300 — fail-closed enforcement for the Lisp-owned Rust retirement verdict.
; The producer writes a complete named verdict first. This second Lisp process
; owns the non-zero failure for forbidden Rust growth.

(визначити verdicts (читати-всі (читати-файл "tests/rust-retirement-verdict.lisp")))
(визначити verdict (перше verdicts))
(визначити verdict-tag (перше verdict))

(за-умовою
  ((тотожне? verdict-tag (як-є rust-retirement-ok)) (identity-relation same)
   (як-є rust-retirement-ok))
  ((тотожне? verdict-tag (як-є rust-retirement-ok)) (identity-relation distinct)
   (за-умовою
     ((тотожне? verdict-tag (як-є rust-retirement-violation)) (identity-relation same)
      (перше ()))
     ((тотожне? verdict-tag (як-є rust-retirement-violation)) (identity-relation distinct)
      (перше ())))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити читати-всі read-all)
