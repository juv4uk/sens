; #604 temporary carrier probe. No probe result is fed to D3 COND.
(load "lib/core.lisp")
(load "lib/machine/encoding/coverage-generator.lisp")

(def encoder-coverage-committed-form
  (car
    (read-all
      (read-file
        "lib/machine/encoding/coverage.lisp"))))

(list
  (quote encoder-coverage-carrier-probe)
  (list (quote index-checks) (encoder-coverage-index-checks))
  (list (quote index-valid) (encoder-coverage-index-valid?))
  (list
    (quote first-row-match)
    (encoder-coverage-committed-row-matches?
      (car encoder-coverage-index-rows)
      (car (cdr (cdr (cdr encoder-coverage-committed-form))))
      (quote ())))
  (list
    (quote rows-valid)
    (encoder-coverage-projection-rows-valid?
      encoder-coverage-index-rows
      (cdr (cdr (cdr encoder-coverage-committed-form)))
      encoder-coverage-partials))
  (list
    (quote projection-valid)
    (encoder-coverage-projection-valid?
      encoder-coverage-committed-form)))
