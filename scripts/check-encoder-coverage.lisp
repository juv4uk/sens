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
  ((encoder-coverage-same? encoder-coverage-index-valid? t)
   (cond
     ((encoder-coverage-projection-valid?
        encoder-coverage-committed-form)
      (quote
        (encoder-coverage-check
          (status pass))))
     (t
      (quote
        (encoder-coverage-check
          (status fail)
          (reason projection-mismatch))))))
  (t
   (quote
     (encoder-coverage-check
       (status fail)
       (reason invalid-coverage-input-projection)))))
