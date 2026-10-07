; #231/#220 — Lisp-owned transition overlay for historical conformance rows.
;
; `tests/fixtures/conformance.lisp` is preserved as historical evidence.  A row
; listed here no longer owns current semantic authority; `supersedes-expr`
; identifies the historical expression and the ordinary `expr`/`expected`
; fields provide its current executable replacement.
;
; Rust may transport this mapping, but it must not invent either the retired
; expression or its replacement.  When the historical two-part-cond corpus is
; eventually archived as a whole, this overlay can disappear with it.

((supersedes-expr . "(cond (0 (quote truthy)) (t (quote falsy)))")
 (expr . "(cond (0 1 (quote wrong)) (0 0 (quote zero-data)))")
 (expected . "zero-data")
 (meta-eval . t)
 (reason . universal-zero-truthiness-retired)
 (owner . "217/220/231"))

((supersedes-expr . "(cond (0 (quote zero-is-truthy)) (t (quote wrong)))")
 (expr . "(cond (0 1 (quote wrong)) (1 1 (quote explicit-fallback)))")
 (expected . "explicit-fallback")
 (meta-eval . t)
 (reason . universal-zero-truthiness-retired)
 (owner . "217/220/231"))

((supersedes-expr . "(= 3 3.0)")
 (expr . "(= 3 3.0)")
 (expected . "1")
 (compiler-corpus . t)
 (reason . exact-q-result-algebra-supersedes-truth-sentinel)
 (owner . "216/220/631"))

((supersedes-expr . "(cond (() (quote first)) (() (quote second)) (t (quote third)))")
 (expr . "(за-умовою (() (як-є first)) (() (як-є second)))")
 (expected . "()")
 (meta-eval . t)
 (owner . "4196/4166"))

((supersedes-expr . "(cond ((quote radio) antenna (quote wrong)))")
 (expr . "(за-умовою ((тотожне? (як-є radio) (як-є radio)) (як-є antenna)))")
 (expected . "antenna")
 (meta-eval . t)
 (owner . "4196/4166"))
