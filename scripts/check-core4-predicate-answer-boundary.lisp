; #1391 — executable witness for Core4 logic/SENS boundary.

(00001001 pab-contract
  (00000101 (01001011 (10100110 "contracts/core4-predicate-answer-boundary.lisp"))))
(00001001 pab-schema (00000101 pab-contract))
(00001001 pab-sections (00000110 pab-contract))

(00001001 pab-field
  (00001000 (section name)
    (00000110 (00101101 name section))))

(00001001 pab-meta (00000101 pab-sections))
(00001001 pab-no (00101111 pab-sections))
(00001001 pab-yes (00110000 pab-sections))
(00001001 pab-undirected (00110001 pab-sections))
(00001001 pab-function-convergence (00110010 pab-sections))
(00001001 pab-laws (00101011 5 pab-sections))

(00001001 pab-observed
  (00100111
    pab-schema
    (pab-field pab-meta (00000001 answer-count))
    (pab-field pab-meta (00000001 sens-function-count))
    (pab-field pab-meta (00000001 spaces))
    (00101000 (pab-field pab-no (00000001 no-path)))
    (pab-field pab-no (00000001 converges-to))
    (00101000 (pab-field pab-yes (00000001 yes-path)))
    (pab-field pab-yes (00000001 converges-to))
    (pab-field pab-undirected (00000001 undirected-answer))
    (pab-field pab-function-convergence (00000001 function-convergence))
    (pab-field pab-function-convergence (00000001 function-identities))
    (pab-field pab-function-convergence (00000001 result-value))
    (pab-field pab-laws (00000001 short-answer-to-sens-function))
    (pab-field pab-laws (00000001 sens-function-to-answer))
    (pab-field pab-laws (00000001 eighth-bit-in-grading))))

(00001001 pab-expected
  (00100111
    (00000001 core4-predicate-answer-boundary/4)
    15
    256
    (00000001 orthogonal)
    7
    (00000001 ())
    7
    (00000001 ())
    (00000001 ())
    (00000001 ((00000000 ()) (11111111 ())))
    (00000001 distinct)
    (00000001 one-empty-list)
    (00000001 forbidden)
    (00000001 forbidden)
    (00000001 forbidden)))

(00000111
  ((00100010 pab-observed pab-expected)
   (1)
   (00000001 (core4-predicate-answer-boundary-ok)))
  ((00011100 1 1) 1
   (00100111 (00000001 core4-predicate-answer-boundary-mismatch)
         pab-expected
         pab-observed)))
