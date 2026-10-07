; #604 temporary exact-result probe. No coverage recursion and no D3 COND.
(load "lib/core.lisp")
(load "lib/machine/encoding/coverage-generator.lisp")

(list
  (quote encoder-coverage-d1-probe)
  (list (quote yes) encoder-coverage-d1-yes)
  (list (quote no) encoder-coverage-d1-no)
  (list (quote same-symbol) (encoder-coverage-same? (quote x) (quote x)))
  (list (quote distinct-symbol) (encoder-coverage-same? (quote x) (quote y)))
  (list (quote empty-empty) (encoder-coverage-empty? (quote ())))
  (list (quote nonempty-empty) (encoder-coverage-empty? (quote (x)))))
