; #1391 — executable witness for the Core4 15-state answer scale.

(def pas-contract
  (car (read-all (read-file "contracts/core4-predicate-answer-scale.lisp"))))
(def pas-schema (car pas-contract))
(def pas-sections (cdr pas-contract))

(def pas-field
  (lambda (section name)
    (cdr (assoc name section))))

(def pas-meta (car pas-sections))
(def pas-no (second pas-sections))
(def pas-boundary (third pas-sections))
(def pas-yes (fourth pas-sections))
(def pas-algebra (fifth pas-sections))

(def pas-no-levels (pas-field pas-no (quote levels)))
(def pas-yes-levels (pas-field pas-yes (quote levels)))

(def pas-observed
  (list
    pas-schema
    (pas-field pas-meta (quote answer-count))
    (pas-field pas-meta (quote answer-grammar))
    (pas-field pas-meta (quote sens-function-space))
    pas-no-levels
    (pas-field pas-boundary (quote boundary))
    (pas-field pas-boundary (quote sanskrit))
    (pas-field pas-boundary (quote direction))
    (pas-field pas-boundary (quote sens-function))
    (pas-field pas-boundary (quote convergence-functions))
    (pas-field pas-boundary (quote function-result))
    pas-yes-levels
    (+ (length pas-no-levels) (length pas-yes-levels) 1)
    (pas-field pas-algebra (quote not-law))
    (pas-field pas-algebra (quote weakening-law))
    (pas-field pas-algebra (quote boundary-law))
    (pas-field pas-algebra (quote eighth-bit-law))
    (pas-field pas-algebra (quote function-convergence-law))))

(def pas-expected
  (list
    (quote core4-predicate-answer-scale/2)
    15
    "0^n | 1^n | (), n=1..7"
    (quote separate-00000000-through-11111111)
    (quote
      (("0"       1 dṛḍha-niścaya)
       ("00"      2 niścaya)
       ("000"     3 nirṇaya)
       ("0000"    4 saṃbhāvanā)
       ("00000"   5 saṃśaya)
       ("000000"  6 aniścaya)
       ("0000000" 7 ajñāta-sīmā)))
    (quote ())
    (quote ajñāta)
    (quote none)
    (quote none)
    (quote (00000000 11111111))
    (quote ())
    (quote
      (("1"       1 dṛḍha-niścaya)
       ("11"      2 niścaya)
       ("111"     3 nirṇaya)
       ("1111"    4 saṃbhāvanā)
       ("11111"   5 saṃśaya)
       ("111111"  6 aniścaya)
       ("1111111" 7 ajñāta-sīmā)))
    15
    (quote same-width-bit-inversion)
    (quote append-same-bit)
    (quote seven-directed-grades-converge-to-empty-list)
    (quote belongs-to-sens-function-space)
    (quote distinct-functions-same-empty-result)))

(cond
  ((equal? pas-observed pas-expected)
   (structural-relation same)
   (quote (core4-predicate-answer-scale-ok)))
  ((= 1 1) 1
   (list (quote core4-predicate-answer-scale-mismatch)
         pas-expected
         pas-observed)))
