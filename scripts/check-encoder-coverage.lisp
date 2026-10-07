; #604 leaf carrier probe for the first committed coverage row.
(load "lib/core.lisp")
(load "lib/machine/encoding/coverage-generator.lisp")

(def encoder-coverage-committed-form
  (car
    (read-all
      (read-file
        "lib/machine/encoding/coverage.lisp"))))

(def encoder-coverage-first-coverage-row
  (car (cdr (cdr (cdr encoder-coverage-committed-form)))))

(def encoder-coverage-first-row-empty-result
  (encoder-coverage-empty?
    encoder-coverage-first-coverage-row))

(def encoder-coverage-first-row-count-result
  (encoder-coverage-count=?
    #b101
    (length encoder-coverage-first-coverage-row)))

(list
  (quote encoder-coverage-first-row-leaf-probe)
  (list
    (quote empty-result)
    encoder-coverage-first-row-empty-result)
  (list
    (quote empty-is-d1-no)
    (encoder-coverage-same?
      encoder-coverage-first-row-empty-result
      encoder-coverage-d1-no))
  (list
    (quote count-result)
    encoder-coverage-first-row-count-result)
  (list
    (quote count-is-d1-yes)
    (encoder-coverage-same?
      encoder-coverage-first-row-count-result
      encoder-coverage-d1-yes))
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
