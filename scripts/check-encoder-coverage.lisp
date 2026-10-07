; #604 temporary exact-D3 equality type probe. No result feeds an outer COND.
(load "lib/core.lisp")
(load "lib/machine/encoding/coverage-generator.lisp")

(list
  (quote encoder-coverage-type-probe)
  (list (quote d1-yes) encoder-coverage-d1-yes)
  (list (quote d1-no) encoder-coverage-d1-no)
  (list
    (quote same-symbol)
    (encoder-coverage-same? (quote coverage) (quote coverage)))
  (list
    (quote different-symbol)
    (encoder-coverage-same? (quote coverage) (quote iclass)))
  (list
    (quote same-string)
    (encoder-coverage-same? "coverage" "coverage"))
  (list
    (quote different-string)
    (encoder-coverage-same? "coverage" "iclass"))
  (list
    (quote same-binary)
    (encoder-coverage-same? #b101 #b101))
  (list
    (quote different-binary)
    (encoder-coverage-same? #b101 #b100))
  (list
    (quote same-list)
    (encoder-coverage-same? (quote (coverage iclass)) (quote (coverage iclass))))
  (list
    (quote different-list)
    (encoder-coverage-same? (quote (coverage iclass)) (quote (coverage status))))
  (list
    (quote empty-nonempty)
    (encoder-coverage-empty? (quote (coverage))))
  (list
    (quote empty-empty)
    (encoder-coverage-empty? (quote ())))
  (list
    (quote count-five)
    (encoder-coverage-count=? #b101 5)))
