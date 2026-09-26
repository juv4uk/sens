; #217 — canonical explicit-result dispatch witnesses.
; Each three-part clause is (query expected-datum expression).

((expr . "(cond ((quote (structural-kind pair)) (structural-kind pair) (quote hit)))")
 (expected . "hit")
 (active . t))

((expr . "(cond ((quote (structural-kind atom)) (structural-kind pair) (quote miss)) ((quote (structural-kind atom)) (structural-kind atom) (quote hit)))")
 (expected . "hit")
 (active . t))

; Empty list is data that may be matched explicitly. It is not an implicit NO.
((expr . "(cond (() () (quote empty-matched)))")
 (expected . "empty-matched")
 (active . t))

; Arbitrary non-empty data is not implicitly YES; it selects only by explicit match.
((expr . "(cond ((quote radio) antenna (quote wrong)) ((quote radio) radio (quote matched)))")
 (expected . "matched")
 (active . t))

; Exact rational binary results dispatch by explicit equality.
((expr . "(cond (1/1 1/1 (quote yes)) (0/1 0/1 (quote no)))")
 (expected . "yes")
 (active . t))

; Historical Contract <=7 observation, retained but no longer active authority.
((expr . "(cond ((quote radio) antenna (quote wrong)))")
 (expected . "()")
 (active . ())
 (superseded-by . "Contract 8.0"))

; Contract 8.0: canonical three-part dispatch fails named on exhaustion.
((expr . "(cond ((quote radio) antenna (quote wrong)))")
 (error . "UnsatisfiedConditional")
 (active . t)
 (since-contract . (8 0)))

; Migration-only two-part clauses preserve historical atom/eq branching while
; library source is moved to canonical three-part dispatch. These rows are NOT
; semantic authority for new control; they only bound the temporary adapter.
((expr . "(cond ((00000010 (quote ())) (quote legacy-atom)) (t (quote wrong)))")
 (expected . "legacy-atom")
 (active . t)
 (compatibility . t))

((expr . "(cond ((00000010 (quote (radio))) (quote wrong)) (t (quote legacy-pair)))")
 (expected . "legacy-pair")
 (active . t)
 (compatibility . t))

((expr . "(cond ((00000011 (quote radio) (quote radio)) (quote legacy-same)) (t (quote wrong)))")
 (expected . "legacy-same")
 (active . t)
 (compatibility . t))

((expr . "(cond ((00000011 (quote radio) (quote antenna)) (quote wrong)) (t (quote legacy-distinct)))")
 (expected . "legacy-distinct")
 (active . t)
 (compatibility . t))
