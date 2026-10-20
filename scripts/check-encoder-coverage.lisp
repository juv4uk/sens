; #604 — structural check for the Lisp-owned encoder coverage authority.
; Validates generated inputs, legacy-subset migration witness, and committed
; coverage row-by-row without rendering the full output string.
; Cardinality checks are BinaryNumber-native end-to-end; this checker must
; never reintroduce implicit ordinary-Number <-> BinaryNumber coercion.

(load "lib/core.lisp")
(load "lib/machine/encoding/coverage-generator.lisp")

(визначити форма-покриття-кодувальника
  (перше
    (читати-всі
      (читати-файл
        "lib/machine/encoding/coverage.lisp"))))

(за-умовою
  ((покриття-кодувальника-індекс-коректний?)
   (за-умовою
     ((покриття-кодувальника-проєкція-коректна?
        форма-покриття-кодувальника)
      (як-є
        (encoder-coverage-check
          (status pass))))
     (так
      (перше (читати-всі "(encoder-coverage-check (status fail) (reason projection-mismatch))")))))
  (так
   (список
     (як-є encoder-coverage-check)
     (як-є (status fail))
     (перше (читати-всі "(reason invalid-coverage-input-projection)"))
     (сполучити (як-є checks) (покриття-кодувальника-перевірки-індексу)))))
