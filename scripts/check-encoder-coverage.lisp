; #604 — structural check for the Lisp-owned encoder coverage authority.
; Validates generated inputs, legacy-subset migration witness, and committed
; coverage row-by-row without rendering the full output string.

(load "lib/core.lisp")
(load "lib/machine/encoding/coverage-generator.lisp")

(def encoder-coverage-committed-form
  (car
    (read-all
      (read-file
        "lib/machine/encoding/coverage.lisp"))))

(def encoder-coverage-first-row-result
  (encoder-coverage-committed-row-matches?
    (car encoder-coverage-index-rows)
    (car (cdr (cdr (cdr encoder-coverage-committed-form))))
    (quote ())))

(def encoder-coverage-coverage-rows
  (cdr (cdr (cdr encoder-coverage-committed-form))))

(def encoder-coverage-probe-index-empty
  (encoder-coverage-empty? encoder-coverage-index-rows))

(def encoder-coverage-probe-coverage-empty
  (encoder-coverage-empty? encoder-coverage-coverage-rows))

(def encoder-coverage-probe-partials-empty
  (encoder-coverage-empty? encoder-coverage-partials))

(def encoder-coverage-probe-first-row-key
  (encoder-coverage-row-key=?
    (car encoder-coverage-index-rows)
    (car encoder-coverage-partials)))

(list
  (quote encoder-coverage-probe)
  (list (quote index-empty) encoder-coverage-probe-index-empty)
  (list
    (quote index-empty-is-d1-no)
    (encoder-coverage-same?
      encoder-coverage-probe-index-empty
      encoder-coverage-d1-no))
  (list (quote coverage-empty) encoder-coverage-probe-coverage-empty)
  (list
    (quote coverage-empty-is-d1-no)
    (encoder-coverage-same?
      encoder-coverage-probe-coverage-empty
      encoder-coverage-d1-no))
  (list (quote partials-empty) encoder-coverage-probe-partials-empty)
  (list
    (quote partials-empty-is-d1-no)
    (encoder-coverage-same?
      encoder-coverage-probe-partials-empty
      encoder-coverage-d1-no))
  (list (quote first-row-key) encoder-coverage-probe-first-row-key)
  (list
    (quote first-row-key-is-d1-no)
    (encoder-coverage-same?
      encoder-coverage-probe-first-row-key
      encoder-coverage-d1-no))
  (list (quote first-row-result) encoder-coverage-first-row-result)
  (list
    (quote first-row-is-d1-no)
    (encoder-coverage-same?
      encoder-coverage-first-row-result
      encoder-coverage-d1-no)))
