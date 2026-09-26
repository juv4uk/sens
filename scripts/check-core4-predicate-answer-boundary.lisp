; #1391 — executable witness for Core4 logic/SENS boundary.

(def pab-contract
  (car (read-all (read-file "contracts/core4-predicate-answer-boundary.lisp"))))
(def pab-schema (car pab-contract))
(def pab-sections (cdr pab-contract))

(def pab-field
  (lambda (section name)
    (cdr (assoc name section))))

(def pab-meta (car pab-sections))
(def pab-no (second pab-sections))
(def pab-yes (third pab-sections))
(def pab-undirected (fourth pab-sections))
(def pab-function-convergence (fifth pab-sections))
(def pab-laws (nth 5 pab-sections))

(def pab-observed
  (list
    pab-schema
    (pab-field pab-meta (quote answer-count))
    (pab-field pab-meta (quote sens-function-count))
    (pab-field pab-meta (quote spaces))
    (length (pab-field pab-no (quote no-path)))
    (pab-field pab-no (quote converges-to))
    (length (pab-field pab-yes (quote yes-path)))
    (pab-field pab-yes (quote converges-to))
    (pab-field pab-undirected (quote undirected-answer))
    (pab-field pab-function-convergence (quote function-convergence))
    (pab-field pab-function-convergence (quote function-identities))
    (pab-field pab-function-convergence (quote result-value))
    (pab-field pab-laws (quote short-answer-to-sens-function))
    (pab-field pab-laws (quote sens-function-to-answer))
    (pab-field pab-laws (quote eighth-bit-in-grading))))

(def pab-expected
  (list
    (quote core4-predicate-answer-boundary/4)
    15
    256
    (quote orthogonal)
    7
    (quote ())
    7
    (quote ())
    (quote ())
    (quote ((00000000 ()) (11111111 ())))
    (quote distinct)
    (quote one-empty-list)
    (quote forbidden)
    (quote forbidden)
    (quote forbidden)))

(cond
  ((equal? pab-observed pab-expected)
   (1)
   (quote (core4-predicate-answer-boundary-ok)))
  ((= 1 1) 1
   (list (quote core4-predicate-answer-boundary-mismatch)
         pab-expected
         pab-observed)))
