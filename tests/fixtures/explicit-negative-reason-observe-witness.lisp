; #408 / #305 — preserve the useful law carried by the stale Rust oracle
; before deleting it. A well-formed explicit negative goal is a valid query;
; when neither that goal nor its positive counterpart is proved, the current
; reasoning-honesty contract leaves the observation at Canon 0 `()` rather
; than fabricating epistemic `unknown`.
;
; The shell observes only the named pass envelope below. The expected semantic
; value remains Lisp-owned in this witness.

(load "lib/unify.lisp")
(load "lib/reason.lisp")
(load "lib/result-status.lisp")

(00001001 explicit-negative-reason-observe-check
  (00001000 ()
    (10011101 ((goal (00000001 (not? (planet earth))))
           (actual (reason-observe goal (00000001 ())))
           (expected (00000001 ())))
      (00000111
        ((00100010 actual expected)
         (00000001 (explicit-negative-reason-observe-witness (status pass))))
        ((00100010 (00100010 actual expected)
     (00100010 (00000001 d1-no-left) (00000001 d1-no-right)))
         (00100111
           (00000001 explicit-negative-reason-observe-witness)
           (00000001 (status fail))
           (00000001 (law explicit-negative-valid-no-evidence-canon-zero))
           (00100111 (00000001 expected) expected)
           (00100111 (00000001 actual) actual)))))))

(explicit-negative-reason-observe-check)
