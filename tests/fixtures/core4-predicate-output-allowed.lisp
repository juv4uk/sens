; #1260 positive fixture: rich raw observation is allowed when an explicit
; Lisp-owned projection produces the final predicate-answer domain.

(core4-predicate-output-case/1
  ((surface . eq)
   (sid . 00000011)
   (role . predicate-question)
   (raw-domain . identity-relation)
   (projection-law . "contracts/core4-eq-result-law.lisp")
   (final-domain . predicate-answer-domain)))
