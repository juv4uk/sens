; #604 temporary first-row leaf probe after BinaryNumber isolation.
(load "lib/core.lisp")
(load "lib/machine/encoding/coverage-generator.lisp")

(def encoder-coverage-committed-form
  (car
    (read-all
      (read-file
        "lib/machine/encoding/coverage.lisp"))))

(def encoder-coverage-first-index-row
  (car encoder-coverage-index-rows))

(def encoder-coverage-first-coverage-row
  (car (cdr (cdr (cdr encoder-coverage-committed-form)))))

(list
  (quote encoder-coverage-first-row-leaves)
  (list
    (quote row-count)
    (encoder-coverage-count=? #b101 (length encoder-coverage-first-coverage-row)))
  (list
    (quote row-tag)
    (encoder-coverage-same? (car encoder-coverage-first-coverage-row) (quote coverage)))
  (list
    (quote iclass-tag)
    (encoder-coverage-same? (car (second encoder-coverage-first-coverage-row)) (quote iclass)))
  (list
    (quote iclass-value)
    (encoder-coverage-same? (second (second encoder-coverage-first-coverage-row)) (third encoder-coverage-first-index-row)))
  (list
    (quote extension-tag)
    (encoder-coverage-same? (car (third encoder-coverage-first-coverage-row)) (quote extension)))
  (list
    (quote extension-value)
    (encoder-coverage-same? (second (third encoder-coverage-first-coverage-row)) (second encoder-coverage-first-index-row)))
  (list
    (quote status-tag)
    (encoder-coverage-same? (car (fourth encoder-coverage-first-coverage-row)) (quote status)))
  (list
    (quote status-value)
    (encoder-coverage-same? (second (fourth encoder-coverage-first-coverage-row)) (quote not-yet-implemented)))
  (list
    (quote reason-tag)
    (encoder-coverage-same? (car (fifth encoder-coverage-first-coverage-row)) (quote reason)))
  (list
    (quote reason-value)
    (encoder-coverage-same?
      (second (fifth encoder-coverage-first-coverage-row))
      "remaining BASE forms pending family-by-family rollout")))
