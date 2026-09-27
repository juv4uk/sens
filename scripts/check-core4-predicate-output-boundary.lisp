; #1391 — executable guard for Core4 final predicate outputs.

(00001001 pob-contract
  (00000101 (01001011 (10100110 "contracts/core4-predicate-output-boundary.lisp"))))
(00001001 pob-schema (00000101 pob-contract))
(00001001 pob-sections (00000110 pob-contract))

(00001001 pob-field
  (00001000 (section name)
    (00000110 (00101101 name section))))

(00001001 pob-meta (00000101 pob-sections))
(00001001 pob-raw (00101111 pob-sections))
(00001001 pob-final (00110000 pob-sections))
(00001001 pob-logic (00110001 pob-sections))
(00001001 pob-functions (00110010 pob-sections))

(00001001 pob-observed
  (00100111
    pob-schema
    (pob-field pob-meta (00000001 function-sens-space))
    (pob-field pob-final (00000001 predicate-question-final-domain))
    (pob-field pob-final (00000001 sens-function-as-final-answer))
    (pob-field pob-logic (00000001 center-count))
    (pob-field pob-logic (00000001 center-direction))
    (pob-field pob-functions (00000001 function-convergence))
    (pob-field pob-functions (00000001 function-identities))
    (pob-field pob-functions (00000001 shared-result))
    (pob-field pob-functions (00000001 shared-result-count))))

(00001001 pob-expected
  (00100111
    (00000001 core4-predicate-output-boundary/3)
    (00000001 exactly-256)
    (00000001 predicate-answer-domain)
    (00000001 forbidden)
    1
    (00000001 none)
    (00000001 ((00000000 ()) (11111111 ())))
    (00000001 distinct)
    (00000001 ())
    1))

(00000111
  ((00100010 pob-observed pob-expected)
   (1)
   (00000001 (core4-predicate-output-boundary-ok)))
  ((00011100 1 1) 1
   (00100111 (00000001 core4-predicate-output-boundary-mismatch)
         pob-expected
         pob-observed)))
