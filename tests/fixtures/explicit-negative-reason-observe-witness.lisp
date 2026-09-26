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

(def explicit-negative-reason-observe-check
  (lambda ()
    (let* ((goal (quote (not? (planet earth))))
           (actual (reason-observe goal (quote ())))
           (expected (quote ())))
      (cond
        ((equal? actual expected) (1)
         (quote (explicit-negative-reason-observe-witness (status pass))))
        ((equal? actual expected) (0)
         (list
           (quote explicit-negative-reason-observe-witness)
           (quote (status fail))
           (quote (law explicit-negative-valid-no-evidence-canon-zero))
           (list (quote expected) expected)
           (list (quote actual) actual)))))))

(explicit-negative-reason-observe-check)
