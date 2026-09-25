; #1391 — Core4 final predicate-answer output boundary.
;
; Final predicate answers belong to the 15-state logic:
;   0^n | 1^n | (), n=1..7
;
; The 8-bit SENS functions are not predicate outputs.
; Two distinct SENS functions, 00000000 and 11111111, may both yield the same
; result (), preserving one undivided unknown/undirected value.

(core4-predicate-output-boundary/3

  ((profile . core4)
   (answer-authority . "contracts/core4-predicate-answer-scale.lisp")
   (boundary-authority . "contracts/core4-predicate-answer-boundary.lisp")
   (policy-role . final-output-only)
   (function-sens-space . exactly-256)
   (runtime-semantic-authority . forbidden)
   (mass-rewrite . forbidden))

  ((raw-observation-domains .
     (structural-kind
      identity-relation
      structural-relation
      class-membership
      text-order))
   (raw-observation-policy . allowed)
   (classifier-data-policy . allowed))

  ((predicate-question-final-domain . predicate-answer-domain)
   (rich-observation-as-final . forbidden)
   (explicit-lisp-projection . required-when-raw-domain-is-rich)
   (sens-function-as-final-answer . forbidden)
   (outside-domain-collapse-to-no . forbidden))

  ((logic-boundary .
     ((no-path  "0..0000000")
      (yes-path "1..1111111")
      (center   ())))
   (center-count . 1)
   (center-direction . none))

  ((function-convergence .
     ((00000000 ())
      (11111111 ())))
   (function-identities . distinct)
   (shared-result . ())
   (shared-result-count . 1)))
