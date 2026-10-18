; #604 — structural check for the Lisp-owned encoder coverage authority.
; Validates generated inputs, legacy-subset migration witness, and committed
; coverage row-by-row without rendering the full output string.
; Cardinality checks are BinaryNumber-native end-to-end; this checker must
; never reintroduce implicit ordinary-Number <-> BinaryNumber coercion.

(load "lib/core.lisp")
(load "lib/machine/encoding/coverage-generator.lisp")

(визначити encoder-coverage-committed-form
  (перше
    (читати-всі
      (читати-файл
        "lib/machine/encoding/coverage.lisp"))))

(за-умовою
  ((encoder-coverage-index-valid?)
   (за-умовою
     ((encoder-coverage-projection-valid?
        encoder-coverage-committed-form)
      (як-є
        (encoder-coverage-check
          (status pass))))
     (encoder-coverage-d1-yes
      (перше (читати-всі "(encoder-coverage-check (status fail) (reason projection-mismatch))")))))
  (encoder-coverage-d1-yes
   (список
     (як-є encoder-coverage-check)
     (як-є (status fail))
     (перше (читати-всі "(reason invalid-coverage-input-projection)"))
     (сполучити (як-є checks) (encoder-coverage-index-checks)))))
