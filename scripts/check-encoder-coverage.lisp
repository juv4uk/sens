; #604 temporary first-row leaf carrier probe after ZEROP normalization.
(load "lib/core.lisp")
(load "lib/machine/encoding/coverage-generator.lisp")

(def encoder-coverage-committed-form
  (car
    (read-all
      (read-file
        "lib/machine/encoding/coverage.lisp"))))

(def encoder-coverage-first-coverage-row
  (car (cdr (cdr (cdr encoder-coverage-committed-form)))))

(list
  (quote encoder-coverage-first-row-leaf-probe)
  (list
    (quote empty-result)
    (encoder-coverage-empty?
      encoder-coverage-first-coverage-row))
  (list
    (quote count-result)
    (encoder-coverage-count=?
      #b101
      (length encoder-coverage-first-coverage-row)))
  (list
    (quote tag-match)
    (encoder-coverage-same?
      (car encoder-coverage-first-coverage-row)
      (quote coverage)))
  (list
    (quote iclass-tag-match)
    (encoder-coverage-same?
      (car (second encoder-coverage-first-coverage-row))
      (quote iclass))))
