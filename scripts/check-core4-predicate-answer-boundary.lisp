; #1391 — executable witness for Core4 logic/SENS boundary.

(визначити pab-contract
  (перше (читати-всі (читати-файл "contracts/core4-predicate-answer-boundary.lisp"))))
(визначити pab-schema (перше pab-contract))
(визначити pab-sections (решта pab-contract))

(визначити pab-field
  (функція (section name)
    (решта (знайти-за-ключем name section))))

(визначити pab-meta (перше pab-sections))
(визначити pab-no (друге pab-sections))
(визначити pab-yes (третє pab-sections))
(визначити pab-undirected (четверте pab-sections))
(визначити pab-function-convergence (п'ятий pab-sections))
(визначити pab-laws (елемент-списку-за-індексом 5 pab-sections))

(визначити pab-observed
  (список
    pab-schema
    (pab-field pab-meta (як-є answer-count))
    (pab-field pab-meta (як-є sens-function-count))
    (pab-field pab-meta (як-є spaces))
    (довжина (pab-field pab-no (як-є no-path)))
    (pab-field pab-no (як-є converges-to))
    (довжина (pab-field pab-yes (як-є yes-path)))
    (pab-field pab-yes (як-є converges-to))
    (pab-field pab-undirected (як-є undirected-answer))
    (pab-field pab-function-convergence (як-є function-convergence))
    (pab-field pab-function-convergence (як-є function-identities))
    (pab-field pab-function-convergence (як-є result-value))
    (pab-field pab-laws (як-є short-answer-to-sens-function))
    (pab-field pab-laws (як-є sens-function-to-answer))
    (pab-field pab-laws (як-є eighth-bit-in-grading))))

(визначити pab-expected
  (список
    (як-є core4-predicate-answer-boundary/4)
    15
    256
    (як-є orthogonal)
    7
    (як-є ())
    7
    (як-є ())
    (як-є ())
    (001 ((00000000 ()) (11111111 ())))
    (як-є distinct)
    (як-є one-empty-list)
    (як-є forbidden)
    (як-є forbidden)
    (як-є forbidden)))

(за-умовою
  ((однакові? pab-observed pab-expected)
   (як-є (core4-predicate-answer-boundary-ok)))
  ((атом? (як-є ()))
   (список (як-є core4-predicate-answer-boundary-mismatch)
         pab-expected
         pab-observed)))
