; #217 — executable targets for canonical explicit control.
;
; Control consumes domain-owned results. It does not decide that arbitrary
; Lisp values are true/false from their shape.
;
; Exact-Q decisions are the one mathematical binary input in this first slice:
;   1/1 (canonical write 1) -> select clause
;   0/1 (canonical write 0) -> continue to the next clause
;
; All other rows below must be rejected when used implicitly as a condition.

((expr . "(cond (1 7))")
 (expected . "7")
 (active . t)
 (case . exact-q-yes-selects))

((expr . "(cond (0 7) (1 9))")
 (expected . "9")
 (active . t)
 (case . exact-q-no-continues))

((expr . "(cond (1/2 7))")
 (error . "Type")
 (active . t)
 (case . ordinary-rational-is-not-decision))

((expr . "(cond (2 7))")
 (error . "Type")
 (active . t)
 (case . ordinary-integer-is-not-decision))

((expr . "(cond (() 7))")
 (error . "Type")
 (active . t)
 (case . empty-list-is-not-false))

((expr . "(cond ((quote radio) 7))")
 (error . "Type")
 (active . t)
 (case . symbol-is-not-condition))

((expr . "(cond ((quote (radio)) 7))")
 (error . "Type")
 (active . t)
 (case . list-is-not-condition))
