; #604 — regenerate encoder coverage from Lisp-owned derived machine coverage inputs.
(load "lib/core.lisp")
(load "lib/machine/encoding/coverage-generator.lisp")

(за-умовою
  ((покриття-кодувальника-індекс-коректний?)
   ((функція ()
      (записати-файл
        "lib/machine/encoding/coverage.lisp"
        (покриття-кодувальника-сформувати-звіт))
      (друкувати
        (список
          (як-є encoder-coverage-generate)
          (як-є (status written))
          (список (як-є forms) покриття-кодувальника-кількість-форм)
          (список (як-є partial) (довжина покриття-кодувальника-часткові-записи)))))))
  (так
   (друкувати
     (перше (читати-всі "(encoder-coverage-generate (status rejected) (reason invalid-coverage-input-projection))")))))
