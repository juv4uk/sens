; #487 — structural parity check for the Lisp-owned coverage policy.
; CI validates the committed projection row-by-row without rendering the
; entire ~184 KB output string. Full rendering remains available only through
; scripts/generate-encoder-coverage.lisp.

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
       (reason invalid-admitted-iclass-index)))))
