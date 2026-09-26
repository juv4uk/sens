; #218 — deep structural relation witnesses for Lisp-owned equal?.
; equal? reports a structural relation; it does not borrow universal truth.

((expr . "(equal? (quote ()) (quote ()))")
 (expected . "(1)")
 (active . t))

((expr . "(equal? (quote radio) (quote radio))")
 (expected . "(1)")
 (active . t))

((expr . "(equal? (quote radio) (quote antenna))")
 (expected . "(0)")
 (active . t))

((expr . "(equal? (quote (radio antenna)) (quote (radio antenna)))")
 (expected . "(1)")
 (active . t))

((expr . "(equal? (quote (radio antenna)) (quote (radio signal)))")
 (expected . "(0)")
 (active . t))

((expr . "(equal? (quote (radio)) (quote radio))")
 (expected . "(0)")
 (active . t))

; #295 — reader/wire-format boundary: a printed dotted pair must reconstruct
; the same structure. The law lives in Lisp data; the existing observer only
; transports the actual result.
((expr . "(equal? (read \"(p . 0)\") (cons (quote p) 0))")
 (expected . "(1)")
 (active . t)
 (case . dotted-pair-reader-round-trip))

; #295 — a domain result produced directly and the same result produced as a
; macro expansion/re-evaluation must remain structurally identical. This is
; the original regression law without reviving the old Bool/Nil representation.
((expr . "(defmacro preservation-exact-no () (< 2 1)) (equal? (< 2 1) (preservation-exact-no))")
 (expected . "(1)")
 (active . t)
 (case . macro-boundary-result-invariance))
