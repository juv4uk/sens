; #216 — Lisp-owned exact-Q binary decision witnesses.
; Expected kind/magnitude and domain status live here; Rust only transports
; the actual runtime kind/rendering to the Lisp verifier.

((expr . "(= 1/3 2/6)")
 (expected-kind . rational)
 (expected-render . "1")
 (decision . yes)
 (active . t))

((expr . "(< 2/3 3/4)")
 (expected-kind . rational)
 (expected-render . "1")
 (decision . yes)
 (active . t))

((expr . "(> 2/3 3/4)")
 (expected-kind . rational)
 (expected-render . "0")
 (decision . no)
 (active . t))

((expr . "(= 3 3)")
 (expected-kind . rational)
 (expected-render . "1")
 (decision . yes)
 (active . t))

((expr . "(< 1 2 3 4)")
 (expected-kind . rational)
 (expected-render . "1")
 (decision . yes)
 (active . t))

; Inexact values are outside the absolute exact-Q binary layer.
((expr . "(= 3.0 3.0)")
 (expected-kind . empty-list)
 (expected-render . "()")
 (decision . no-answer)
 (active . t))

((expr . "(< 0.5 1.0)")
 (expected-kind . empty-list)
 (expected-render . "()")
 (decision . no-answer)
 (active . t))
