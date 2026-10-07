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

(def encoder-coverage-projection-result
  (encoder-coverage-projection-valid?
    encoder-coverage-committed-form))

(def encoder-coverage-first-row-result
  (encoder-coverage-committed-row-matches?
    (car encoder-coverage-index-rows)
    (car (cdr (cdr (cdr encoder-coverage-committed-form))))
    (quote ())))

(def encoder-coverage-rows-result
  (encoder-coverage-projection-rows-valid?
    encoder-coverage-index-rows
    (cdr (cdr (cdr encoder-coverage-committed-form)))
    encoder-coverage-partials))

(cond
  ((encoder-coverage-same?
     encoder-coverage-index-valid?
     encoder-coverage-d1-yes)
   (cond
     ((encoder-coverage-same?
        encoder-coverage-projection-result
        encoder-coverage-d1-yes)
      (quote
        (encoder-coverage-check
          (status pass))))
     (encoder-coverage-d1-yes
      (list
        (quote encoder-coverage-check)
        (quote (status fail))
        (quote (reason projection-mismatch))
        (list (quote projection-result) encoder-coverage-projection-result)
        (list
          (quote projection-is-d1-no)
          (encoder-coverage-same?
            encoder-coverage-projection-result
            encoder-coverage-d1-no))
        (list (quote rows-result) encoder-coverage-rows-result)
        (list
          (quote rows-is-d1-no)
          (encoder-coverage-same?
            encoder-coverage-rows-result
            encoder-coverage-d1-no))
        (list (quote first-row-result) encoder-coverage-first-row-result)
        (list
          (quote first-row-is-d1-no)
          (encoder-coverage-same?
            encoder-coverage-first-row-result
            encoder-coverage-d1-no))))))
  (encoder-coverage-d1-yes
   (list
     (quote encoder-coverage-check)
     (quote (status fail))
     (quote (reason invalid-coverage-input-projection))
     (cons (quote checks) encoder-coverage-index-checks))))
