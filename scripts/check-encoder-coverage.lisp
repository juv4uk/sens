; #604 — structural check for the Lisp-owned encoder coverage authority.
; Validates generated inputs, legacy-subset migration witness, and committed
; coverage row-by-row without rendering the full output string.
; Cardinality checks are BinaryNumber-native end-to-end; this checker must
; never reintroduce implicit ordinary-Number <-> BinaryNumber coercion.

(load "lib/core.lisp")
(load "lib/machine/encoding/coverage-generator.lisp")

(0011 encoder-coverage-committed-form
  (100
    (110101001
      (110110111
        "lib/machine/encoding/coverage.lisp"))))

(110
  ((encoder-coverage-index-valid?)
   (110
     ((encoder-coverage-projection-valid?
        encoder-coverage-committed-form)
      (001
        (encoder-coverage-check
          (status pass))))
     (encoder-coverage-d1-yes
      (100 (110101001 "(encoder-coverage-check (status fail) (reason projection-mismatch))")))))
  (encoder-coverage-d1-yes
   (1110
     (001 encoder-coverage-check)
     (001 (status fail))
     (100 (110101001 "(reason invalid-coverage-input-projection)"))
     (111 (001 checks) (encoder-coverage-index-checks)))))
