; #604 temporary carrier probe. No probe result is fed to D3 COND.
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

(def encoder-coverage-first-partial-row
  (car encoder-coverage-partials))

(list
  (quote encoder-coverage-local-carrier-probe)
  (list (quote index-checks) (encoder-coverage-index-checks))
  (list (quote index-valid) (encoder-coverage-index-valid?))
  (list
    (quote first-row-match)
    (encoder-coverage-committed-row-matches?
      encoder-coverage-first-index-row
      encoder-coverage-first-coverage-row
      (quote ())))
  (list
    (quote first-row-match-is-yes)
    (encoder-coverage-same?
      (encoder-coverage-committed-row-matches?
        encoder-coverage-first-index-row
        encoder-coverage-first-coverage-row
        (quote ()))
      encoder-coverage-d1-yes))
  (list
    (quote first-partial-self-key)
    (encoder-coverage-row-key=?
      encoder-coverage-first-partial-row
      encoder-coverage-first-partial-row))
  (list
    (quote first-partial-self-key-is-yes)
    (encoder-coverage-same?
      (encoder-coverage-row-key=?
        encoder-coverage-first-partial-row
        encoder-coverage-first-partial-row)
      encoder-coverage-d1-yes)))
