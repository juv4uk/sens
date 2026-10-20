; #408 / #305 — preserve the useful law carried by the stale Rust oracle
; before deleting it. A well-formed explicit negative goal is a valid query;
; when neither that goal nor its positive counterpart is proved, the current
; reasoning-honesty contract leaves the observation at empty rather
; than fabricating epistemic unknown.
;
; Ukrainian projection only.

(load "lib/unify.lisp")
(load "lib/reason.lisp")
(load "lib/result-status.lisp")

(визначити explicit-negative-reason-observe-check
  (функція ()
    (нехай ((goal (як-є (not? (planet earth))))
           (actual (reason-observe goal (як-є ())))
           (expected (як-є ())))
      (за-умовою
        ((тотожне? actual expected)
         (як-є (explicit-negative-reason-observe-witness (status pass))))
        (так
         (список
           (як-є explicit-negative-reason-observe-witness)
           (як-є (status fail))
           (як-є (law explicit-negative-valid-no-evidence-canon-zero))
           (список (як-є expected) expected)
           (список (як-є actual) actual)))))))

(explicit-negative-reason-observe-check)
