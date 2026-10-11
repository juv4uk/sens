; #1391 — executable witness for Core4 logic/SENS boundary.

(0011 pab-contract
  (100 (110101001 (110110111 "contracts/core4-predicate-answer-boundary.lisp"))))
(0011 pab-schema (100 pab-contract))
(0011 pab-sections (011 pab-contract))

(0011 pab-field
  (0010 (section name)
    (011 (11100 name section))))

(0011 pab-meta (100 pab-sections))
(0011 pab-no (1001 pab-sections))
(0011 pab-yes (10011 pab-sections))
(0011 pab-undirected (100111 pab-sections))
(0011 pab-function-convergence (110110101 pab-sections))
(0011 pab-laws (000100 5 pab-sections))

(0011 pab-observed
  (1110
    pab-schema
    (pab-field pab-meta (001 answer-count))
    (pab-field pab-meta (001 sens-function-count))
    (pab-field pab-meta (001 spaces))
    (000000 (pab-field pab-no (001 no-path)))
    (pab-field pab-no (001 converges-to))
    (000000 (pab-field pab-yes (001 yes-path)))
    (pab-field pab-yes (001 converges-to))
    (pab-field pab-undirected (001 undirected-answer))
    (pab-field pab-function-convergence (001 function-convergence))
    (pab-field pab-function-convergence (001 function-identities))
    (pab-field pab-function-convergence (001 result-value))
    (pab-field pab-laws (001 short-answer-to-sens-function))
    (pab-field pab-laws (001 sens-function-to-answer))
    (pab-field pab-laws (001 eighth-bit-in-grading))))

(0011 pab-expected
  (1110
    (001 core4-predicate-answer-boundary/4)
    15
    256
    (001 orthogonal)
    7
    (001 ())
    7
    (001 ())
    (001 ())
    (001 ((00000000 ()) (11111111 ())))
    (001 distinct)
    (001 one-empty-list)
    (001 forbidden)
    (001 forbidden)
    (001 forbidden)))

(110
  ((11110111 pab-observed pab-expected)
   (001 (core4-predicate-answer-boundary-ok)))
  ((010 (001 ()))
   (1110 (001 core4-predicate-answer-boundary-mismatch)
         pab-expected
         pab-observed)))
