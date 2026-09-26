; #1391 — executable guard for Core4 final predicate outputs.

(def pob-contract
  (car (read-all (read-file "contracts/core4-predicate-output-boundary.lisp"))))
(def pob-schema (car pob-contract))
(def pob-sections (cdr pob-contract))

(def pob-field
  (lambda (section name)
    (cdr (assoc name section))))

(def pob-meta (car pob-sections))
(def pob-raw (second pob-sections))
(def pob-final (third pob-sections))
(def pob-logic (fourth pob-sections))
(def pob-functions (fifth pob-sections))

(def pob-observed
  (list
    pob-schema
    (pob-field pob-meta (quote function-sens-space))
    (pob-field pob-final (quote predicate-question-final-domain))
    (pob-field pob-final (quote sens-function-as-final-answer))
    (pob-field pob-logic (quote center-count))
    (pob-field pob-logic (quote center-direction))
    (pob-field pob-functions (quote function-convergence))
    (pob-field pob-functions (quote function-identities))
    (pob-field pob-functions (quote shared-result))
    (pob-field pob-functions (quote shared-result-count))))

(def pob-expected
  (list
    (quote core4-predicate-output-boundary/3)
    (quote exactly-256)
    (quote predicate-answer-domain)
    (quote forbidden)
    1
    (quote none)
    (quote ((00000000 ()) (11111111 ())))
    (quote distinct)
    (quote ())
    1))

(cond
  ((equal? pob-observed pob-expected)
   (1)
   (quote (core4-predicate-output-boundary-ok)))
  ((= 1 1) 1
   (list (quote core4-predicate-output-boundary-mismatch)
         pob-expected
         pob-observed)))
