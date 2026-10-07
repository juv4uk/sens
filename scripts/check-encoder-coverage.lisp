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

(cond
  (encoder-coverage-index-valid?
   (cond
     ((encoder-coverage-projection-valid?
        encoder-coverage-committed-form)
      (quote
        (encoder-coverage-check
          (status pass))))
     (encoder-coverage-d1-yes
      (quote
        (encoder-coverage-check
          (status fail)
          (reason projection-mismatch))))))
  (encoder-coverage-d1-yes
   (list
     (quote encoder-coverage-check)
     (quote (status fail))
     (quote (reason invalid-coverage-input-projection))
     (cons (quote checks) encoder-coverage-index-checks))))
