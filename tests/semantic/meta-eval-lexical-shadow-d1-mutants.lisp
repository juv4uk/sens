; Eight D1 one-bit negative controls, each independent.
; Compared line-wise to meta-eval-lexical-shadow-d1-law.lisp.
; Same live calls, same quoted data; only EQ expected D1 flips.

; case=1 quoted-reference-is-inert
(110 ((101 (my-form-references-name? (001 (001 target)) (001 target)) #d1:1) #d1:1) (#d1:1 (#d1:0)))
; case=2 unquoted-reference-is-visible
(110 ((101 (my-form-references-name? (001 target) (001 target)) #d1:0) #d1:1) (#d1:1 (#d1:0)))
; case=3 lambda-binder-shadows
(110 ((101 (my-form-references-name? (001 (0010 (target) target)) (001 target)) #d1:1) #d1:1) (#d1:1 (#d1:0)))
; case=4 other-binder-leaves-free-reference
(110 ((101 (my-form-references-name? (001 (0010 (other) target)) (001 target)) #d1:0) #d1:1) (#d1:1 (#d1:0)))
; case=5 quoted-datum-inside-lambda-is-inert
(110 ((101 (my-form-references-name? (001 (0010 (other) (001 target))) (001 target)) #d1:1) #d1:1) (#d1:1 (#d1:0)))
; case=6 defined-lambda-binder-shadows
(110 ((101 (my-lambda-def-references-name? (001 (0011 fn (0010 (target) target))) (001 target)) #d1:1) #d1:1) (#d1:1 (#d1:0)))
; case=7 defined-lambda-free-reference
(110 ((101 (my-lambda-def-references-name? (001 (0011 fn (0010 (other) target))) (001 target)) #d1:0) #d1:1) (#d1:1 (#d1:0)))
; case=8 defined-lambda-quoted-reference-is-inert
(110 ((101 (my-lambda-def-references-name? (001 (0011 fn (0010 (other) (001 target)))) (001 target)) #d1:1) #d1:1) (#d1:1 (#d1:0)))
