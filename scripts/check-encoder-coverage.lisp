; #604 temporary recursive predicate probe. No checker COND.
(load "lib/core.lisp")
(load "lib/machine/encoding/coverage-generator.lisp")

(list
  (quote encoder-coverage-index-unique-probe)
  (encoder-coverage-index-unique?
    encoder-coverage-index-rows
    (quote ())))
